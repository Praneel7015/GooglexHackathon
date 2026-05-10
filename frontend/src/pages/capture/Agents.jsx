import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame } from '../../components/ui';
import StepHeader from '../../components/StepHeader';
import AgentPipeline from '../../components/AgentPipeline';
import { runPipeline, AGENT_STAGES } from '../../lib/agents';
import { useApp } from '../../lib/store';
import { findNearby } from '../../lib/seed';
import { api } from '../../lib/api';
import { useT } from '../../lib/i18n';

// Labels shown while waiting on the Drafting + Submission stage (slow due to LLM calls)
const WAITING_HINTS = [
  'Drafting formal complaint letter…',
  'Translating to Kannada…',
  'Composing tweet…',
  'Generating RTI template…',
  'Dispatching to agencies…',
];

// Module-level flag so React StrictMode's double-mount doesn't fire the
// pipeline twice. A ref would reset between mounts; a module variable persists.
let _pipelineStarted = false;

export default function Agents() {
  const T = useT();
  const [activeIndex, setActiveIndex] = useState(0);
  const [outputs, setOutputs] = useState({});
  const [elapsedSec, setElapsedSec] = useState(0);
  const [waitingHint, setWaitingHint] = useState('');
  const navigate = useNavigate();
  const cur = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);

  const curRef = useRef(cur);
  const patchRef = useRef(patch);
  const navigateRef = useRef(navigate);

  // Reset the module-level guard when the component unmounts for real
  // (i.e. the user navigates away or submits again later).
  useEffect(() => {
    return () => { _pipelineStarted = false; };
  }, []);

  // Elapsed timer — shown while the backend is processing
  useEffect(() => {
    const start = Date.now();
    const t = setInterval(() => setElapsedSec(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(t);
  }, []);

  // Cycle through waiting hints while drafting/submitting (slow LLM stages)
  useEffect(() => {
    let i = 0;
    const t = setInterval(() => {
      i = (i + 1) % WAITING_HINTS.length;
      setWaitingHint(WAITING_HINTS[i]);
    }, 3000);
    setWaitingHint(WAITING_HINTS[0]);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    // Guard: module-level variable persists across StrictMode double-mount.
    // Reset when navigating away so submitting again on a fresh page works.
    if (_pipelineStarted) return;
    _pipelineStarted = true;

    const snapshot = curRef.current;
    // `cancelled` only prevents duplicate API calls — it never blocks navigation.
    let cancelled = false;

    // Convert dataURL photo to a File for the backend
    async function dataURLtoFile(dataUrl) {
      if (!dataUrl) return null;
      const res = await fetch(dataUrl);
      const blob = await res.blob();
      return new File([blob], 'complaint.jpg', { type: 'image/jpeg' });
    }

    async function runReal() {
      const photoFile = await dataURLtoFile(snapshot.photo);
      if (!photoFile) {
        runMock();
        return;
      }

      // Start the animation in parallel so UI feels responsive.
      // Advances through stages until the last one, then pulses "working" hints.
      const animStages = [...AGENT_STAGES];
      let animIdx = 0;
      const animTimer = setInterval(() => {
        if (cancelled) { clearInterval(animTimer); return; }
        if (animIdx < animStages.length - 1) {
          const stage = animStages[animIdx];
          setActiveIndex(animIdx + 1);
          setOutputs(o => ({ ...o, [stage.key]: '...' }));
          animIdx++;
        }
        // Once at the last stage, the timer keeps running so the pulse animation
        // stays active — just don't advance past the end.
      }, 2500);

      // Get user info and channel preferences from store
      const state = useApp.getState();
      const userName = state.user?.name || undefined;
      const userEmail = state.channels?.email?.connected ? state.channels.email.value : undefined;
      const skipTwitter = !state.channels?.twitter?.connected;
      const skipEmail = !state.channels?.email?.connected;

      // Real backend call
      const result = await api.submitReport({
        photo: photoFile,
        fallback_lat: snapshot.gps?.[0],
        fallback_lng: snapshot.gps?.[1],
        user_name: userName,
        user_email: userEmail,
        voice_note: snapshot.voiceBlob || undefined,
        skip_twitter: skipTwitter ? '1' : undefined,
        skip_email: skipEmail ? '1' : undefined,
      });

      clearInterval(animTimer);

      // NOTE: Do NOT check `cancelled` here — we always want to update the UI
      // and navigate after the backend responds, even if StrictMode unmounted
      // and remounted the component. The module-level guard ensures only one
      // API call fires, so we always act on its result.

      if (result) {
        const r = result.reporter || {};
        const g = result.geo || {};
        const rt = result.routing || {};
        const cv = result.crowd_validation || {};
        const dr = result.drafting || {};
        const sub = result.submission || {};

        setOutputs({
          reporter: `${r.issue_type || 'classified'} · severity ${r.severity || '?'}`,
          geo: `Ward ${g.ward_number || '?'} · ${g.ward_name || g.address || ''}`.slice(0, 60),
          routing: `${rt.primary_agency?.name || 'BBMP'} · ${rt.twitter_handle || ''}`,
          crowd: cv.is_bundled
            ? `Bundling ${cv.member_count} nearby reports · joint complaint`
            : `Standalone complaint · ${(cv.nearest_complaints || []).length} nearby`,
          drafting: dr.email_subject ? 'Email + complaint letter drafted' : 'Drafts generated',
          submit: (() => {
            const chs = sub.submitted_channels || [];
            const emailOk = chs.find(c => c.channel === 'email')?.status === 'success';
            const tweetOk = chs.find(c => c.channel === 'twitter')?.status === 'success';
            if (sub.status === 'suppressed') return `Bundled (${sub.cluster_size_at_send} residents)`;
            const parts = [];
            if (emailOk) parts.push('Email ✓');
            if (tweetOk) parts.push('Tweet ✓');
            return parts.length ? `Dispatched · ${parts.join(' · ')}` : 'Dispatched';
          })(),
        });
        setActiveIndex(AGENT_STAGES.length);

        patchRef.current({
          issue: r.issue_type || snapshot.issue,
          severity: r.severity || snapshot.severity,
          ward: g.ward_number || snapshot.ward,
          wardName: g.ward_name || '',
          agencyCode: rt.primary_agency?.name || 'BBMP',
          bundleSize: cv.member_count || 0,
          nearby: cv.nearest_complaints || [],
          backendResult: result,
        });
      } else {
        // Backend failed — save locally
        console.warn('[Agents] Backend unavailable, complaint saved locally only');
        setOutputs({
          reporter: 'Offline — saved locally',
          geo: 'Will process when online',
          routing: '—',
          crowd: '—',
          drafting: '—',
          submit: 'Queued for retry',
        });
        setActiveIndex(AGENT_STAGES.length);
        patchRef.current({ backendResult: null });
      }

      setTimeout(() => navigateRef.current('/confirm'), 1200);
    }

    function runMock() {
      const cancel = runPipeline(snapshot, {
        onStage: (i, stage, output) => {
          setActiveIndex(i + 1);
          setOutputs(o => ({ ...o, [stage.key]: output }));
          if (stage.key === 'crowd') {
            const nearby = findNearby({ ll: snapshot.gps || [13.0995, 77.5963], issue: snapshot.issue, id: 'NEW' });
            patchRef.current({ nearby, bundleSize: nearby.length });
          }
        },
        onDone: () => setTimeout(() => navigateRef.current('/confirm'), 600),
        perStageMs: 900,
      });
      return cancel;
    }

    runReal();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <StepHeader kicker={T('agents.step')} title={T('agents.heading')} />
        <div className="mt-4 flex-1">
          <AgentPipeline activeIndex={activeIndex} outputs={outputs} />
        </div>
        <div className="text-right font-hand text-olive text-[13px] -rotate-2 -mt-2">{T('ag.live')}</div>
        {activeIndex >= AGENT_STAGES.length ? (
          <div className="font-mono text-center text-[10px] text-coffee/55 mt-1">
            {T('ag.done')}
          </div>
        ) : (
          <div className="mt-1 space-y-0.5">
            <div className="font-mono text-center text-[10px] text-coffee/55 animate-pulse">
              {waitingHint}
            </div>
            <div className="font-mono text-center text-[9px] text-coffee/40">
              {T('ag.progress', { done: activeIndex, total: AGENT_STAGES.length })}
              {elapsedSec > 5 ? ` · ${elapsedSec}s` : ''}
            </div>
          </div>
        )}
      </div>
    </PhoneFrame>
  );
}

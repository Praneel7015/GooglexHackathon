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

export default function Agents() {
  const T = useT();
  const [activeIndex, setActiveIndex] = useState(0);
  const [outputs, setOutputs] = useState({});
  const navigate = useNavigate();
  const cur = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);

  const curRef = useRef(cur);
  const patchRef = useRef(patch);
  const navigateRef = useRef(navigate);

  useEffect(() => {
    const snapshot = curRef.current;
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
        // Fallback to mock pipeline if no photo
        runMock();
        return;
      }

      // Start the mock animation in parallel so UI feels responsive
      const animStages = [...AGENT_STAGES];
      let animIdx = 0;
      const animTimer = setInterval(() => {
        if (cancelled || animIdx >= animStages.length) {
          clearInterval(animTimer);
          return;
        }
        const stage = animStages[animIdx];
        setActiveIndex(animIdx + 1);
        setOutputs(o => ({ ...o, [stage.key]: '...' }));
        animIdx++;
      }, 1800);

      // Real backend call
      const result = await api.submitReport({
        photo: photoFile,
        fallback_lat: snapshot.gps?.[0],
        fallback_lng: snapshot.gps?.[1],
        user_name: undefined,
        user_email: undefined,
        voice_note: snapshot.voiceBlob || undefined,
      });

      clearInterval(animTimer);

      if (cancelled) return;

      if (result) {
        // Drive UI with real data
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
          drafting: dr.tweet_text ? 'Tweet · email · RTI drafted' : 'Drafts generated',
          submit: sub.status === 'sent' ? 'Dispatched · Twitter ✓ · Email ✓' :
                  sub.status === 'suppressed' ? `Suppressed · bundled (${sub.cluster_size_at_send})` :
                  'Dispatched · stub mode',
        });
        setActiveIndex(AGENT_STAGES.length);

        // Update store with real data
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

        setTimeout(() => {
          if (!cancelled) navigateRef.current('/confirm');
        }, 1200);
      } else {
        // Backend failed — fall back to mock
        console.warn('[Agents] Backend unavailable, falling back to mock pipeline');
        runMock();
      }
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
        <div className="font-mono text-center text-[10px] text-coffee/55 mt-1">
          {activeIndex >= AGENT_STAGES.length ? T('ag.done') : T('ag.progress', { done: activeIndex, total: AGENT_STAGES.length })}
        </div>
      </div>
    </PhoneFrame>
  );
}

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame, Card, Button } from '../../components/ui';
import { useApp } from '../../lib/store';
import { useT } from '../../lib/i18n';

export default function Confirm() {
  const T = useT();
  const cur = useApp(s => s.current);
  const patchChannel = useApp(s => s.patchChannel);
  const fileCurrent = useApp(s => s.fileCurrent);
  const navigate = useNavigate();
  const bundleN = cur.bundleSize || 0;

  // Drive channel status from real backend response (set in Agents.jsx)
  const backendSub = cur.backendResult?.submission;
  const backendChannels = backendSub?.submitted_channels || [];

  useEffect(() => {
    if (backendChannels.length > 0) {
      // Real backend data — show channels as they were dispatched
      let i = 0;
      const timer = setInterval(() => {
        if (i >= backendChannels.length) { clearInterval(timer); return; }
        const ch = backendChannels[i];
        const key = ch.channel === 'email' ? 'email' :
                    ch.channel === 'twitter' ? 'twitter' :
                    ch.channel === 'whatsapp' ? 'whatsapp' : 'portal';
        patchChannel(key, ch.status === 'success');
        i++;
      }, 500);
      return () => clearInterval(timer);
    } else {
      // Fallback: mark all as done after 2s (mock mode)
      const t = setTimeout(() => {
        ['twitter', 'email', 'portal', 'whatsapp'].forEach(k => patchChannel(k, true));
      }, 2000);
      return () => clearTimeout(t);
    }
  }, [backendChannels, patchChannel]);

  // Derive channel display from backend data
  const twitterHandle = cur.backendResult?.routing?.twitter_handle || '@BBMPCOMM';
  const officerEmail = cur.backendResult?.routing?.ward_officer?.email || 'ward officer';
  const subStatus = backendSub?.status;

  const CHANNELS = [
    { key: 'twitter',  label: 'Twitter',     hint: twitterHandle,
      mode: backendChannels.find(c => c.channel === 'twitter')?.mode },
    { key: 'email',    label: 'Email',       hint: officerEmail,
      mode: backendChannels.find(c => c.channel === 'email')?.mode },
    { key: 'portal',   label: 'BBMP portal', hint: 'pre-filled',
      mode: 'stub' },
    { key: 'whatsapp', label: 'WhatsApp',    hint: 'councillor',
      mode: backendChannels.find(c => c.channel === 'whatsapp')?.mode },
  ];

  const goTrack = () => {
    const filed = fileCurrent();
    const trackId = cur.backendResult?.complaint_id || filed.id;
    navigate(`/track/${trackId}`);
  };

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <div className="text-center mt-1">
          <div className="w-12 h-12 rounded-full bg-olive border-[1.5px] border-line mx-auto mb-2.5 flex items-center justify-center text-mist text-2xl animate-pop-in">✓</div>
          <h1 className="font-hand text-coffee text-[24px] leading-tight whitespace-pre-line">{T('conf.filed', { n: bundleN })}</h1>
          {subStatus === 'suppressed' && (
            <div className="font-sans text-[10px] text-coffee/65 mt-1">Joined existing cluster · next notification at milestone</div>
          )}
        </div>

        <Card padding="p-0" tone="mist" className="mt-3 h-24 overflow-hidden relative">
          <svg viewBox="0 0 220 96" width="100%" height="100%" className="block">
            <path d="M10 80 Q 30 30, 70 25 Q 130 15, 180 35 Q 210 55, 200 85 Q 100 92, 10 80 z"
              fill="none" stroke="#71816d" strokeWidth="1.4" strokeDasharray="3 3" />
            {Array.from({ length: Math.max(1, bundleN) }).map((_, i) => {
              const x = 30 + (i * 7) % 160 + (i % 3) * 4;
              const y = 35 + (i * 13) % 50;
              return <circle key={i} cx={x} cy={y} r="2.4" fill="#71816d" stroke="#342a21" strokeWidth=".7" />;
            })}
            <circle cx="115" cy="55" r="14" fill="#71816d" stroke="#342a21" strokeWidth="1.4" />
            <text x="115" y="59" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="11" fill="#fbf8f1" fontWeight="600">{bundleN + 1}</text>
          </svg>
        </Card>

        <div className="font-sans text-[9px] uppercase tracking-wider text-coffee/65 mt-3 mb-1.5">{T('conf.channels')}</div>
        <div className="space-y-1.5">
          {CHANNELS.map(c => {
            const sent = !!cur.channels[c.key];
            const modeLabel = c.mode === 'stub' ? ' (stub)' : '';
            return (
              <Card key={c.key} padding="px-2.5 py-1.5" className="flex items-center gap-2">
                <span className={'w-2 h-2 rounded-full ' + (sent ? 'bg-olive' : 'bg-beige animate-pulse-soft')} />
                <span className="font-sans text-[11px] font-semibold text-coffee">{c.label}{modeLabel}</span>
                <span className="font-mono text-[10px] text-coffee/65">{c.hint}</span>
                <span className={'ml-auto font-sans text-[11px] font-semibold ' + (sent ? 'text-olive' : 'text-coffee/55')}>{sent ? '✓' : '…'}</span>
              </Card>
            );
          })}
        </div>

        <Button variant="primary" onClick={goTrack} full size="md" className="mt-auto">{T('conf.track')}</Button>
      </div>
    </PhoneFrame>
  );
}

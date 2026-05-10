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

  const hasBackend = !!cur.backendResult;
  const bundleN = cur.bundleSize || 0;
  const total = bundleN + 1;

  // Backend data
  const backendSub = cur.backendResult?.submission;
  const backendChannels = backendSub?.submitted_channels || [];
  const subStatus = backendSub?.status;
  const isBundled = cur.backendResult?.crowd_validation?.is_bundled || false;
  const issueType = (cur.issue || cur.backendResult?.reporter?.issue_type || 'civic issue').replace(/_/g, ' ');
  const wardName = cur.wardName || cur.backendResult?.geo?.ward_name || '';
  const agencyName = cur.agencyCode || cur.backendResult?.routing?.primary_agency?.name || 'BBMP';

  // Channel statuses from backend
  const emailChannel = backendChannels.find(c => c.channel === 'email');
  const twitterChannel = backendChannels.find(c => c.channel === 'twitter');
  const emailSent = emailChannel?.status === 'success';
  const emailSkipped = emailChannel?.status === 'skipped';
  const twitterSent = twitterChannel?.status === 'success';
  const twitterFailed = twitterChannel?.status === 'failed';
  const twitterSkipped = twitterChannel?.status === 'skipped';

  useEffect(() => {
    if (!backendChannels.length) return;
    let i = 0;
    const timer = setInterval(() => {
      if (i >= backendChannels.length) { clearInterval(timer); return; }
      const ch = backendChannels[i];
      if (ch.channel === 'email') patchChannel('email', ch.status === 'success');
      if (ch.channel === 'twitter') patchChannel('twitter', ch.status === 'success');
      i++;
    }, 600);
    return () => clearInterval(timer);
  }, [backendChannels, patchChannel]);

  const goTrack = () => {
    const filed = fileCurrent();
    const trackId = cur.backendResult?.complaint_id || filed.id;
    navigate(`/track/${trackId}`);
  };

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        {/* Header */}
        <div className="text-center mt-1">
          <div className="w-12 h-12 rounded-full bg-olive border-[1.5px] border-line mx-auto mb-2 flex items-center justify-center text-mist text-2xl animate-pop-in">
            {hasBackend ? '✓' : '⚠'}
          </div>
          <h1 className="font-hand text-coffee text-[22px] leading-tight">
            {hasBackend
              ? (isBundled ? `Bundled with ${bundleN} others` : 'Complaint Filed')
              : 'Complaint Saved Locally'}
          </h1>
          {hasBackend && (
            <div className="font-sans text-[11px] text-coffee/70 mt-1">
              {issueType} · {wardName || 'Bengaluru'} · {agencyName}
            </div>
          )}
          {!hasBackend && (
            <div className="font-sans text-[11px] text-rust mt-1">
              Backend unavailable — will retry when online
            </div>
          )}
        </div>

        {/* Crowd Validation Map (from Crowd.jsx) */}
        <Card tone="mist" padding="p-0" className="mt-3 overflow-hidden relative" style={{ height: bundleN > 0 ? 200 : 96 }}>
          <svg viewBox={bundleN > 0 ? "0 0 220 200" : "0 0 220 96"} width="100%" height="100%" preserveAspectRatio="xMidYMid slice" className="block">
            {bundleN > 0 && (
              <>
                <circle cx="110" cy="100" r="80" fill="none" stroke="#342a21" strokeWidth="1" strokeDasharray="4 4" />
                <text x="110" y="30" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="8" fill="#5a4a38" letterSpacing="1.5">500m RADIUS</text>
                {Array.from({ length: bundleN }).map((_, i) => {
                  const ang = i * 137.5 * Math.PI / 180;
                  const r = 25 + (i * 7) % 50;
                  const x = 110 + Math.cos(ang) * r;
                  const y = 100 + Math.sin(ang) * r;
                  return <circle key={i} cx={x} cy={y} r="3" fill="#71816d" stroke="#342a21" strokeWidth=".7" style={{ animation: `pop-in .35s ${i * 30}ms ease-out backwards` }} />;
                })}
                <g style={{ animation: 'pop-in .5s 1s ease-out backwards' }}>
                  <circle cx="110" cy="100" r="30" fill="#71816d" fillOpacity=".22" />
                  <circle cx="110" cy="100" r="18" fill="#71816d" stroke="#342a21" strokeWidth="1.5" />
                  <text x="110" y="105" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="14" fill="#fbf8f1" fontWeight="700">{total}</text>
                </g>
              </>
            )}
            {bundleN === 0 && (
              <>
                <path d="M10 70 Q 50 20, 110 30 Q 170 40, 210 70 Q 150 85, 10 70 z" fill="none" stroke="#71816d" strokeWidth="1.4" strokeDasharray="3 3" />
                <circle cx="110" cy="48" r="14" fill="#71816d" stroke="#342a21" strokeWidth="1.4" />
                <text x="110" y="53" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="11" fill="#fbf8f1" fontWeight="600">1</text>
                <text x="110" y="82" textAnchor="middle" fontFamily="Caveat" fontSize="12" fill="#342a21">Your complaint</text>
              </>
            )}
          </svg>
        </Card>

        {/* Bundle info */}
        {isBundled && (
          <Card tone="coffee" padding="px-3 py-2" className="mt-2">
            <div className="font-sans text-[9px] uppercase tracking-wider opacity-70">Crowd Validated</div>
            <div className="font-hand text-[15px] font-bold mt-0.5">Joint complaint filed on behalf of {total} residents</div>
          </Card>
        )}

        {/* Dispatch status — show real results from backend */}
        {hasBackend && (
          <div className="mt-3">
            <div className="font-sans text-[9px] uppercase tracking-wider text-coffee/65 mb-1.5">Dispatch Status</div>
            <div className="space-y-1.5">
              {/* Email */}
              {emailChannel && (
                <Card padding="px-2.5 py-1.5" className="flex items-center gap-2">
                  <span className={'w-2 h-2 rounded-full ' + (emailSent ? 'bg-olive' : emailSkipped ? 'bg-coffee/30' : 'bg-beige animate-pulse-soft')} />
                  <span className="font-sans text-[11px] font-semibold text-coffee">Email</span>
                  <span className="font-mono text-[10px] text-coffee/65">
                    {emailSent ? 'sent to ward officer' : emailSkipped ? 'disabled in settings' : 'sending...'}
                  </span>
                  <span className={'ml-auto font-sans text-[11px] font-semibold ' + (emailSent ? 'text-olive' : emailSkipped ? 'text-coffee/40' : 'text-coffee/55')}>
                    {emailSent ? '✓' : emailSkipped ? '—' : '…'}
                  </span>
                </Card>
              )}
              {/* Twitter */}
              {twitterChannel && (
                <Card padding="px-2.5 py-1.5" className="flex items-center gap-2">
                  <span className={'w-2 h-2 rounded-full ' + (twitterSent ? 'bg-olive' : twitterSkipped ? 'bg-coffee/30' : twitterFailed ? 'bg-rust' : 'bg-beige animate-pulse-soft')} />
                  <span className="font-sans text-[11px] font-semibold text-coffee">Twitter</span>
                  <span className="font-mono text-[10px] text-coffee/65">
                    {twitterSent ? (cur.backendResult?.routing?.twitter_handle || '@BBMPCOMM') : twitterSkipped ? 'disabled in settings' : twitterFailed ? 'failed' : 'posting...'}
                  </span>
                  <span className={'ml-auto font-sans text-[11px] font-semibold ' + (twitterSent ? 'text-olive' : twitterSkipped ? 'text-coffee/40' : twitterFailed ? 'text-rust' : 'text-coffee/55')}>
                    {twitterSent ? '✓' : twitterSkipped ? '—' : twitterFailed ? '✗' : '…'}
                  </span>
                </Card>
              )}
            </div>
            {subStatus === 'suppressed' && (
              <div className="font-sans text-[10px] text-coffee/65 mt-1.5 text-center">
                Joined existing cluster · next email at milestone
              </div>
            )}
          </div>
        )}

        <Button variant="primary" onClick={goTrack} full size="md" className="mt-auto">
          {T('conf.track')}
        </Button>
      </div>
    </PhoneFrame>
  );
}

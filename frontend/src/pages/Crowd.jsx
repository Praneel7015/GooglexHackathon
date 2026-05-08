import { PhoneFrame, Card, Button } from '../components/ui';
import { useApp } from '../lib/store';
import { useNavigate } from 'react-router-dom';
import { useT } from '../lib/i18n';

export default function Crowd() {
  const T = useT();
  const navigate = useNavigate();
  const bundleSize = useApp(s => s.current.bundleSize) || 0;
  const total = bundleSize + 1;

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <div className="text-center">
          <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55">{T('crowd.moment')}</div>
          <h1 className="font-hand text-[22px] text-coffee leading-tight mt-0.5">{T('crowd.heading')}</h1>
        </div>

        <Card tone="mist" padding="p-0" className="mt-3 h-72 overflow-hidden relative">
          <svg viewBox="0 0 220 280" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
            <g stroke="#c9b79c" strokeWidth="2" fill="none" strokeLinecap="round">
              <path d="M 0 100 L 220 130" />
              <path d="M 110 0 L 130 280" />
              <path d="M 0 200 L 220 220" />
            </g>
            <circle cx="110" cy="140" r="90" fill="none" stroke="#342a21" strokeWidth="1" strokeDasharray="4 4" />
            <text x="110" y="44" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="8" fill="#5a4a38" letterSpacing="1.5">500m RADIUS</text>
            {Array.from({ length: bundleSize }).map((_, i) => {
              const ang = i * 137.5 * Math.PI / 180;
              const r = 30 + (i * 7) % 60;
              const x = 110 + Math.cos(ang) * r;
              const y = 140 + Math.sin(ang) * r;
              return <circle key={i} cx={x} cy={y} r="3" fill="#71816d" stroke="#342a21" strokeWidth=".7" style={{ animation: `pop-in .35s ${i * 30}ms ease-out backwards` }} />;
            })}
            <g style={{ animation: 'pop-in .5s 1.2s ease-out backwards' }}>
              <circle cx="110" cy="140" r="36" fill="#71816d" fillOpacity=".22" />
              <circle cx="110" cy="140" r="22" fill="#71816d" stroke="#342a21" strokeWidth="1.5" />
              <text x="110" y="146" textAnchor="middle" fontFamily="JetBrains Mono" fontSize="16" fill="#fbf8f1" fontWeight="700">{total}</text>
            </g>
          </svg>
        </Card>

        <Card tone="coffee" padding="px-3 py-2.5" className="mt-3">
          <div className="font-sans text-[9px] uppercase tracking-wider opacity-70">{T('crowd.bundled')}</div>
          <div className="font-hand text-[16px] font-bold mt-0.5">{T('crowd.filed', { n: total })}</div>
        </Card>

        <Button variant="primary" onClick={() => navigate('/track')} full className="mt-auto">{T('crowd.continue')}</Button>
      </div>
    </PhoneFrame>
  );
}

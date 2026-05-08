import { Card, Chip, Button } from '../components/ui';
import { Link } from 'react-router-dom';

function FauxQR({ size = 220 }) {
  const grid = 25;
  const cell = size / grid;
  const filled = (x, y) => {
    if (x < 7 && y < 7)              return x === 0 || x === 6 || y === 0 || y === 6 || (x >= 2 && x <= 4 && y >= 2 && y <= 4);
    if (x > grid - 8 && y < 7)       { const ax = x - (grid - 7), ay = y; return ax === 0 || ax === 6 || ay === 0 || ay === 6 || (ax >= 2 && ax <= 4 && ay >= 2 && ay <= 4); }
    if (x < 7 && y > grid - 8)       { const ax = x, ay = y - (grid - 7); return ax === 0 || ax === 6 || ay === 0 || ay === 6 || (ax >= 2 && ax <= 4 && ay >= 2 && ay <= 4); }
    return ((x * 131 + y * 977 + x * y * 17) % 7) < 3;
  };
  const cells = [];
  for (let y = 0; y < grid; y++)
    for (let x = 0; x < grid; x++)
      if (filled(x, y)) cells.push(<rect key={`${x}-${y}`} x={x * cell} y={y * cell} width={cell} height={cell} fill="#342a21" />);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <rect width={size} height={size} fill="#fbf8f1" />
      {cells}
      <rect x={size / 2 - 18} y={size / 2 - 18} width="36" height="36" fill="#fbf8f1" />
      <circle cx={size / 2} cy={size / 2} r="14" fill="#71816d" stroke="#342a21" strokeWidth="1.5" />
      <text x={size / 2} y={size / 2 + 5} textAnchor="middle" fontFamily="Caveat" fontSize="16" fill="#fbf8f1" fontWeight="700">N</text>
    </svg>
  );
}

export default function Install() {
  return (
    <section className="max-w-[1280px] mx-auto px-4 md:px-8 py-10 md:py-16 grid md:grid-cols-2 gap-10 items-center">
      <div>
        <Chip>Install · ಸ್ಥಾಪಿಸಿ</Chip>
        <h1 className="font-hand font-bold text-coffee text-4xl md:text-6xl leading-[.95] mt-2 tracking-tight">
          Carry the city<br />in your pocket.
        </h1>
        <p className="font-kn text-coffee/70 text-base mt-3">ನಗರವನ್ನು ಜೇಬಿನಲ್ಲಿ ಇಟ್ಟುಕೊಳ್ಳಿ.</p>
        <p className="font-sans text-[14px] text-coffee mt-5 max-w-md leading-relaxed">
          NammaCity is a Progressive Web App. No app store. No 60-MB download.
          Scan the code, tap "Add to Home Screen", and you're filing complaints in 30 seconds.
        </p>
        <ol className="mt-6 space-y-3">
          {[
            ['Scan the QR with your phone camera', 'iPhone or Android · works offline once installed'],
            ['Tap "Add to Home Screen"',           'Looks and behaves like a native app'],
            ['Open NammaCity → start filing',      'First-time onboarding takes 90 seconds']
          ].map(([h, s], i) => (
            <li key={i} className="flex gap-3 items-start">
              <span className="font-mono text-[12px] text-olive font-semibold pt-0.5">0{i + 1}</span>
              <div>
                <div className="font-sans font-semibold text-coffee text-[13.5px]">{h}</div>
                <div className="font-sans text-[12px] text-coffee/65">{s}</div>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-7 flex flex-wrap gap-3 items-center">
          <Button as={Link} to="/onboard" variant="secondary" size="md">Start onboarding →</Button>
          <span className="font-sans text-[11px] text-coffee/55">or visit <span className="font-mono text-olive">nammacity.org</span> on your phone</span>
        </div>
      </div>

      {/* QR card */}
      <div className="flex flex-col items-center">
        <Card padding="p-6" className="bg-paper shadow-deep">
          <FauxQR size={220} />
          <div className="text-center mt-4">
            <div className="font-hand text-coffee text-lg font-bold">NammaCity · ನಮ್ಮಸಿಟಿ</div>
            <div className="font-mono text-[9px] tracking-wider text-olive">SCAN TO INSTALL</div>
          </div>
        </Card>
        <div className="mt-5 flex gap-3 font-sans text-[10px] text-coffee/65">
          <span>iOS Safari</span><span className="opacity-40">·</span>
          <span>Android Chrome</span><span className="opacity-40">·</span>
          <span>Edge / Firefox</span>
        </div>
      </div>
    </section>
  );
}

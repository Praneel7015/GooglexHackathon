import { useParams, Link } from 'react-router-dom';
import { Card, Chip } from '../components/ui';
import { officerForWard, WARDS, COMPLAINTS } from '../lib/seed';
import { useT } from '../lib/i18n';

export default function Officer() {
  const T = useT();
  const { id } = useParams();
  const wardId = Number(id) || 95;
  const officer = officerForWard(wardId);
  const recent = COMPLAINTS.filter(c => c.ward === wardId).slice(0, 6);

  return (
    <section className="max-w-[1280px] mx-auto px-4 md:px-8 py-8 md:py-12 grid md:grid-cols-[200px_1fr] gap-8 md:gap-12">
      <div>
        <div className="img-x w-40 h-52 mb-3" />
        <div className="font-hand text-coffee text-2xl font-bold leading-tight">{officer.name}</div>
        <hr className="border-line my-3" />
        <table className="font-sans text-[12px] w-full">
          <tbody>
            <tr><td className="text-[10px] uppercase tracking-wider text-coffee/55 pt-1">{T('off.role')}</td></tr>
            <tr><td className="pb-2">{officer.role}</td></tr>
            <tr><td className="text-[10px] uppercase tracking-wider text-coffee/55 pt-1">{T('off.ward')}</td></tr>
            <tr><td className="pb-2">{officer.ward} · {officer.wardName}</td></tr>
            <tr><td className="text-[10px] uppercase tracking-wider text-coffee/55 pt-1">{T('off.jurisdiction')}</td></tr>
            <tr><td className="pb-2">BBMP Roads · {officer.zone}</td></tr>
            <tr><td className="text-[10px] uppercase tracking-wider text-coffee/55 pt-1">{T('off.tenure')}</td></tr>
            <tr><td className="font-mono text-[11px]">{T('off.since', { y: officer.since })}</td></tr>
          </tbody>
        </table>
      </div>

      <div>
        <Chip>{T('off.chip', { ward: officer.ward })}</Chip>
        <h1 className="font-hand text-coffee text-3xl md:text-4xl mt-1 mb-5 tracking-tight">{T('off.heading')}</h1>

        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            [officer.handled.toLocaleString(), T('off.handled'),  T('off.handled.sub'),  'coffee'],
            [`${officer.avgResponse}d`,        T('off.response'), T('off.response.sub'), 'coffee'],
            [`${officer.resolutionRate}%`,      T('off.rate'),     T('off.rate.sub'),     'olive']
          ].map(([n, l, s, c], i) => (
            <Card key={i} tone="paper">
              <div className={'font-hand text-2xl md:text-3xl font-bold leading-none ' + (c === 'olive' ? 'text-olive' : 'text-coffee')}>{n}</div>
              <div className="font-sans font-semibold text-coffee text-[11px] mt-1.5">{l}</div>
              <div className="font-sans text-coffee/55 text-[10px]">{s}</div>
            </Card>
          ))}
        </div>

        <Chip>{T('off.chart')}</Chip>
        <Card padding="p-4" className="mt-2 mb-6">
          <svg viewBox="0 0 480 80" width="100%" height="80">
            <line x1="0" y1="78" x2="480" y2="78" stroke="#c9b79c" strokeWidth="1" />
            <path d="M 0 60 L 40 50 L 80 55 L 120 40 L 160 35 L 200 42 L 240 30 L 280 28 L 320 22 L 360 26 L 400 18 L 440 14 L 480 10"
              stroke="#71816d" strokeWidth="2" fill="none" strokeLinecap="round" />
            {[0,40,80,120,160,200,240,280,320,360,400,440,480].map((x, i) => {
              const ys = [60,50,55,40,35,42,30,28,22,26,18,14,10];
              return <circle key={i} cx={x} cy={ys[i]} r="2.4" fill="#71816d" stroke="#342a21" strokeWidth=".6" />;
            })}
            {['Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'].map((m, i) =>
              <text key={m} x={i * 40 + 10} y={90} fontFamily="JetBrains Mono" fontSize="8" fill="#8a7560">{m}</text>
            )}
          </svg>
        </Card>

        <Chip>{T('off.log')}</Chip>
        <ul className="mt-2">
          {recent.map(r => (
            <li key={r.id} className="grid grid-cols-[80px_1fr_100px_80px] py-2 border-b border-dashed border-beige font-sans text-[12px] items-center">
              <span className="font-mono text-[10px] text-olive">{r.id}</span>
              <span className="text-coffee font-medium">{r.issue} · {r.wardName}</span>
              <Chip tone={r.status === 'resolved' ? 'olive' : 'paper'}>{r.status}</Chip>
              <span className="font-mono text-[10px] text-coffee/55 text-right">{r.ageDays}d ago</span>
            </li>
          ))}
        </ul>

        <Link to="/leaderboard" className="block mt-6 font-sans text-[12px] text-olive font-semibold underline">{T('off.back')}</Link>
      </div>
    </section>
  );
}

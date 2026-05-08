import { useParams, Link } from 'react-router-dom';
import { Card, Chip } from '../components/ui';
import { useApp } from '../lib/store';
import { useT } from '../lib/i18n';

export default function Track() {
  const T = useT();
  const { id } = useParams();
  const filed = useApp(s => s.filed);
  const item = filed.find(c => c.id === id) || filed[0];
  const headerId = item?.id || 'NMC-2467';
  const issue = item?.issue || 'Pothole';
  const ward = item?.wardName || 'Yelahanka Main Rd';

  const DEFAULT_STEPS = [
    { day: 0,  label: 'Filed · BBMP Roads',                status: 'sent' },
    { day: 3,  label: 'Twitter escalation · @BBMPCOMM',    status: 'sent' },
    { day: 7,  label: 'Cc Ward Engineer (Yelahanka)',      status: 'active' },
    { day: 14, label: 'CC councillor + RTI draft',         status: 'queued' },
    { day: 21, label: 'Press alert · The Hindu civic desk',status: 'queued' },
    { day: 30, label: 'Public dashboard auto-elevation',   status: 'queued' }
  ];

  const steps = item?.timeline || DEFAULT_STEPS;

  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-[11px] text-coffee/65">{headerId}</span>
        <Chip tone="olive">{T('tr.active')}</Chip>
      </div>
      <h1 className="font-hand text-coffee text-2xl leading-tight">{issue} · {ward} · Severity {item?.severity || 4}</h1>

      <Card tone="mist" padding="p-3" className="mt-3">
        <div className="text-[9px] uppercase tracking-wider font-sans text-coffee/65">{T('tr.likelihood')}</div>
        <div className="font-hand text-[20px] text-coffee mt-1">73% in 21 days</div>
        <div className="h-2 bg-paper border-[1.4px] border-line rounded-full mt-2 overflow-hidden">
          <div className="h-full bg-olive transition-[width] duration-500" style={{ width: '73%' }} />
        </div>
        <div className="text-[10px] font-sans text-coffee/65 mt-1.5">{T('tr.basis')}</div>
      </Card>

      <div className="relative mt-5 pl-1">
        <div className="absolute left-[14px] top-2 bottom-2 w-px border-l border-dashed border-beige" />
        {steps.map((s, i) => {
          const active = s.status === 'active';
          return (
            <div key={i} className="flex gap-3 py-1.5 items-start">
              <div className="w-7 flex justify-center pt-0.5">
                <span className={['w-3.5 h-3.5 rounded-full border-[1.5px] border-line',
                  s.status === 'sent' ? 'bg-olive' : 'bg-paper',
                  active ? 'shadow-[0_0_0_4px_rgba(113,129,109,.25)] animate-pulse-soft' : ''
                ].join(' ')} />
              </div>
              <div className={`flex-1 ${active ? 'border-l-2 border-olive pl-2 -ml-0.5' : ''}`}>
                <div className="flex justify-between font-sans text-[11.5px] font-semibold">
                  <span className={active ? 'text-coffee' : 'text-coffee/65'}>Day {s.day} · {s.label}</span>
                  <span className="font-mono text-[10px] text-olive">
                    {s.status === 'sent' ? '✓' : s.status === 'active' ? '· · ·' : ''}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <Link to="/dashboard" className="block mt-6 font-sans text-[12px] text-olive font-semibold underline">{T('tr.dashboard')}</Link>

      {filed.length > 1 && (
        <div className="mt-8">
          <Chip>{T('tr.others')}</Chip>
          <ul className="mt-2 space-y-1">
            {filed.filter(c => c.id !== item?.id).map(c => (
              <li key={c.id}>
                <Link to={`/track/${c.id}`} className="grid grid-cols-[80px_1fr_60px] gap-2 py-1 text-[11.5px] font-sans hover:bg-mist rounded px-1.5">
                  <span className="font-mono text-olive">{c.id}</span>
                  <span className="text-coffee">{c.issue}</span>
                  <span className="font-mono text-[10px] text-coffee/55 text-right">sev {c.severity}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Card, Chip } from '../components/ui';
import { useApp } from '../lib/store';
import { api } from '../lib/api';
import { useT } from '../lib/i18n';

export default function Track() {
  const T = useT();
  const { id } = useParams();
  const filed = useApp(s => s.filed);

  const [liveDetail, setLiveDetail] = useState(null);
  const [liveList, setLiveList] = useState(null);

  useEffect(() => {
    if (id) {
      api.getComplaint(id).then(data => { if (data) setLiveDetail(data); });
    }
    api.listComplaints({ limit: 20 }).then(data => { if (data) setLiveList(data.complaints); });
  }, [id]);

  const localItem = filed.find(c => c.id === id) || filed[0];

  const headerId = liveDetail?.id?.slice(0, 13) || localItem?.id || 'NMC-2467';
  const issue = liveDetail?.issue_type?.replace(/_/g, ' ') || localItem?.issue || 'Pothole';
  const ward = liveDetail?.location?.ward_name || localItem?.wardName || 'Yelahanka Main Rd';
  const severity = liveDetail?.severity || localItem?.severity || 4;

  const DEFAULT_STEPS = [
    { day: 0,  label: 'Filed · BBMP Roads',                status: 'sent' },
    { day: 3,  label: 'Twitter escalation · @BBMPCOMM',    status: 'sent' },
    { day: 7,  label: 'Cc Ward Engineer (Yelahanka)',      status: 'active' },
    { day: 14, label: 'CC councillor + RTI draft',         status: 'queued' },
    { day: 21, label: 'Press alert · The Hindu civic desk',status: 'queued' },
    { day: 30, label: 'Public dashboard auto-elevation',   status: 'queued' }
  ];

  const steps = liveDetail?.escalation?.timeline
    ? liveDetail.escalation.timeline.map(t => ({
        day: t.stage === 'submitted' ? 0 : t.stage === 'councillor_tagged' ? 7 :
             t.stage === 'rti_filed' ? 14 : t.stage === 'mla_tagged' ? 21 : 30,
        label: t.action,
        status: t.completed ? 'sent' : (liveDetail.escalation.current_stage === t.stage ? 'active' : 'queued'),
      }))
    : (localItem?.timeline || DEFAULT_STEPS);

  const otherComplaints = liveList
    ? liveList.filter(c => c.id !== (liveDetail?.id || id)).slice(0, 5)
    : filed.filter(c => c.id !== localItem?.id);

  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-[11px] text-coffee/65">{headerId}</span>
        <Chip tone="olive">{T('tr.active')}</Chip>
      </div>
      <h1 className="font-hand text-coffee text-2xl leading-tight">{issue} · {ward} · Severity {severity}</h1>

      <Card tone="mist" padding="p-3" className="mt-3">
        <div className="text-[9px] uppercase tracking-wider font-sans text-coffee/65">{T('tr.likelihood')}</div>
        <div className="font-hand text-[20px] text-coffee mt-1">73% in 21 days</div>
        <div className="h-2 bg-paper border-[1.4px] border-line rounded-full mt-2 overflow-hidden">
          <div className="h-full bg-olive transition-[width] duration-500" style={{ width: '73%' }} />
        </div>
        <div className="text-[10px] font-sans text-coffee/65 mt-1.5">{T('tr.basis')}</div>
      </Card>

      <div className="relative mt-5 px-1">
        {steps.map((s, i) => {
          const status = s.status;
          const done = status === 'sent';
          const active = status === 'active';
          const isLast = i === steps.length - 1;

          return (
            <div key={i} className={`flex gap-4 items-stretch transition-opacity duration-300 ${status === 'queued' ? 'opacity-55' : 'opacity-100'}`}>
              <div className="w-5 flex flex-col items-center relative">
                {!isLast && (
                  <div className={['absolute top-5 bottom-0 w-[2px] rounded-full transition-colors duration-500',
                    done ? 'bg-olive' : 'bg-line/20'].join(' ')} />
                )}
                <div className="z-10 bg-paper py-1">
                  <span className={['flex items-center justify-center w-[18px] h-[18px] rounded-full border-[2px] transition-colors duration-300',
                    done ? 'bg-olive border-olive text-mist' :
                    active ? 'bg-paper border-olive shadow-[0_0_0_4px_rgba(113,129,109,.15)] animate-pulse-soft' :
                    'bg-paper border-line/40'
                  ].join(' ')}>
                    {done && (
                      <svg viewBox="0 0 14 14" className="w-[10px] h-[10px]">
                        <path d="M3 7.5 L5.5 10 L11 4" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </span>
                </div>
              </div>
              <div className="flex-1 pb-6 pt-1">
                <div className={['font-sans text-[12.5px] font-semibold transition-colors', active ? 'text-coffee' : 'text-coffee/70'].join(' ')}>
                  Day {s.day} · {s.label}
                </div>
                {active && (
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="flex h-1.5 w-1.5 rounded-full bg-olive animate-pulse" />
                    <span className="text-[10.5px] font-medium text-olive/90 uppercase tracking-tight">Active Step</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Link to="/dashboard" className="block mt-6 font-sans text-[12px] text-olive font-semibold underline">{T('tr.dashboard')}</Link>

      {otherComplaints.length > 0 && (
        <div className="mt-8">
          <Chip>{T('tr.others')}</Chip>
          <ul className="mt-2 space-y-1">
            {otherComplaints.map(c => (
              <li key={c.id}>
                <Link to={`/track/${c.id}`} className="grid grid-cols-[80px_1fr_60px] gap-2 py-1 text-[11.5px] font-sans hover:bg-mist rounded px-1.5">
                  <span className="font-mono text-olive">{(c.id || '').slice(0, 8)}</span>
                  <span className="text-coffee">{(c.issue_type || c.issue || '').replace(/_/g, ' ')}</span>
                  <span className="font-mono text-[10px] text-coffee/55 text-right">sev {c.severity || '?'}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

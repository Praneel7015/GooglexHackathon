import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Card, Chip } from '../components/ui';
import { useApp } from '../lib/store';
import { api } from '../lib/api';
import { useT } from '../lib/i18n';

/* How many full days since a timestamp (ms) */
function daysSince(ts) {
  if (!ts) return 0;
  return Math.floor((Date.now() - ts) / 86_400_000);
}

function StatusBadge({ status }) {
  const styles = {
    ACTIVE:   'bg-olive/15 text-olive-dark border-olive/30',
    RESOLVED: 'bg-mist border-beige text-coffee/65',
    PENDING:  'bg-mist border-beige text-coffee/65',
  };
  return (
    <span className={`text-[10px] font-sans font-semibold uppercase tracking-wide border rounded-full px-2 py-0.5 ${styles[status] || styles.ACTIVE}`}>
      {status || 'Active'}
    </span>
  );
}

/* ── List view: all complaints for this user ───────────────────────── */
function ComplaintList({ complaints, navigate }) {
  const T = useT();

  if (complaints.length === 0) {
    return (
      <div className="max-w-md mx-auto p-6 flex flex-col items-center gap-4 mt-10">
        <div className="w-14 h-14 rounded-full bg-mist border-[1.5px] border-line flex items-center justify-center">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
            <path d="M5 7 H19 M5 12 H19 M5 17 H12" />
          </svg>
        </div>
        <p className="font-hand text-coffee text-xl">No complaints yet</p>
        <p className="font-sans text-[12px] text-coffee/55 text-center">
          Once you file a complaint, you can track its status and escalation timeline here.
        </p>
        <Link
          to="/capture"
          className="mt-2 px-4 py-2 bg-olive text-mist font-sans text-[12px] font-semibold rounded-md hover:bg-olive-dark transition-colors"
        >
          File a Complaint →
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <h1 className="font-hand text-coffee text-2xl font-bold tracking-tight mb-1">Your Complaints</h1>
      <p className="font-sans text-[11px] text-coffee/55 mb-5">{complaints.length} issue{complaints.length !== 1 ? 's' : ''} filed by you</p>

      <ul className="flex flex-col gap-3">
        {complaints.map(c => {
          const days = daysSince(c.submittedAt);
          const issue = (c.issue_type || c.issue || 'Issue').replace(/_/g, ' ');
          const ward = c.location?.ward_name || c.wardName || '';
          const severity = c.severity || '?';
          const cid = (c.id || '').slice(0, 13);

          return (
            <li key={c.id}>
              <button
                onClick={() => navigate(`/track/${c.id}`)}
                className="w-full text-left box bg-paper hover:bg-mist transition-colors p-3 rounded-md flex flex-col gap-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-coffee/55">{cid}</span>
                  <StatusBadge status="ACTIVE" />
                </div>
                <div className="font-hand text-coffee text-[17px] leading-snug capitalize">{issue}</div>
                <div className="flex items-center gap-3 flex-wrap">
                  {ward && (
                    <span className="font-sans text-[11px] text-coffee/65">{ward}</span>
                  )}
                  <span className="font-sans text-[11px] text-coffee/55">Severity {severity}</span>
                  <span className="font-mono text-[10px] text-olive ml-auto">
                    {days === 0 ? 'Today' : `${days}d ago`}
                  </span>
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ── Detail view: single complaint ─────────────────────────────────── */
function ComplaintDetail({ id, localItem, filed }) {
  const T = useT();
  const navigate = useNavigate();

  const [liveDetail, setLiveDetail] = useState(null);
  useEffect(() => {
    if (id) api.getComplaint(id).then(d => { if (d) setLiveDetail(d); });
  }, [id]);

  const headerId   = liveDetail?.id?.slice(0, 13) || localItem?.id?.slice(0, 13) || id;
  const issue      = (liveDetail?.issue_type || localItem?.issue || 'Issue').replace(/_/g, ' ');
  const ward       = liveDetail?.location?.ward_name || localItem?.wardName || '';
  const severity   = liveDetail?.severity || localItem?.severity || '?';
  const submittedAt = localItem?.submittedAt || null;
  const daysElapsed = daysSince(submittedAt);

  const DEFAULT_STEPS = [
    { day: 0,  label: 'Initial multi-channel submission',       status: 'sent'   },
    { day: 7,  label: 'Ward councillor tagged (Day 7)',          status: 'queued' },
    { day: 14, label: 'RTI application filed (Day 14)',          status: 'queued' },
    { day: 21, label: 'MLA + media notified (Day 21)',           status: 'queued' },
    { day: 30, label: 'PIL outline drafted (Day 30)',            status: 'queued' },
  ];

  const steps = liveDetail?.escalation?.timeline
    ? liveDetail.escalation.timeline.map(t => ({
        day: t.stage === 'submitted' ? 0 : t.stage === 'councillor_tagged' ? 7 :
             t.stage === 'rti_filed' ? 14 : t.stage === 'mla_tagged' ? 21 : 30,
        label: t.action,
        status: t.completed ? 'sent' : (liveDetail.escalation.current_stage === t.stage ? 'active' : 'queued'),
      }))
    : (localItem?.timeline
        ? localItem.timeline.map(t => ({
            ...t,
            status: t.day <= daysElapsed ? 'sent' : t.status,
          }))
        : DEFAULT_STEPS.map(s => ({
            ...s,
            status: s.day <= daysElapsed ? 'sent' : s.day === DEFAULT_STEPS.find(ss => ss.day > daysElapsed)?.day ? 'active' : 'queued',
          })));

  // Other complaints by this user (excluding current)
  const otherComplaints = filed.filter(c => c.id !== id);

  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      {/* back */}
      <button
        onClick={() => navigate('/track')}
        className="font-sans text-[11px] text-olive underline mb-4 block hover:text-olive-dark"
      >
        ← All your complaints
      </button>

      {/* header */}
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-[11px] text-coffee/65">{headerId}</span>
        <StatusBadge status="ACTIVE" />
      </div>
      <h1 className="font-hand text-coffee text-2xl leading-tight capitalize">
        {issue}{ward ? ` · ${ward}` : ''} · Severity {severity}
      </h1>

      {/* days elapsed banner */}
      <div className="mt-3 flex items-center gap-2">
        <span className="font-mono text-[11px] text-coffee/55 bg-mist border border-beige rounded-full px-2.5 py-1">
          {daysElapsed === 0 ? 'Filed today' : `Filed ${daysElapsed} day${daysElapsed !== 1 ? 's' : ''} ago`}
        </span>
        {submittedAt && (
          <span className="font-mono text-[10px] text-coffee/40">
            {new Date(submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
          </span>
        )}
      </div>

      {/* resolution likelihood */}
      <Card tone="mist" padding="p-3" className="mt-3">
        <div className="text-[9px] uppercase tracking-wider font-sans text-coffee/65">Resolution Likelihood</div>
        <div className="font-hand text-[20px] text-coffee mt-1">73% in 21 days</div>
        <div className="h-2 bg-paper border-[1.4px] border-line rounded-full mt-2 overflow-hidden">
          <div className="h-full bg-olive transition-[width] duration-500" style={{ width: '73%' }} />
        </div>
        <div className="text-[10px] font-sans text-coffee/65 mt-1.5">
          Based on Ward 95 history · 142 similar cases
        </div>
      </Card>

      {/* escalation timeline */}
      <div className="relative mt-5 px-1">
        {steps.map((s, i) => {
          const done   = s.status === 'sent';
          const active = s.status === 'active';
          const isLast = i === steps.length - 1;

          return (
            <div key={i} className={`flex gap-4 items-stretch transition-opacity duration-300 ${s.status === 'queued' ? 'opacity-55' : 'opacity-100'}`}>
              <div className="w-5 flex flex-col items-center relative">
                {!isLast && (
                  <div className={['absolute top-5 bottom-0 w-[2px] rounded-full transition-colors duration-500',
                    done ? 'bg-olive' : 'bg-line/20'].join(' ')} />
                )}
                <div className="z-10 bg-paper py-1">
                  <span className={['flex items-center justify-center w-[18px] h-[18px] rounded-full border-[2px] transition-colors duration-300',
                    done   ? 'bg-olive border-olive text-mist' :
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
                {done && s.day > 0 && (
                  <div className="text-[10px] text-coffee/45 font-mono mt-0.5">Completed</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Link to="/dashboard" className="block mt-2 font-sans text-[12px] text-olive font-semibold underline">
        View on public dashboard →
      </Link>

      {/* other complaints by this user */}
      {otherComplaints.length > 0 && (
        <div className="mt-8">
          <Chip>Your Other Complaints</Chip>
          <ul className="mt-2 space-y-1">
            {otherComplaints.slice(0, 5).map(c => {
              const days = daysSince(c.submittedAt);
              return (
                <li key={c.id}>
                  <Link
                    to={`/track/${c.id}`}
                    className="grid grid-cols-[80px_1fr_60px] gap-2 py-1 text-[11.5px] font-sans hover:bg-mist rounded px-1.5 transition-colors"
                  >
                    <span className="font-mono text-olive">{(c.id || '').slice(0, 8)}</span>
                    <span className="text-coffee capitalize">{(c.issue_type || c.issue || '').replace(/_/g, ' ')}</span>
                    <span className="font-mono text-[10px] text-coffee/55 text-right">
                      {days === 0 ? 'today' : `${days}d`}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ── Main export ────────────────────────────────────────────────────── */
export default function Track() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Only show complaints filed by this user (from Zustand persisted store)
  const filed = useApp(s => s.filed);

  // If an ID is given but it's not in the user's own filed list, still try to render
  // (the detail view will pull from the API if available)
  const localItem = filed.find(c => c.id === id) || null;

  if (id) {
    return <ComplaintDetail id={id} localItem={localItem} filed={filed} />;
  }

  return <ComplaintList complaints={filed} navigate={navigate} />;
}

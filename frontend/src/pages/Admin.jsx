import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { Card, Chip } from '../components/ui';

/* ─── helpers ───────────────────────────────────────────────────────── */
function daysSince(dateStr) {
  if (!dateStr) return '—';
  const d = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000);
  return d === 0 ? 'Today' : `${d}d`;
}

const STATUS_META = {
  open:        { label: 'Open',        dot: '●', cls: 'bg-olive/15 text-olive-dark border-olive/30' },
  in_progress: { label: 'In Progress', dot: '◑', cls: 'bg-amber-100 text-amber-800 border-amber-300' },
  resolved:    { label: 'Resolved',    dot: '✓', cls: 'bg-mist border-beige text-coffee/70' },
  revoked:     { label: 'Revoked',     dot: '✗', cls: 'bg-rust/10 text-rust border-rust/30' },
};

const ALL_STATUSES = ['open', 'in_progress', 'resolved', 'revoked'];

function StatusBadge({ status }) {
  const m = STATUS_META[status] || STATUS_META.open;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-sans font-semibold uppercase tracking-wide border rounded-full px-2 py-0.5 ${m.cls}`}>
      {m.dot} {m.label}
    </span>
  );
}

/* ─── Stat card ─────────────────────────────────────────────────────── */
function StatCard({ label, value, sub }) {
  return (
    <div className="box bg-paper p-4 flex flex-col gap-1">
      <div className="font-hand text-coffee text-[28px] font-bold leading-none">{value ?? '—'}</div>
      <div className="font-sans text-[11px] font-semibold text-coffee/70">{label}</div>
      {sub && <div className="font-mono text-[9px] text-coffee/40">{sub}</div>}
    </div>
  );
}

/* ─── Inline status picker ──────────────────────────────────────────── */
function StatusPicker({ current, onSelect, loading }) {
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {ALL_STATUSES.map(s => {
        const m = STATUS_META[s];
        const active = s === current;
        return (
          <button
            key={s}
            disabled={active || loading}
            onClick={() => onSelect(s)}
            className={[
              'px-2.5 py-1 rounded-full font-sans text-[10px] font-semibold border transition-all',
              active ? `${m.cls} cursor-default` : 'border-line/30 text-coffee/60 hover:border-olive hover:text-olive bg-paper',
              loading ? 'opacity-40 cursor-not-allowed' : ''
            ].join(' ')}
          >
            {m.dot} {m.label}
          </button>
        );
      })}
    </div>
  );
}

/* ─── Single complaint row ──────────────────────────────────────────── */
function ComplaintRow({ c, onStatusChange }) {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [toast, setToast] = useState('');

  const handleStatus = async (newStatus) => {
    setUpdating(true);
    const res = await api.updateComplaintStatus(c.id, newStatus);
    setUpdating(false);
    if (res?.ok) {
      setToast(`✓ Set to ${STATUS_META[newStatus].label}`);
      onStatusChange(c.id, newStatus);
      setTimeout(() => setToast(''), 2500);
    } else {
      setToast('⚠ Update failed');
      setTimeout(() => setToast(''), 2500);
    }
  };

  return (
    <div className="border-b border-line/10 last:border-0">
      {/* main row */}
      <button
        className="w-full text-left grid grid-cols-[1fr_100px_48px_36px_110px_44px_32px] gap-2 px-4 py-3 hover:bg-mist/50 transition-colors items-center"
        onClick={() => setExpanded(e => !e)}
      >
        <span className="font-mono text-[10px] text-olive truncate">{(c.id || '').slice(0, 13)}</span>
        <span className="font-sans text-[11.5px] text-coffee capitalize truncate">{(c.issue_type || '').replace(/_/g, ' ')}</span>
        <span className="font-sans text-[11px] text-coffee/65 text-center">{c.ward_number || '—'}</span>
        <span className={`font-sans text-[11px] font-bold text-center ${c.severity >= 4 ? 'text-rust' : 'text-coffee/70'}`}>{c.severity || '—'}</span>
        <span><StatusBadge status={c.status} /></span>
        <span className="font-mono text-[10px] text-coffee/50 text-right">{daysSince(c.created_at)}</span>
        <span className="text-coffee/40 text-[10px] text-right">{expanded ? '▲' : '▼'}</span>
      </button>

      {/* expanded panel */}
      {expanded && (
        <div className="px-4 pb-4 pt-1 bg-mist/30 border-t border-line/10">
          {c.description && (
            <p className="font-sans text-[11.5px] text-coffee/75 leading-relaxed mb-3 max-w-2xl">{c.description}</p>
          )}
          <div className="flex flex-wrap gap-4 text-[10px] font-mono text-coffee/50 mb-3">
            {c.ward_name && <span>Ward: {c.ward_name}</span>}
            {c.created_at && <span>Filed: {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>}
            {c.cluster_id && <span>Cluster: {c.cluster_id.slice(0, 8)}</span>}
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <div>
              <div className="font-sans text-[10px] uppercase tracking-wider text-coffee/45 mb-1">Update Status</div>
              <StatusPicker current={c.status} onSelect={handleStatus} loading={updating} />
            </div>
            {toast && (
              <span className={`font-sans text-[11px] font-semibold ${toast.startsWith('✓') ? 'text-olive' : 'text-rust'}`}>
                {toast}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Main Admin Page ───────────────────────────────────────────────── */
const ISSUE_TYPES = ['pothole', 'garbage', 'streetlight', 'sewage', 'water_leak', 'encroachment', 'noise', 'other'];

export default function Admin() {
  const navigate = useNavigate();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Filters
  const [filterStatus, setFilterStatus]     = useState('');
  const [filterIssue, setFilterIssue]       = useState('');
  const [filterWard, setFilterWard]         = useState('');
  const [searchId, setSearchId]             = useState('');

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    const params = { limit: 200 };
    if (filterStatus) params.status = filterStatus;
    if (filterIssue)  params.issue_type = filterIssue;
    if (filterWard)   params.ward_number = filterWard;
    const res = await api.listComplaints(params);
    if (res) {
      setComplaints(res.complaints || []);
      setTotal(res.total || 0);
    }
    setLoading(false);
  }, [filterStatus, filterIssue, filterWard]);

  useEffect(() => { fetchComplaints(); }, [fetchComplaints]);

  // Optimistic status update
  const handleStatusChange = (id, newStatus) => {
    setComplaints(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
  };

  // Client-side ID search filter
  const visible = searchId.trim()
    ? complaints.filter(c => (c.id || '').toLowerCase().includes(searchId.toLowerCase()))
    : complaints;

  // Stats computed from loaded complaints
  const counts = ALL_STATUSES.reduce((acc, s) => {
    acc[s] = complaints.filter(c => c.status === s).length;
    return acc;
  }, {});

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      {/* header */}
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <div>
          <h1 className="font-hand text-coffee text-2xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="font-sans text-[11px] text-coffee/55">Manage all complaints · {total} total in DB</p>
        </div>
        <button
          onClick={fetchComplaints}
          className="px-3 py-1.5 border border-line rounded-md font-sans text-[11px] text-coffee hover:bg-mist transition-colors flex items-center gap-1.5"
        >
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0 1 15-5.7M20 15a9 9 0 0 1-15 5.7" />
          </svg>
          Refresh
        </button>
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Open"        value={counts.open}        sub="awaiting action" />
        <StatCard label="In Progress" value={counts.in_progress} sub="being handled" />
        <StatCard label="Resolved"    value={counts.resolved}    sub="completed" />
        <StatCard label="Revoked"     value={counts.revoked}     sub="dismissed" />
      </div>

      {/* filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <input
          type="text"
          value={searchId}
          onChange={e => setSearchId(e.target.value)}
          placeholder="Search by complaint ID…"
          className="flex-1 min-w-[180px] bg-paper border border-line rounded-md px-3 py-1.5 font-mono text-[11px] text-coffee placeholder-coffee/35 focus:outline-none focus:border-olive"
        />
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="bg-paper border border-line rounded-md px-2 py-1.5 font-sans text-[11px] text-coffee focus:outline-none focus:border-olive"
        >
          <option value="">All Statuses</option>
          {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_META[s].label}</option>)}
        </select>
        <select
          value={filterIssue}
          onChange={e => setFilterIssue(e.target.value)}
          className="bg-paper border border-line rounded-md px-2 py-1.5 font-sans text-[11px] text-coffee focus:outline-none focus:border-olive"
        >
          <option value="">All Issue Types</option>
          {ISSUE_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
        </select>
        <input
          type="number"
          value={filterWard}
          onChange={e => setFilterWard(e.target.value)}
          placeholder="Ward #"
          className="w-20 bg-paper border border-line rounded-md px-2 py-1.5 font-sans text-[11px] text-coffee focus:outline-none focus:border-olive"
        />
      </div>

      {/* table */}
      <div className="box bg-paper overflow-hidden">
        {/* header row */}
        <div className="grid grid-cols-[1fr_100px_48px_36px_110px_44px_32px] gap-2 px-4 py-2 bg-coffee text-mist/70 font-sans text-[9px] uppercase tracking-wider border-b border-line/20">
          <span>Complaint ID</span>
          <span>Issue Type</span>
          <span className="text-center">Ward</span>
          <span className="text-center">Sev</span>
          <span>Status</span>
          <span className="text-right">Age</span>
          <span />
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <div className="w-6 h-6 border-2 border-olive border-t-transparent rounded-full animate-spin" />
              <span className="font-sans text-[11px] text-coffee/55">Loading complaints…</span>
            </div>
          </div>
        ) : visible.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <p className="font-sans text-[12px] text-coffee/45">No complaints match the current filters.</p>
          </div>
        ) : (
          <div>
            {visible.map(c => (
              <ComplaintRow key={c.id} c={c} onStatusChange={handleStatusChange} />
            ))}
          </div>
        )}

        {/* footer */}
        {!loading && visible.length > 0 && (
          <div className="px-4 py-2 border-t border-line/10 bg-mist/20">
            <span className="font-mono text-[9px] text-coffee/40">
              Showing {visible.length} of {complaints.length} loaded complaints
              {(filterStatus || filterIssue || filterWard || searchId) && ' · filters active'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

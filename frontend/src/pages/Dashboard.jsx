import BangaloreMap from '../components/BangaloreMap';
import { Card, Chip, Logo } from '../components/ui';
import { aggregateStats, COMPLAINTS, WARDS } from '../lib/seed';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useT } from '../lib/i18n';
import { api } from '../lib/api';

export default function Dashboard() {
  const T = useT();
  const [filter, setFilter] = useState('All');

  // Real data from backend (falls back to seed if backend unavailable)
  const [liveStats, setLiveStats] = useState(null);
  const [liveComplaints, setLiveComplaints] = useState(null);

  useEffect(() => {
    api.getDashboardStats().then(data => { if (data) setLiveStats(data); });
    api.listComplaints({ limit: 8 }).then(data => { if (data) setLiveComplaints(data.complaints); });
  }, []);

  // Use backend data if available, else fall back to seed
  const stats = liveStats ? {
    open: liveStats.totals?.total_open ?? 0,
    resolvedPct: liveStats.totals?.total_complaints
      ? Math.round((liveStats.totals.total_resolved / liveStats.totals.total_complaints) * 100)
      : 0,
    wardsReporting: (liveStats.wards || []).length,
    medianFirstResponse: liveStats.totals?.avg_resolution_days ?? 7.2,
  } : aggregateStats();

  const wards = liveStats?.wards?.length
    ? liveStats.wards.map(w => ({
        id: w.ward_number,
        name: w.ward_name,
        resolution: w.resolution_rate,
        open: w.open,
        tone: w.resolution_rate >= 0.65 ? 'olive' : w.resolution_rate >= 0.4 ? 'beige' : 'coffee',
      }))
    : WARDS;

  const recent = liveComplaints
    ? liveComplaints.map(c => ({
        id: c.id?.slice(0, 8) || 'NMC-?',
        issue: (c.issue_type || '').replace(/_/g, ' '),
        wardName: c.ward_name || '',
        status: c.status || 'open',
      }))
    : [...COMPLAINTS].sort((a, b) => a.ageDays - b.ageDays).slice(0, 8);

  return (
    <div className="bg-paper min-h-[calc(100vh-60px)]">
      {/* stats strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 border-b border-line">
        {[
          [String(stats.open).toLocaleString(),   T('stat.open'),      'beige'],
          [`${stats.resolvedPct}%`,                T('stat.resolved') + ' < 30 days', 'olive'],
          [String(stats.wardsReporting),           T('stat.wards') + ' reporting',    'paper'],
          [`${stats.medianFirstResponse} days`,    'median first response',            'paper']
        ].map(([n, l, tone], i) => (
          <div key={i} className={[
            'p-4 md:p-5 border-r border-line last:border-r-0',
            tone === 'beige' ? 'bg-beige text-coffee' :
            tone === 'olive' ? 'bg-olive text-mist'  :
                              'bg-paper text-coffee'
          ].join(' ')}>
            <div className="font-hand font-bold text-2xl md:text-3xl leading-none tracking-tight">{n}</div>
            <div className="font-sans text-[10px] uppercase tracking-wider mt-1.5 opacity-75">{l}</div>
          </div>
        ))}
      </div>

      {/* main grid */}
      <div className="grid lg:grid-cols-[1.6fr_1fr] gap-0">
        {/* MAP */}
        <div className="relative h-[60vh] lg:h-[calc(100vh-200px)] border-b lg:border-b-0 lg:border-r border-line">
          <BangaloreMap mode="clusters" interactive />
          <div className="absolute top-3 right-3 z-[400] bg-paper border border-line rounded p-2 text-[10px] shadow-sm">
            <div className="font-sans text-[9px] uppercase tracking-wider text-coffee/65 mb-1">{T('dash.density')}</div>
            <div className="flex items-center gap-2">
              <div className="w-20 h-2 border border-line" style={{ background: 'linear-gradient(to right, #f1e0c5, #71816d, #342a21)' }} />
              <span className="font-mono text-[9px]">{T('dash.low')}</span>
              <span className="font-mono text-[9px] ml-auto">{T('dash.high')}</span>
            </div>
          </div>
        </div>

        {/* leaderboard rail */}
        <aside className="bg-paper p-4 md:p-6 lg:overflow-y-auto lg:max-h-[calc(100vh-200px)]">
          <Chip>{T('dash.trending')}</Chip>
          <h3 className="font-hand text-coffee text-2xl mt-1.5 mb-3 leading-tight">{T('dash.rightnow')}</h3>
          <ul className="text-[12px] font-sans space-y-1.5 mb-5">
            {[
              ['Garbage pickup missed · Whitefield', 18],
              ['Pothole · ORR Bellandur stretch', 47],
              ['Streetlight · Sarjapur Rd', 22],
              ['Water leak · Jayanagar 4th block', 12]
            ].map(([title, n]) => (
              <li key={title} className="flex justify-between border-b border-dashed border-beige pb-1">
                <span className="text-coffee">{title}</span>
                <span className="font-mono text-olive">+{n}</span>
              </li>
            ))}
          </ul>

          <Chip>{T('dash.leaderboard')}</Chip>
          <div className="flex flex-wrap gap-1.5 mt-2 mb-3">
            {['All', 'Pothole', 'Garbage', 'Water'].map(f => (
              <Chip
                key={f}
                tone={filter === f ? 'coffee' : 'paper'}
                onClick={() => setFilter(f)}
                className="cursor-pointer"
              >{f}</Chip>
            ))}
          </div>
          <ul className="space-y-1">
            {wards.map((w, i) => (
              <li key={w.id}>
                <Link to={`/officer/${w.id}`} className="grid grid-cols-[24px_1fr_60px_44px] gap-2 items-center px-2 py-1.5 rounded hover:bg-mist text-[12px] font-sans">
                  <span className="font-mono text-coffee/55">{i + 1}</span>
                  <span className="font-semibold text-coffee">{w.name}</span>
                  <div className="h-1.5 bg-mist border border-line relative overflow-hidden">
                    <div
                      className={[
                        'absolute inset-y-0 left-0',
                        w.tone === 'olive' ? 'bg-olive' : w.tone === 'beige' ? 'bg-beige' : 'bg-coffee'
                      ].join(' ')}
                      style={{ width: `${Math.round((w.resolution || 0) * 100)}%` }}
                    />
                  </div>
                  <span className={`font-mono text-right ${w.tone === 'olive' ? 'text-olive font-semibold' : w.tone === 'coffee' ? 'text-coffee font-semibold' : 'text-coffee/65'}`}>
                    {Math.round((w.resolution || 0) * 100)}%
                  </span>
                </Link>
              </li>
            ))}
          </ul>

          <div className="font-hand text-[12px] text-coffee/65 mt-3 text-right">↓ click any row → officer scorecard</div>

          <Chip className="mt-6">{T('dash.latest')}</Chip>
          <ul className="mt-2 space-y-1.5">
            {recent.map(c => (
              <li key={c.id} className="grid grid-cols-[80px_1fr_64px] text-[11px] font-sans gap-2 items-center border-b border-dashed border-beige pb-1">
                <span className="font-mono text-olive">{c.id}</span>
                <span className="text-coffee">{c.issue} · {c.wardName}</span>
                <span className={[
                  'text-right text-[10px] font-mono',
                  c.status === 'resolved' ? 'text-olive' : c.status === 'escalated' ? 'text-rust' : 'text-coffee/60'
                ].join(' ')}>{c.status}</span>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}

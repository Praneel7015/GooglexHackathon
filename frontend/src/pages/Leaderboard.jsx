import { useState, useMemo, useEffect } from 'react';
import { Chip } from '../components/ui';
import { Link } from 'react-router-dom';
import { WARDS } from '../lib/seed';
import { api } from '../lib/api';
import { useT } from '../lib/i18n';

export default function Leaderboard() {
  const T = useT();
  const [filter, setFilter] = useState('All');
  const [sortDir, setSortDir] = useState('desc');
  const [liveWards, setLiveWards] = useState(null);

  useEffect(() => {
    api.getDashboardStats().then(data => {
      if (data?.wards?.length) {
        setLiveWards(data.wards.map(w => ({
          id: w.ward_number,
          name: w.ward_name,
          councillor: '',
          resolution: w.resolution_rate,
          open: w.open,
          avg: w.avg_response_days ?? 0,
          tone: w.resolution_rate >= 0.65 ? 'olive' : w.resolution_rate >= 0.4 ? 'beige' : 'coffee',
        })));
      }
    });
  }, []);

  const sourceWards = liveWards || WARDS;

  const ranked = useMemo(() =>
    [...sourceWards].sort((a, b) => sortDir === 'desc' ? b.resolution - a.resolution : a.resolution - b.resolution),
    [sortDir, sourceWards]
  );

  return (
    <section className="max-w-[1400px] mx-auto px-4 md:px-8 py-8 md:py-12">
      <Chip>{T('lb.chip')}</Chip>
      <h1 className="font-hand text-coffee text-4xl md:text-5xl mt-1 leading-[.95] tracking-tight">
        {T('lb.heading')}
      </h1>
      <p className="font-kn text-coffee/70 mt-2">{T('lb.subtitle')}</p>

      <div className="flex flex-wrap gap-2 items-center mt-6">
        {['All', 'Pothole', 'Garbage', 'Water', 'Streetlight'].map(f => (
          <Chip key={f} tone={filter === f ? 'coffee' : 'paper'} onClick={() => setFilter(f)} className="cursor-pointer">{f}</Chip>
        ))}
        <span className="ml-auto font-mono text-[11px] text-coffee/65 cursor-pointer" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
          {T('lb.sort')} {sortDir === 'desc' ? '↓' : '↑'}
        </span>
      </div>

      <div className="border-[1.5px] border-line rounded-md overflow-hidden mt-3 bg-paper">
        <div className="grid grid-cols-[32px_1fr_72px] md:grid-cols-[40px_1fr_1.1fr_70px_1.2fr_70px] gap-x-3 md:gap-x-4 bg-beige px-3 md:px-4 py-2 border-b border-line font-sans text-[10px] uppercase tracking-wider font-semibold">
          <div>#</div>
          <div>{T('lb.col.ward')}</div>
          <div className="hidden md:block">{T('lb.col.councillor')}</div>
          <div className="hidden md:block text-right">{T('lb.col.open')}</div>
          <div>{T('lb.col.resolution')}</div>
          <div className="hidden md:block text-right">{T('lb.col.avgtime')}</div>
        </div>
        {ranked.map((w, i) => (
          <Link
            key={w.id}
            to={`/officer/${w.id}`}
            className="grid grid-cols-[32px_1fr_72px] md:grid-cols-[40px_1fr_1.1fr_70px_1.2fr_70px] gap-x-3 md:gap-x-4 px-3 md:px-4 py-2.5 border-b border-dashed border-beige bg-paper items-center text-[12px] font-sans hover:bg-mist transition-colors"
          >
            <span className="font-mono text-coffee/55">{i + 1}</span>
            <span className="font-semibold text-coffee truncate">{w.name}</span>
            <span className="hidden md:block text-coffee/75 truncate">{w.councillor || ''}</span>
            <span className="hidden md:block font-mono text-right tabular-nums">{w.open}</span>
            <span className="flex items-center gap-1.5">
              <div className="flex-1 h-1.5 bg-mist border border-line relative overflow-hidden hidden md:block">
                <div
                  className={w.tone === 'olive' ? 'absolute inset-y-0 left-0 bg-olive' : w.tone === 'beige' ? 'absolute inset-y-0 left-0 bg-beige' : 'absolute inset-y-0 left-0 bg-coffee'}
                  style={{ width: `${Math.round((w.resolution || 0) * 100)}%` }}
                />
              </div>
              <span className={`font-mono text-[11px] font-semibold ${w.tone === 'olive' ? 'text-olive' : w.tone === 'coffee' ? 'text-coffee' : 'text-coffee/65'}`}>
                {Math.round((w.resolution || 0) * 100)}%
              </span>
            </span>
            <span className="hidden md:block font-mono text-right text-coffee/65">{w.avg}d</span>
          </Link>
        ))}
      </div>

      <div className="font-hand text-[13px] text-coffee/70 mt-3 text-right">{T('lb.footer')}</div>
    </section>
  );
}

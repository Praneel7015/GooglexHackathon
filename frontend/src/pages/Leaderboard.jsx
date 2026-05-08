import { useState, useMemo } from 'react';
import { Chip } from '../components/ui';
import { Link } from 'react-router-dom';
import { WARDS } from '../lib/seed';

export default function Leaderboard() {
  const [filter, setFilter] = useState('All');
  const [sortDir, setSortDir] = useState('desc');
  const ranked = useMemo(() =>
    [...WARDS].sort((a, b) => sortDir === 'desc' ? b.resolution - a.resolution : a.resolution - b.resolution),
    [sortDir]
  );
  return (
    <section className="max-w-[1400px] mx-auto px-4 md:px-8 py-8 md:py-12">
      <Chip>198 wards · ranked by resolution rate</Chip>
      <h1 className="font-hand text-coffee text-4xl md:text-5xl mt-1 leading-[.95] tracking-tight">
        How is your ward<br/>actually performing?
      </h1>
      <p className="font-kn text-coffee/70 mt-2">ನಿಮ್ಮ ವಾರ್ಡ್ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ?</p>

      <div className="flex flex-wrap gap-2 items-center mt-6">
        {['All', 'Pothole', 'Garbage', 'Water', 'Streetlight'].map(f => (
          <Chip key={f} tone={filter === f ? 'coffee' : 'paper'} onClick={() => setFilter(f)} className="cursor-pointer">{f}</Chip>
        ))}
        <span className="ml-auto font-mono text-[11px] text-coffee/65 cursor-pointer" onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')}>
          SORT · resolution rate {sortDir === 'desc' ? '↓' : '↑'}
        </span>
      </div>

      {/* table */}
      <div className="border-[1.5px] border-line rounded-md overflow-hidden mt-3 bg-paper">
        <div className="grid grid-cols-[40px_1fr_1.1fr_70px_1.2fr_70px] bg-beige px-4 py-2 border-b border-line font-sans text-[10px] uppercase tracking-wider font-semibold">
          <div>#</div><div>Ward</div><div className="hidden md:block">Councillor</div><div className="text-right">Open</div><div>Resolution</div><div className="text-right">Avg time</div>
        </div>
        {ranked.map((w, i) => (
          <Link
            key={w.id}
            to={`/officer/${w.id}`}
            className="grid grid-cols-[40px_1fr_1.1fr_70px_1.2fr_70px] px-4 py-2.5 border-b border-dashed border-beige bg-paper items-center text-[12px] font-sans hover:bg-mist transition-colors"
          >
            <span className="font-mono text-coffee/55">{i + 1}</span>
            <span className="font-semibold text-coffee">{w.name}</span>
            <span className="hidden md:block text-coffee/75">{w.councillor}</span>
            <span className="font-mono text-right tabular-nums">{w.open}</span>
            <span className="flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-mist border border-line relative overflow-hidden">
                <div
                  className={w.tone === 'olive' ? 'absolute inset-y-0 left-0 bg-olive' : w.tone === 'beige' ? 'absolute inset-y-0 left-0 bg-beige' : 'absolute inset-y-0 left-0 bg-coffee'}
                  style={{ width: `${Math.round(w.resolution * 100)}%` }}
                />
              </div>
              <span className={`font-mono text-[11px] w-9 text-right font-semibold ${w.tone === 'olive' ? 'text-olive' : w.tone === 'coffee' ? 'text-coffee' : 'text-coffee/65'}`}>
                {Math.round(w.resolution * 100)}%
              </span>
            </span>
            <span className="font-mono text-right text-coffee/65">{w.avg}d</span>
          </Link>
        ))}
      </div>

      <div className="font-hand text-[13px] text-coffee/70 mt-3 text-right">↓ click any row → officer scorecard</div>
    </section>
  );
}

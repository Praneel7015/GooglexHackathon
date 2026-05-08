import { Link } from 'react-router-dom';
import { Button, Card, Chip } from '../components/ui';
import { aggregateStats } from '../lib/seed';
import { useT } from '../lib/i18n';

export default function Landing() {
  const T = useT();
  const stats = aggregateStats();

  const HOW = [
    ['01', T('how.01.title'), T('how.01.body')],
    ['02', T('how.02.title'), T('how.02.body')],
    ['03', T('how.03.title'), T('how.03.body')],
    ['04', T('how.04.title'), T('how.04.body')],
  ];

  const DIFF = [
    [T('diff.01.title'), T('diff.01.body')],
    [T('diff.02.title'), T('diff.02.body')],
    [T('diff.03.title'), T('diff.03.body')],
    [T('diff.04.title'), T('diff.04.body')],
  ];

  return (
    <div>
      <section className="bg-mist border-b border-line">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-10 md:py-20 grid md:grid-cols-[1.2fr_1fr] gap-8 md:gap-12 items-center">
          <div>
            <Chip tone="paper" className="mb-3">{T('landing.chip')}</Chip>
            <h1 className="font-hand font-bold text-coffee leading-[.95] tracking-tight text-5xl md:text-7xl">
              The city,<br/>
              <span className="text-olive">filing back.</span>
            </h1>
            <p className="font-kn text-coffee/70 mt-4 text-base md:text-lg">{T('app.tagline')}</p>
            <p className="font-sans text-coffee mt-5 max-w-xl text-[14.5px] md:text-base leading-relaxed">{T('landing.body')}</p>
            <div className="flex flex-wrap gap-3 items-center mt-7">
              <Button as={Link} to="/install" variant="primary" size="lg">{T('cta.install')} →</Button>
              <Button as={Link} to="/dashboard" variant="secondary" size="lg">{T('cta.dashboard')}</Button>
              <span className="font-sans text-[12px] text-coffee/60 ml-1">{T('landing.scanqr')}</span>
            </div>
            <div className="border-t border-dashed border-beige mt-8 pt-4 flex gap-6 md:gap-10 font-sans text-[12px] text-coffee/65">
              {[
                [stats.open.toLocaleString(), T('stat.open')],
                [stats.resolved.toLocaleString(), T('stat.resolved')],
                [stats.wardsReporting, T('stat.wards')],
                ['30+', T('stat.agencies')]
              ].map(([k, v]) => (
                <div key={v}>
                  <div className="font-hand text-[22px] text-coffee font-bold leading-none">{k}</div>
                  {v}
                </div>
              ))}
            </div>
          </div>

          <div className="relative h-[360px] md:h-[440px] hidden md:flex items-center justify-center select-none">
            <div className="phone-frame w-[200px] h-[400px] -rotate-[4deg] relative overflow-hidden">
              <div className="absolute top-3 left-1/2 -translate-x-1/2 w-16 h-4 bg-ink rounded-full z-10" />
              <div className="absolute inset-[6px] top-[6px] rounded-[30px] bg-[#1a1a1a] overflow-hidden flex flex-col">
                <div className="flex justify-between items-center px-5 pt-10 pb-1">
                  <span className="text-white/60 text-[8px] font-mono">9:41</span>
                  <span className="text-white/60 text-[8px] font-mono">●●●</span>
                </div>
                <div className="flex-1 relative mx-3 mb-3 rounded-2xl overflow-hidden bg-[#111]">
                  <div className="absolute inset-0" style={{ background: 'linear-gradient(160deg, #2a3a2a 0%, #1a2a1a 40%, #0f1a0f 100%)' }} />
                  <div className="absolute inset-5">
                    <div className="absolute top-0 left-0 w-5 h-5 border-t-2 border-l-2 border-white/70 rounded-tl" />
                    <div className="absolute top-0 right-0 w-5 h-5 border-t-2 border-r-2 border-white/70 rounded-tr" />
                    <div className="absolute bottom-0 left-0 w-5 h-5 border-b-2 border-l-2 border-white/70 rounded-bl" />
                    <div className="absolute bottom-0 right-0 w-5 h-5 border-b-2 border-r-2 border-white/70 rounded-br" />
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full border-2 border-white/50" />
                  </div>
                  <div className="absolute top-3 left-3 bg-olive/90 text-white text-[8px] font-sans font-semibold px-2 py-0.5 rounded-full">AI · Auto-routing</div>
                  <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur-sm text-white text-[8px] font-sans px-2.5 py-1 rounded-full whitespace-nowrap">Pothole detected · Ward 95</div>
                </div>
                <div className="flex justify-center pb-4">
                  <div className="w-12 h-12 rounded-full bg-white/10 border-2 border-white/30 flex items-center justify-center">
                    <div className="w-9 h-9 rounded-full bg-white/90" />
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute top-6 right-2 rotate-[6deg]">
              <Card tone="coffee" padding="px-3 py-2" className="font-sans text-[11px] font-semibold">
                <div className="text-[9px] uppercase tracking-wider opacity-70 mb-0.5">Ward 95</div>
                Filed in 1.4s
              </Card>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-paper">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <Chip tone="paper" className="mb-2">{T('landing.how.chip')}</Chip>
          <h2 className="font-hand text-3xl md:text-4xl text-coffee mb-6">{T('landing.how.head')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {HOW.map(([n, h, p]) => (
              <Card key={n} tone="paper" padding="p-4">
                <div className="font-mono text-[10px] tracking-wider text-olive mb-1.5">{n}</div>
                <div className="font-hand text-xl text-coffee leading-tight font-bold mb-1.5">{h}</div>
                <div className="font-sans text-[12px] text-coffee/70 leading-snug">{p}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-coffee text-mist">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <Chip tone="ghost" className="mb-2 border-mist/40 text-mist">{T('landing.moat.chip')}</Chip>
          <h2 className="font-hand text-3xl md:text-4xl mb-6">{T('landing.moat.head')}</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {DIFF.map(([t1, p]) => (
              <div key={t1} className="border-l-2 border-olive pl-4">
                <div className="font-hand font-bold text-2xl">{t1}</div>
                <div className="font-sans text-[13px] text-mist/80 mt-1.5 leading-relaxed">{p}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

import { Link } from 'react-router-dom';
import { Button, Card, Chip } from '../components/ui';
import { useApp } from '../lib/store';
import { aggregateStats } from '../lib/seed';
import { t } from '../lib/i18n';

export default function Landing() {
  const lang = useApp(s => s.language);
  const stats = aggregateStats();
  return (
    <div>
      {/* HERO */}
      <section className="bg-mist border-b border-line">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-10 md:py-20 grid md:grid-cols-[1.2fr_1fr] gap-8 md:gap-12 items-center">
          <div>
            <Chip tone="paper" className="mb-3">Bengaluru · 198 wards · live</Chip>
            <h1 className="font-hand font-bold text-coffee leading-[.95] tracking-tight text-5xl md:text-7xl">
              The city,<br/>
              <span className="text-olive">filing back.</span>
            </h1>
            <p className="font-kn text-coffee/70 mt-4 text-base md:text-lg">{t(lang, 'app.tagline')}</p>
            <p className="font-sans text-coffee mt-5 max-w-xl text-[14.5px] md:text-base leading-relaxed">
              Photograph any civic issue — pothole, garbage, leak, dead light. Our agents
              file it across 30+ agencies, bundle it with your neighbours' reports,
              and track it on a public dashboard until it's fixed.
            </p>
            <div className="flex flex-wrap gap-3 items-center mt-7">
              <Button as={Link} to="/install" variant="primary" size="lg">{t(lang, 'cta.install')} →</Button>
              <Button as={Link} to="/dashboard" variant="secondary" size="lg">{t(lang, 'cta.dashboard')}</Button>
              <span className="font-sans text-[12px] text-coffee/60 ml-1">↳ scan QR · install on phone</span>
            </div>

            {/* social proof strip */}
            <div className="border-t border-dashed border-beige mt-8 pt-4 flex gap-6 md:gap-10 font-sans text-[12px] text-coffee/65">
              {[
                [stats.open.toLocaleString(), 'open'],
                [stats.resolved.toLocaleString(), 'resolved'],
                [stats.wardsReporting, 'wards'],
                ['30+', 'agencies routed']
              ].map(([k, v]) => (
                <div key={v}>
                  <div className="font-hand text-[22px] text-coffee font-bold leading-none">{k}</div>
                  {v}
                </div>
              ))}
            </div>
          </div>

          {/* phone mockup */}
          <div className="relative h-[360px] md:h-[440px] hidden md:flex items-center justify-center">
            <div className="phone-frame w-[200px] h-[400px] -rotate-[4deg] relative">
              <div className="absolute top-1.5 left-1/2 -translate-x-1/2 w-16 h-3.5 bg-ink rounded-full" />
              <div className="img-x absolute inset-x-3 top-7 bottom-14" />
              <div className="absolute bottom-5 left-0 right-0 flex justify-center">
                <div className="w-12 h-12 rounded-full bg-olive border-[3px] border-paper" style={{ boxShadow: '0 0 0 1.5px #2a221b' }} />
              </div>
              <div className="absolute top-12 left-0 right-0 text-center font-hand text-mist/90 text-[13px]" style={{ textShadow: '0 1px 2px rgba(0,0,0,.5)' }}>viewfinder</div>
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

      {/* HOW IT WORKS */}
      <section className="bg-paper">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <Chip tone="paper" className="mb-2">How it works</Chip>
          <h2 className="font-hand text-3xl md:text-4xl text-coffee mb-6">From photo to fixed.</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              ['01', 'Capture',  'Photo + voice. Auto-located. Kannada or English.'],
              ['02', 'Bundle',   '37 nearby reports merge into one signal.'],
              ['03', 'Route',    '30+ agencies. Twitter, email, BBMP portal.'],
              ['04', 'Track',    '30-day escalation ladder. Public.']
            ].map(([n, h, p]) => (
              <Card key={n} tone="paper" padding="p-4">
                <div className="font-mono text-[10px] tracking-wider text-olive mb-1.5">{n}</div>
                <div className="font-hand text-xl text-coffee leading-tight font-bold mb-1.5">{h}</div>
                <div className="font-sans text-[12px] text-coffee/70 leading-snug">{p}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* DIFFERENTIATORS */}
      <section className="bg-coffee text-mist">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <Chip tone="ghost" className="mb-2 border-mist/40 text-mist">The moat</Chip>
          <h2 className="font-hand text-3xl md:text-4xl mb-6">Why one voice now matters.</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              ['Crowd Validation', 'One pothole report gets ignored. 47 bundled reports get fixed. AI does political organising automatically.'],
              ['Escalation Ladder', 'Day 7 councillor tag → Day 14 RTI → Day 21 MLA + media → Day 30 PIL.'],
              ['Public Dashboard',  'Live ward-level civic-health map. Officials change behaviour when measured.'],
              ['Multi-Agency Routing', '30+ agencies pre-mapped. Most citizens file to wrong place; we don\'t.']
            ].map(([t1, p]) => (
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

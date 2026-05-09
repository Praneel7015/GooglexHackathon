import { useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Link, useLocation } from 'react-router-dom';
import { Button, Card, Chip } from '../components/ui';
import { aggregateStats } from '../lib/seed';
import { useT } from '../lib/i18n';
import { usePWAInstall } from '../hooks/usePWAInstall';

const LIVE_URL = 'https://namma-city-1c3ca.web.app/';

export default function Landing() {
  const T = useT();
  const stats = aggregateStats();
  const location = useLocation();
  const { installPrompt, triggerInstall, isInstalled } = usePWAInstall();

  // Auto-scroll to #install when the page loads with that hash
  // e.g. navigating to /#install or clicking the hero CTA
  useEffect(() => {
    if (location.hash === '#install') {
      setTimeout(() => {
        document.getElementById('install')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [location.hash]);

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
              The city,<br />
              <span className="text-olive">filing back.</span>
            </h1>
            <p className="font-kn text-coffee/70 mt-4 text-base md:text-lg">{T('app.tagline')}</p>
            <p className="font-sans text-coffee mt-5 max-w-xl text-[14.5px] md:text-base leading-relaxed">{T('landing.body')}</p>
            <div className="flex flex-wrap gap-3 items-center mt-7">
              <Button
                as="button"
                variant="primary"
                size="lg"
                onClick={() => document.getElementById('install')?.scrollIntoView({ behavior: 'smooth' })}
              >{T('cta.install')} →</Button>
              <Button as={Link} to="/onboard" variant="secondary" size="lg">Learn more</Button>
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

      {/* ── 10 Agents ── */}
      <section className="bg-mist border-t border-line">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <Chip tone="paper" className="mb-2">10-agent pipeline · Google ADK + Gemini 2.5 Pro</Chip>
          <h2 className="font-hand text-3xl md:text-4xl text-coffee mb-2">One photo. Ten agents. Zero manual steps.</h2>
          <p className="font-sans text-[13px] text-coffee/65 mb-7 max-w-2xl">Each agent runs in parallel inside Google ADK, orchestrated by Gemini 2.5 Pro multimodal reasoning. Photo + voice in Kannada, Hindi, English, or Tamil — all handled.</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
            {[
              ['01', 'Reporter', 'Classifies issue across ~30 types. Assigns severity 1–5. Detects spam & duplicates via Gemini vision.'],
              ['02', 'Geo', 'Extracts GPS from EXIF or Gemini landmark detection. Maps to BBMP ward, MLA constituency, police jurisdiction.'],
              ['03', 'Routing', '30+ agencies pre-mapped. BBMP, BESCOM, BWSSB, BMTC, Traffic Police, KSPCB, BMRCL, RERA and more.'],
              ['04', 'Crowd Validation', 'Clusters nearby reports (200–500m radius + semantic similarity). 3+ matches → auto-bundle as neighbourhood issue.'],
              ['05', 'Drafting', 'Generates formal complaint letter in English + Kannada, tweet ≤280 chars, email to ward officer, RTI template.'],
              ['06', 'Submission', 'Twitter/X API, Gmail SMTP, BBMP Sahaaya pre-fill, WhatsApp. If one channel fails, others succeed.'],
              ['07', 'Escalation', 'Day 7 councillor tag → Day 14 RTI → Day 21 MLA + media → Day 30 PIL. AI as enforcer, not messenger.'],
              ['08', 'Prediction', 'Ward-level resolution likelihood from historical data. "73% chance in 21 days based on Ward 95 history."'],
              ['09', 'Dashboard', 'Renders public accountability map. Officials change behaviour when measured. The legacy layer.'],
              ['10', 'Engagement', 'Civic Karma points. Badges: Pothole Hunter, Garbage Crusader. Ward leaderboards. Virality built in.'],
            ].map(([n, title, body]) => (
              <div key={n} className="bg-paper border border-line rounded p-3">
                <div className="font-mono text-[9px] tracking-wider text-olive mb-1">{n}</div>
                <div className="font-hand text-[15px] font-bold text-coffee leading-tight mb-1">{title}</div>
                <div className="font-sans text-[11px] text-coffee/65 leading-snug">{body}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Escalation Ladder ── */}
      <section className="bg-coffee text-mist border-t border-line/20">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16 grid md:grid-cols-[1fr_1.4fr] gap-10 items-start">
          <div>
            <Chip tone="ghost" className="mb-2 border-mist/40 text-mist">Escalation ladder · automatic</Chip>
            <h2 className="font-hand text-3xl md:text-4xl mb-3">AI as enforcer,<br />not messenger.</h2>
            <p className="font-sans text-[13px] text-mist/75 leading-relaxed max-w-sm">If the agency goes silent, NammaCity doesn't. The escalation clock starts the moment you file — no manual follow-up needed.</p>
          </div>
          <div className="space-y-0">
            {[
              ['Day 0', 'Multi-channel submission', 'Twitter/X · Gmail · BBMP Sahaaya pre-fill · Dashboard', true],
              ['Day 7', 'Councillor tagged by name', 'Auto-tweet naming ward councillor. First political pressure.', false],
              ['Day 14', 'RTI application filed', 'AI-drafted. Legally binding — agency must respond in 30 days.', false],
              ['Day 21', 'MLA + media escalation', '@CMofKarnataka · @TimesofIndia_blr · @DeccanHerald', false],
              ['Day 30', 'PIL outline + NGO notification', 'Draft prepared. Partner NGOs (Janaagraha, Citizen Matters) alerted.', false],
            ].map(([day, title, sub, first]) => (
              <div key={day} className={`flex gap-4 items-start py-4 ${!first ? 'border-t border-mist/10' : ''}`}>
                <div className="font-mono text-[10px] text-olive w-14 shrink-0 pt-0.5">{day}</div>
                <div>
                  <div className="font-sans font-semibold text-[13px] text-mist">{title}</div>
                  <div className="font-sans text-[11px] text-mist/60 mt-0.5">{sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Agencies + Stack ── */}
      <section className="bg-paper border-t border-line">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16">
          <div className="grid md:grid-cols-2 gap-12">
            {/* Agencies */}
            <div>
              <Chip tone="paper" className="mb-2">30+ agencies · pre-mapped</Chip>
              <h2 className="font-hand text-2xl md:text-3xl text-coffee mb-5">We know who handles what.</h2>
              <div className="space-y-2">
                {[
                  ['BBMP', 'Roads · Garbage · Parks · Drainage · Streetlights · Building violations'],
                  ['BESCOM', 'Electricity · Broken poles · Dangerous wires · Outages'],
                  ['BWSSB', 'Water leaks · Sewage overflow · Broken pipes'],
                  ['BMTC', 'Bus stops · Missed buses · Conductor issues'],
                  ['Traffic Police', 'Signals · Traffic violations · Illegal parking'],
                  ['KSPCB', 'Air, water & noise pollution'],
                  ['BMRCL', 'Metro station issues'],
                  ['RERA Karnataka', 'Builder fraud · Real-estate disputes'],
                  ['Karnataka Forest', 'Tree fall · Illegal tree cutting'],
                ].map(([agency, handles]) => (
                  <div key={agency} className="flex gap-3 text-[12px] font-sans border-b border-dashed border-beige pb-2">
                    <span className="font-semibold text-coffee w-32 shrink-0">{agency}</span>
                    <span className="text-coffee/60">{handles}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Stack */}
            <div>
              <Chip tone="paper" className="mb-2">Open source · built in 24 hours</Chip>
              <h2 className="font-hand text-2xl md:text-3xl text-coffee mb-5">The stack behind the city.</h2>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ['Google ADK', 'Multi-agent orchestration'],
                  ['Gemini 2.5 Flash', 'Multimodal · photo + voice + text'],
                  ['Gemini Live API', 'Real-time multilingual voice'],
                  ['FastAPI (Python)', 'Async backend + WebSocket'],
                  ['PostgreSQL+PostGIS', 'Geo radius queries'],
                  ['ChromaDB', 'Semantic similarity clustering'],
                  ['Leaflet + OSM', 'Free maps · no API key'],
                  ['React + Vite', 'PWA · installable on home screen'],
                  ['Twitter API v2', 'Publicly verifiable submissions'],
                  ['Gmail API', 'Email to ward officers'],
                ].map(([tech, role]) => (
                  <div key={tech} className="bg-mist border border-line rounded p-2.5">
                    <div className="font-mono text-[10px] font-semibold text-coffee">{tech}</div>
                    <div className="font-sans text-[10px] text-coffee/55 mt-0.5">{role}</div>
                  </div>
                ))}
              </div>
              <a
                href="https://github.com/Praneel7015/GooglexHackathon"
                target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-2 mt-5 font-sans text-[12px] font-semibold text-olive underline"
              >↗ View source on GitHub</a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Install section (merged from /install) ── */}
      <section id="install" className="bg-paper border-t border-line scroll-mt-16">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-12 md:py-16 grid md:grid-cols-2 gap-10 items-center">
          <div>
            <Chip>{T('install.chip')}</Chip>
            <h2 className="font-hand font-bold text-coffee text-4xl md:text-6xl leading-[.95] mt-2 tracking-tight">
              {T('install.heading')}
            </h2>
            <p className="font-kn text-coffee/70 text-base mt-3">{T('install.subtitle')}</p>
            <p className="font-sans text-[14px] text-coffee mt-5 max-w-md leading-relaxed">
              {T('install.body')}
            </p>
            <ol className="mt-6 space-y-3">
              {[
                [T('install.step1.h'), T('install.step1.s')],
                [T('install.step2.h'), T('install.step2.s')],
                [T('install.step3.h'), T('install.step3.s')],
              ].map(([h, s], i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="font-mono text-[12px] text-olive font-semibold pt-0.5">0{i + 1}</span>
                  <div>
                    <div className="font-sans font-semibold text-coffee text-[13.5px]">{h}</div>
                    <div className="font-sans text-[12px] text-coffee/65">{s}</div>
                  </div>
                </li>
              ))}
            </ol>
            <div className="mt-7 flex flex-wrap gap-3 items-center">
              {isInstalled ? (
                <div className="inline-flex items-center gap-2 font-sans text-[13px] text-olive font-semibold">
                  <span>✓</span> NammaCity is installed!
                </div>
              ) : installPrompt ? (
                <Button
                  as="button"
                  variant="primary"
                  size="md"
                  onClick={triggerInstall}
                >
                  ⬇ Install NammaCity
                </Button>
              ) : (
                <Button as={Link} to="/onboard" variant="secondary" size="md">{T('install.cta')}</Button>
              )}
              <span className="font-sans text-[11px] text-coffee/55">{T('install.visit')} <span className="font-mono text-olive">nammacity.org</span></span>
            </div>
          </div>

          {/* PWA Install Card */}
          <div className="flex flex-col items-center w-full max-w-sm">
            <Card padding="p-6" className="bg-paper shadow-deep w-full">
              {/* App identity */}
              <div className="flex items-center gap-3 mb-5">
                <img src="/favicon-96x96.png" alt="NammaCity icon" className="w-12 h-12 rounded-xl" />
                <div>
                  <div className="font-hand text-coffee text-lg font-bold leading-tight">NammaCity</div>
                  <div className="font-mono text-[9px] tracking-wider text-olive">ನಮ್ಮಸಿಟಿ · Scan to install</div>
                </div>
              </div>

              {/* Real QR Code */}
              <div className="flex justify-center mb-4">
                <a href={LIVE_URL} target="_blank" rel="noreferrer" title="Scan to open NammaCity">
                  <div className="p-3 bg-[#fbf8f1] rounded-xl border border-line inline-block">
                    <QRCodeSVG
                      value={LIVE_URL}
                      size={180}
                      bgColor="#fbf8f1"
                      fgColor="#342a21"
                      level="M"
                      imageSettings={{
                        src: '/favicon-96x96.png',
                        x: undefined,
                        y: undefined,
                        height: 32,
                        width: 32,
                        excavate: true,
                      }}
                    />
                  </div>
                </a>
              </div>

              {/* Live URL chip */}
              <a
                href={LIVE_URL}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 bg-mist border border-line rounded-lg px-3 py-2 mb-4 hover:border-olive transition-colors group"
              >
                <span className="w-2 h-2 rounded-full bg-olive shrink-0 animate-pulse" />
                <span className="font-mono text-[11px] text-coffee/80 truncate flex-1">namma-city-1c3ca.web.app</span>
                <span className="font-sans text-[10px] text-olive font-semibold group-hover:underline shrink-0">↗ Open</span>
              </a>

              {/* Primary install action */}
              {isInstalled ? (
                <div className="w-full flex items-center justify-center gap-2 bg-olive/10 border border-olive/30 rounded-lg px-4 py-3 font-sans text-[13px] text-olive font-semibold">
                  <span>✓</span> Already installed!
                </div>
              ) : installPrompt ? (
                <button
                  onClick={triggerInstall}
                  className="w-full bg-coffee text-mist font-sans font-semibold text-[14px] rounded-lg px-4 py-3 hover:bg-coffee/90 active:scale-[.98] transition-all flex items-center justify-center gap-2"
                >
                  <span>⬇</span> Install App — Free
                </button>
              ) : (
                <a
                  href={LIVE_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full bg-coffee text-mist font-sans font-semibold text-[14px] rounded-lg px-4 py-3 hover:bg-coffee/90 transition-all flex items-center justify-center gap-2"
                >
                  <span>↗</span> Open in browser
                </a>
              )}

              {/* Per-platform mini instructions */}
              <div className="mt-4 space-y-2">
                {[
                  ['Android', 'Tap ⋮ menu → "Add to Home screen"'],
                  ['iOS Safari', 'Tap Share ↑ → "Add to Home Screen"'],
                  ['Desktop', 'Click ⊕ in address bar to install'],
                ].map(([platform, hint]) => (
                  <div key={platform} className="flex gap-2 text-[11px] font-sans">
                    <span className="font-semibold text-coffee w-20 shrink-0">{platform}</span>
                    <span className="text-coffee/55">{hint}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}

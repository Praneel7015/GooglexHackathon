import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Logo, LanguageToggle, Button } from './ui';
import { useState } from 'react';
import { useT } from '../lib/i18n';

const NAV = [
  { to: '/capture',     labelKey: 'nav.file' },
  { to: '/track',       labelKey: 'nav.track' },
  { to: '/dashboard',   labelKey: 'nav.dashboard' },
  { to: '/leaderboard', labelKey: 'nav.wards' },
  { to: '/settings',    labelKey: 'nav.settings' },
];

export default function PublicShell({ floatingHeader = false }) {
  const [open, setOpen] = useState(false);
  const T = useT();
  const loc = useLocation();
  return (
    <div className="min-h-[100dvh] bg-paper text-coffee flex flex-col">
      <header className={['sticky top-0 z-30 border-b border-line bg-paper/95 backdrop-blur', floatingHeader ? '' : ''].join(' ')}>
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-3 flex items-center gap-4 md:gap-8">
          <Link to="/" className="shrink-0"><Logo size={28} /></Link>
          <nav className="hidden md:flex gap-5 font-sans text-[13px] text-coffee/80">
            {NAV.map(n => (
              <NavLink key={n.to} to={n.to} className={({ isActive }) =>
                isActive ? 'text-coffee font-semibold ul-strk' : 'hover:text-coffee'
              }>{T(n.labelKey)}</NavLink>
            ))}
          </nav>
          <div className="flex-1" />
          <LanguageToggle />
          <Button as="button" variant="primary" size="sm" className="hidden md:inline-flex" onClick={() => { window.location.href = '/#install'; }}>{T('nav.openapp')}</Button>
          <button
            onClick={() => setOpen(o => !o)}
            className="md:hidden p-2 rounded-md border border-line bg-paper"
            aria-label="Menu" aria-expanded={open}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#342a21" strokeWidth="1.8" strokeLinecap="round">
              {open ? <path d="M6 6 L18 18 M6 18 L18 6" /> : <path d="M4 7 H20 M4 12 H20 M4 17 H20" />}
            </svg>
          </button>
        </div>
        {open && (
          <div className="md:hidden border-t border-line/30 bg-paper">
            <div className="px-4 py-3 flex flex-col gap-2 font-sans text-sm">
              {NAV.map(n => (
                <Link key={n.to} to={n.to} onClick={() => setOpen(false)} className="py-1.5">{T(n.labelKey)}</Link>
              ))}
              <Button as="button" variant="primary" size="md" full onClick={() => { setOpen(false); window.location.href = '/#install'; }}>{T('nav.openapp')}</Button>
            </div>
          </div>
        )}
      </header>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-coffee text-mist/85">
        <div className="max-w-[1280px] mx-auto px-4 md:px-8 py-6 flex flex-col md:flex-row gap-4 items-start md:items-center font-sans text-[12px]">
          <Logo size={24} dark />
          <span>NammaCity · ನಮ್ಮಸಿಟಿ · An open civic project for Bengaluru</span>
          <span className="md:ml-auto opacity-70">Privacy · <a href="https://github.com/Praneel7015/GooglexHackathon" target="_blank" rel="noreferrer" className="underline hover:opacity-100">Source</a> · Methodology · Contact</span>
        </div>
      </footer>
    </div>
  );
}

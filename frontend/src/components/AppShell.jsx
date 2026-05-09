import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Logo, LanguageToggle } from './ui';
import { useT } from '../lib/i18n';
import { useApp } from '../lib/store';
import { signOut as firebaseSignOut } from '../lib/firebase';

const TABS = [
  { to: '/capture',     labelKey: 'nav.file',      icon: 'camera' },
  { to: '/track',       labelKey: 'nav.track',     icon: 'list' },
  { to: '/dashboard',   labelKey: 'nav.dashboard', icon: 'map' },
  { to: '/leaderboard', labelKey: 'nav.wards',     icon: 'chart' },
  { to: '/settings',    labelKey: 'nav.settings',  icon: 'gear' }
];

const ICONS = {
  camera: <path d="M5 8 H8 L10 6 H14 L16 8 H19 V18 H5 Z M12 11 a3 3 0 1 0 .01 0" />,
  list:   <path d="M5 7 H19 M5 12 H19 M5 17 H19" />,
  map:    <path d="M5 6 L9 5 L15 7 L19 6 V18 L15 19 L9 17 L5 18 Z M9 5 V17 M15 7 V19" />,
  gear:   <path d="M12 8 a4 4 0 1 0 .01 0 M12 4 v2 M12 18 v2 M4 12 h2 M18 12 h2 M6.3 6.3 l1.4 1.4 M16.3 16.3 l1.4 1.4 M6.3 17.7 l1.4 -1.4 M16.3 7.7 l1.4 -1.4" />,
  chart:  <path d="M3 3v18h18 M7 14l4-4 4 4 4-8" strokeLinejoin="round" />,
  user:   <path d="M12 11a4 4 0 100-8 4 4 0 000 8z M4 21a8 8 0 0116 0" />,
  logout: <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4 M16 17l5-5-5-5 M21 12H9" />
};

function Icon({ name, active, color }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none"
      stroke={color || (active ? '#342a21' : '#5a4a38')}
      strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  );
}

export default function AppShell() {
  const T = useT();
  const navigate = useNavigate();
  const { user, signOut } = useApp();

  const handleSignOut = async () => {
    try { await firebaseSignOut(); } catch (_) {}
    signOut();
    navigate('/auth');
  };

  // Initials for avatar
  const initials = (user?.name || '?').split(' ').map(s => s[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div className="min-h-[100dvh] bg-paper text-coffee flex flex-col">
      {/* ── Mobile top bar ── */}
      <header className="md:hidden flex items-center justify-between px-4 pt-safe pb-2 border-b border-line/20">
        <Link to="/"><Logo size={26} withText /></Link>
        <button
          onClick={handleSignOut}
          title="Sign out"
          className="flex items-center gap-1.5 font-sans text-[11px] text-coffee/60 hover:text-rust transition-colors"
        >
          <Icon name="logout" color="currentColor" />
          <span className="sr-only">Sign out</span>
        </button>
      </header>

      <div className="flex-1 flex md:flex-row flex-col">
        {/* ── Desktop sidebar ── */}
        <aside className="hidden md:flex md:flex-col w-48 bg-coffee text-mist border-r border-line p-5 gap-2">
          <Link to="/" className="mb-4"><Logo size={32} dark /></Link>

          {TABS.map(t => (
            <NavLink key={t.to} to={t.to} className={({ isActive }) =>
              ['rounded-md px-3 py-2 font-sans text-sm flex items-center gap-2 transition-colors',
                isActive ? 'bg-mist text-coffee font-semibold' : 'text-mist/85 hover:bg-mist/10'
              ].join(' ')
            }>
              <Icon name={t.icon} active={false} />
              <span>{T(t.labelKey)}</span>
            </NavLink>
          ))}

          {/* ── Sidebar bottom: user + logout ── */}
          <div className="mt-auto pt-4 border-t border-mist/15 flex flex-col gap-2">
            {/* User pill */}
            {user?.name && (
              <div className="flex items-center gap-2 px-1">
                <div className="w-7 h-7 rounded-full bg-olive text-mist flex items-center justify-center font-hand text-[13px] font-bold shrink-0">
                  {initials}
                </div>
                <div className="min-w-0">
                  <div className="font-sans text-[11px] font-semibold text-mist/90 truncate">{user.name}</div>
                  {user.email && (
                    <div className="font-mono text-[9px] text-mist/45 truncate">{user.email}</div>
                  )}
                </div>
              </div>
            )}

            {/* Logout button */}
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 rounded-md px-3 py-2 font-sans text-sm text-mist/60 hover:bg-rust/20 hover:text-rust transition-colors w-full text-left"
            >
              <Icon name="logout" color="currentColor" />
              <span>Sign out</span>
            </button>

            <div className="text-[10px] opacity-35 font-mono px-1">v0.1.0 · open civic</div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 pb-20 md:pb-0">
          <div className="bg-coffee text-mist border-b border-line">
            <div className="px-4 md:px-8 py-3 md:py-4 flex flex-wrap items-center gap-3 md:gap-5">
              <div className="flex-1 min-w-[140px]">
                <div className="font-sans text-[9px] uppercase tracking-[.18em] opacity-70">{T('dash.live')}</div>
                <div className="font-kn text-[11px] opacity-75 mt-0.5">{T('dash.subtitle')}</div>
              </div>
              <div className="font-mono text-[10px] opacity-70 hidden lg:block">{new Date().toUTCString().slice(5, 22)} IST</div>
              <LanguageToggle tone="dark" />
            </div>
          </div>
          <Outlet />
          <footer className="hidden md:block border-t border-line bg-coffee text-mist/85">
            <div className="px-4 md:px-8 py-5 flex flex-col md:flex-row gap-3 items-start md:items-center font-sans text-[11px]">
              <Logo size={22} dark />
              <span className="opacity-80">NammaCity · ನಮ್ಮಸಿಟಿ · An open civic project for Bengaluru</span>
              <span className="md:ml-auto opacity-55">Privacy · <a href="https://github.com/Praneel7015/GooglexHackathon" target="_blank" rel="noreferrer" className="underline hover:opacity-100">Source</a> · Methodology · Contact</span>
            </div>
          </footer>
        </main>
      </div>

      {/* ── Mobile bottom nav ── */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-paper border-t border-line/40 pb-safe">
        <div className="flex">
          {TABS.map(t => (
            <NavLink key={t.to} to={t.to} className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-0.5 py-2 ${isActive ? 'text-coffee' : 'text-coffee/60'}`
            } end>
              {({ isActive }) => (
                <>
                  <Icon name={t.icon} active={isActive} />
                  <span className="text-[10px] font-sans font-medium">{T(t.labelKey)}</span>
                  <span className={`h-0.5 w-5 rounded-full ${isActive ? 'bg-olive' : 'bg-transparent'}`} />
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}

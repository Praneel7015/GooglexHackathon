import { Link, NavLink, Outlet } from 'react-router-dom';
import { Logo, LanguageToggle } from './ui';

// AppShell is the *in-app* shell with bottom nav. Used after onboarding.
const TABS = [
  { to: '/capture',     label: 'File',      icon: 'camera' },
  { to: '/track',       label: 'Track',     icon: 'list' },
  { to: '/dashboard',   label: 'Dashboard', icon: 'map' },
  { to: '/settings',    label: 'Settings',  icon: 'gear' }
];

const ICONS = {
  camera: <path d="M5 8 H8 L10 6 H14 L16 8 H19 V18 H5 Z M12 11 a3 3 0 1 0 .01 0" />,
  list:   <path d="M5 7 H19 M5 12 H19 M5 17 H19" />,
  map:    <path d="M5 6 L9 5 L15 7 L19 6 V18 L15 19 L9 17 L5 18 Z M9 5 V17 M15 7 V19" />,
  gear:   <path d="M12 8 a4 4 0 1 0 .01 0 M12 4 v2 M12 18 v2 M4 12 h2 M18 12 h2 M6.3 6.3 l1.4 1.4 M16.3 16.3 l1.4 1.4 M6.3 17.7 l1.4 -1.4 M16.3 7.7 l1.4 -1.4" />
};

function Icon({ name, active }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke={active ? '#342a21' : '#5a4a38'} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  );
}

export default function AppShell() {
  return (
    <div className="min-h-[100dvh] bg-paper text-coffee flex flex-col">
      {/* top bar (mobile only) */}
      <header className="md:hidden flex items-center px-4 pt-safe pb-2 border-b border-line/20">
        <Link to="/"><Logo size={26} withText /></Link>
      </header>

      {/* desktop sidebar + content */}
      <div className="flex-1 flex md:flex-row flex-col">
        <aside className="hidden md:flex md:flex-col w-56 bg-coffee text-mist border-r border-line p-5 gap-2">
          <Link to="/" className="mb-4"><Logo size={32} dark /></Link>
          {TABS.map(t => (
            <NavLink key={t.to} to={t.to} className={({ isActive }) =>
              [
                'rounded-md px-3 py-2 font-sans text-sm flex items-center gap-2 transition-colors',
                isActive ? 'bg-mist text-coffee font-semibold' : 'text-mist/85 hover:bg-mist/10'
              ].join(' ')
            }>
              <Icon name={t.icon} active={false} />
              <span>{t.label}</span>
            </NavLink>
          ))}
          <div className="mt-auto pt-4 border-t border-mist/15">
            <LanguageToggle tone="dark" />
            <div className="text-[10px] mt-3 opacity-50 font-mono">v0.1.0 · open civic project</div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 pb-20 md:pb-0">
          <Outlet />
        </main>
      </div>

      {/* bottom nav (mobile) */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-paper border-t border-line/40 pb-safe">
        <div className="flex">
          {TABS.map(t => (
            <NavLink key={t.to} to={t.to} className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-0.5 py-2 ${isActive ? 'text-coffee' : 'text-coffee/60'}`
            } end>
              {({ isActive }) => (
                <>
                  <Icon name={t.icon} active={isActive} />
                  <span className="text-[10px] font-sans font-medium">{t.label}</span>
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

import { Routes, Route, Navigate } from 'react-router-dom';
import { useApp } from './lib/store';

import PublicShell from './components/PublicShell';
import AppShell, { isAdmin } from './components/AppShell';

import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Leaderboard from './pages/Leaderboard';
import Officer from './pages/Officer';

import Onboarding from './pages/Onboarding';
import Connect from './pages/Connect';
import Capture from './pages/capture/Capture';
import Voice from './pages/capture/Voice';
import Agents from './pages/capture/Agents';
import Confirm from './pages/capture/Confirm';
import Crowd from './pages/Crowd';
import Track from './pages/Track';
import Settings from './pages/Settings';
import Auth from './pages/Auth';
import Admin from './pages/Admin';

/** Guard: if user is not authenticated (no firebaseUid), redirect to /auth */
function RequireAuth({ children }) {
  const firebaseUid = useApp(s => s.user.firebaseUid);
  if (!firebaseUid) return <Navigate to="/auth" replace />;
  return children;
}

/** Guard: if user is already authenticated, redirect away from /auth */
function GuestOnly({ children }) {
  const firebaseUid = useApp(s => s.user.firebaseUid);
  if (firebaseUid) return <Navigate to="/dashboard" replace />;
  return children;
}

/** Guard: only admin emails can access — others go to /dashboard */
function RequireAdmin({ children }) {
  const email = useApp(s => s.user.email);
  const firebaseUid = useApp(s => s.user.firebaseUid);
  if (!firebaseUid) return <Navigate to="/auth" replace />;
  if (!isAdmin(email)) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      {/* Auth page (public, redirects away if already logged in) */}
      <Route path="/auth" element={<GuestOnly><Auth /></GuestOnly>} />

      {/* Capture flow + connect render their own PhoneFrame, so no shell. */}
      <Route path="/connect"      element={<Connect />} />
      <Route path="/capture"      element={<Capture />} />
      <Route path="/voice"        element={<Voice />} />
      <Route path="/agents"       element={<Agents />} />
      <Route path="/confirm"      element={<Confirm />} />
      <Route path="/crowd"        element={<Crowd />} />

      {/* Public site (with header + footer) */}
      <Route element={<PublicShell />}>
        <Route path="/"             element={<Landing />} />
      </Route>

      {/* App shell with bottom nav + sidebar — all protected */}
      <Route element={<RequireAuth><AppShell /></RequireAuth>}>
        <Route path="/onboard"      element={<Onboarding />} />
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/leaderboard"  element={<Leaderboard />} />
        <Route path="/officer/:id"  element={<Officer />} />
        <Route path="/track"        element={<Track />} />
        <Route path="/track/:id"    element={<Track />} />
        <Route path="/settings"     element={<Settings />} />

        {/* Admin — only for emails listed in VITE_ADMIN_EMAILS */}
        <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

import { Routes, Route, Navigate } from 'react-router-dom';

import PublicShell from './components/PublicShell';
import AppShell from './components/AppShell';

import Landing from './pages/Landing';
import Install from './pages/Install';
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

export default function App() {
  return (
    <Routes>
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
        <Route path="/install"      element={<Install />} />
      </Route>

      {/* App shell with bottom nav + sidebar */}
      <Route element={<AppShell />}>
        <Route path="/onboard"      element={<Onboarding />} />
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/leaderboard"  element={<Leaderboard />} />
        <Route path="/officer/:id"  element={<Officer />} />
        <Route path="/track"        element={<Track />} />
        <Route path="/track/:id"    element={<Track />} />
        <Route path="/settings"     element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

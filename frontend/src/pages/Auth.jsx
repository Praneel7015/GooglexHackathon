import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../lib/store';
import {
  signInWithEmail,
  signUpWithEmail,
  signInWithGoogle,
  resetPassword,
} from '../lib/firebase';
// Logo is not needed directly here

/* ─── tiny helpers ─────────────────────────────────────────────────── */
const InputRow = ({ label, type = 'text', value, onChange, placeholder, autoFocus }) => (
  <div className="flex flex-col gap-1">
    <label className="font-sans text-[11px] uppercase tracking-wider text-coffee/65">{label}</label>
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoFocus={autoFocus}
      className="bg-paper border-[1.5px] border-line rounded-md px-3 py-2.5 font-sans text-[13px] text-coffee placeholder-coffee/35 focus:outline-none focus:border-olive transition-colors"
    />
  </div>
);

const ErrMsg = ({ msg }) =>
  msg ? (
    <div className="bg-rust/10 border border-rust/30 rounded-md px-3 py-2 font-sans text-[12px] text-rust">
      {msg}
    </div>
  ) : null;

const OkMsg = ({ msg }) =>
  msg ? (
    <div className="bg-olive/10 border border-olive/30 rounded-md px-3 py-2 font-sans text-[12px] text-olive-dark">
      {msg}
    </div>
  ) : null;

/* ─── Google icon ───────────────────────────────────────────────────── */
const GoogleIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.61z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

/* ─── Main Component ────────────────────────────────────────────────── */
export default function Auth() {
  const navigate = useNavigate();
  const { setUser, setOnboarded } = useApp();

  const [mode, setMode] = useState('signin'); // 'signin' | 'signup' | 'reset'
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [name, setName]         = useState('');
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState('');
  const [ok, setOk]             = useState('');

  const isOnboarded = useApp(s => s.onboarded);

  const afterAuth = (u, isNewUser = false) => {
    setUser({
      firebaseUid: u.uid,
      name: u.name || u.email?.split('@')[0] || 'Citizen',
      email: u.email,
      id: u.uid?.slice(0, 8),
    });
    // Auto-connect email channel so complaints CC the user
    useApp.getState().setChannel('email', { connected: true, value: u.email });
    setOnboarded(true);
    // New users → onboarding; returning users → dashboard
    navigate(isNewUser ? '/onboard' : '/dashboard');
  };

  const handleEmail = async (e) => {
    e.preventDefault();
    setErr(''); setOk('');
    if (!email || !password) { setErr('Please fill in all fields.'); return; }
    setLoading(true);
    try {
      let u;
      if (mode === 'signup') {
        u = await signUpWithEmail(email, password);
        if (name) setUser({ name });
        afterAuth(u, true);  // new user → onboarding
      } else {
        u = await signInWithEmail(email, password);
        afterAuth(u, false); // returning user → dashboard
      }
    } catch (ex) {
      const map = {
        'auth/email-already-in-use': 'Email already registered. Try signing in.',
        'auth/invalid-email': 'Invalid email address.',
        'auth/wrong-password': 'Incorrect password.',
        'auth/user-not-found': 'No account found with this email.',
        'auth/weak-password': 'Password must be at least 6 characters.',
        'auth/too-many-requests': 'Too many attempts. Please try again later.',
        'auth/invalid-credential': 'Invalid email or password.',
      };
      setErr(map[ex.code] || ex.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setErr(''); setOk('');
    setLoading(true);
    try {
      const u = await signInWithGoogle();
      afterAuth(u, true); // always show onboarding (has skip button)
    } catch (ex) {
      if (ex.code !== 'auth/popup-closed-by-user') {
        setErr(ex.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setErr(''); setOk('');
    if (!email) { setErr('Enter your email to reset the password.'); return; }
    setLoading(true);
    try {
      await resetPassword(email);
      setOk('Reset link sent! Check your inbox.');
    } catch (ex) {
      setErr(ex.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-sand flex items-center justify-center p-4">
      <div className="w-full max-w-sm">

        {/* logo + tagline */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-coffee rounded-2xl w-16 h-16 flex items-center justify-center mb-4 shadow-lg">
            <span className="font-hand text-mist text-3xl font-bold leading-none">N</span>
          </div>
          <h1 className="font-hand text-coffee text-3xl font-bold tracking-tight">NammaCity</h1>
          <p className="font-sans text-[12px] text-coffee/55 mt-1">Bengaluru's civic operating system</p>
        </div>

        {/* card */}
        <div className="box bg-paper p-6 shadow-md">

          {/* tab toggle — only show for signin/signup */}
          {mode !== 'reset' && (
            <div className="flex rounded-md overflow-hidden border-[1.5px] border-line mb-5">
              {(['signin', 'signup']).map(m => (
                <button key={m}
                  onClick={() => { setMode(m); setErr(''); setOk(''); }}
                  className={[
                    'flex-1 py-2 font-sans text-[12px] font-semibold transition-colors',
                    mode === m ? 'bg-coffee text-mist' : 'bg-paper text-coffee/65 hover:bg-mist'
                  ].join(' ')}
                >
                  {m === 'signin' ? 'Sign In' : 'Create Account'}
                </button>
              ))}
            </div>
          )}

          {mode === 'reset' && (
            <div className="mb-4">
              <h2 className="font-hand text-coffee text-xl font-bold">Reset Password</h2>
              <p className="font-sans text-[11px] text-coffee/55 mt-0.5">We'll email you a reset link</p>
            </div>
          )}

          <ErrMsg msg={err} />
          <OkMsg msg={ok} />

          {/* form */}
          <form onSubmit={mode === 'reset' ? handleReset : handleEmail} className="flex flex-col gap-3 mt-3">
            {mode === 'signup' && (
              <InputRow
                label="Your Name"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Arjun Sharma"
                autoFocus
              />
            )}

            <InputRow
              label="Email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoFocus={mode !== 'signup'}
            />

            {mode !== 'reset' && (
              <InputRow
                label="Password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            )}

            <button
              type="submit"
              disabled={loading}
              className="mt-1 w-full py-2.5 bg-olive text-mist font-sans text-[13px] font-semibold rounded-md disabled:opacity-50 hover:bg-olive-dark transition-colors"
            >
              {loading
                ? 'Please wait…'
                : mode === 'reset'
                ? 'Send Reset Link'
                : mode === 'signup'
                ? 'Create Account'
                : 'Sign In'}
            </button>
          </form>

          {/* reset / back links */}
          {mode === 'signin' && (
            <button
              onClick={() => { setMode('reset'); setErr(''); setOk(''); }}
              className="mt-2 w-full font-sans text-[11px] text-coffee/55 hover:text-olive underline text-center"
            >
              Forgot password?
            </button>
          )}
          {mode === 'reset' && (
            <button
              onClick={() => { setMode('signin'); setErr(''); setOk(''); }}
              className="mt-2 w-full font-sans text-[11px] text-coffee/55 hover:text-olive underline text-center"
            >
              ← Back to sign in
            </button>
          )}

          {mode !== 'reset' && (
            <>
              {/* divider */}
              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-line/20" />
                <span className="font-sans text-[10px] text-coffee/45">or</span>
                <div className="flex-1 h-px bg-line/20" />
              </div>

              {/* Google SSO */}
              <button
                onClick={handleGoogle}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2.5 py-2.5 border-[1.5px] border-line rounded-md bg-paper hover:bg-mist transition-colors font-sans text-[12.5px] font-medium text-coffee disabled:opacity-50"
              >
                <GoogleIcon />
                Continue with Google
              </button>
            </>
          )}
        </div>

        <p className="font-sans text-[10.5px] text-coffee/40 text-center mt-5 leading-relaxed">
          By signing in you agree to our{' '}
          <span className="underline cursor-pointer hover:text-olive">Privacy Policy</span>.
          <br />NammaCity is an open civic project for Bengaluru.
        </p>
      </div>
    </div>
  );
}

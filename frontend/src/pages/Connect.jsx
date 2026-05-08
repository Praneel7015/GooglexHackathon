import { useState } from 'react';
import { PhoneFrame, Card, Chip, Button } from '../components/ui';
import { useApp } from '../lib/store';
import { useNavigate } from 'react-router-dom';
import { useT } from '../lib/i18n';

export default function Connect() {
  const T = useT();
  const channels = useApp(s => s.channels);
  const user = useApp(s => s.user);
  const setChannel = useApp(s => s.setChannel);
  const patchCurrent = useApp(s => s.patchCurrent);
  const navigate = useNavigate();

  const [name, setName] = useState(user.name || '');
  const [email, setEmail] = useState(channels.email?.value || '');
  const [editing, setEditing] = useState(!channels.email?.connected);

  const handleSave = () => {
    if (email && email.includes('@')) {
      setChannel('email', { connected: true, value: email });
      // Also update user name in store
      useApp.setState(s => ({ user: { ...s.user, name: name || 'Citizen' } }));
      setEditing(false);
    }
  };

  const handleSkip = () => {
    // Anonymous mode — no CC, no Reply-To
    setChannel('email', { connected: false, value: '' });
    useApp.setState(s => ({ user: { ...s.user, name: '' } }));
    navigate('/capture');
  };

  const emailConnected = channels.email?.connected && channels.email?.value;

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <div className="flex gap-1.5 justify-center mb-3">
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-transparent border border-line" />
        </div>

        <Chip>{T('conn.step')}</Chip>
        <h1 className="font-hand text-coffee text-[22px] leading-tight font-bold tracking-tight mt-1.5">
          Your identity on the complaint
        </h1>
        <p className="font-sans text-[11.5px] text-coffee/75 leading-relaxed mb-4 mt-2">
          Your email will be CC'd on the complaint to BBMP so they can reply directly to you. Your name appears in the formal letter.
        </p>

        <div className="space-y-3 flex-1">
          {/* Name */}
          <div>
            <label className="font-sans text-[10px] uppercase tracking-wider text-coffee/55 mb-1 block">Your Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Ojasvi Poonia"
              className="w-full bg-mist border border-line rounded px-3 py-2 font-sans text-[13px] text-coffee focus:outline-none focus:border-olive"
            />
          </div>

          {/* Email */}
          <div>
            <label className="font-sans text-[10px] uppercase tracking-wider text-coffee/55 mb-1 block">Your Email (for CC + Reply-To)</label>
            {editing ? (
              <div className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="flex-1 bg-mist border border-line rounded px-3 py-2 font-sans text-[13px] text-coffee focus:outline-none focus:border-olive"
                />
                <button
                  onClick={handleSave}
                  disabled={!email || !email.includes('@')}
                  className="px-3 py-2 bg-olive text-mist font-sans text-[11px] font-semibold rounded disabled:opacity-40"
                >Save</button>
              </div>
            ) : (
              <Card tone="mist" padding="px-3 py-2" className="flex items-center gap-2 cursor-pointer border-olive" onClick={() => setEditing(true)}>
                <span className="w-5 h-5 rounded-full bg-olive text-mist flex items-center justify-center text-[10px] font-bold">✓</span>
                <span className="font-mono text-[12px] text-olive flex-1">{channels.email?.value}</span>
                <span className="font-sans text-[10px] text-coffee/55">edit</span>
              </Card>
            )}
          </div>

          {/* How it works */}
          <Card tone="mist" padding="px-3 py-2.5" className="mt-2">
            <div className="font-sans text-[10px] uppercase tracking-wider text-coffee/55 mb-1">How it works</div>
            <div className="font-sans text-[11px] text-coffee/75 leading-relaxed space-y-1">
              <div>• Email goes <b>From:</b> NammaCity → <b>To:</b> BBMP ward officer</div>
              <div>• You're <b>CC'd</b> so you see the complaint</div>
              <div>• <b>Reply-To</b> set to your email so BBMP replies go to you</div>
            </div>
          </Card>
        </div>

        <div className="flex gap-2 mt-3">
          <Button variant="secondary" onClick={handleSkip} className="flex-1">Skip (anonymous)</Button>
          <Button
            variant="primary"
            disabled={!emailConnected}
            onClick={() => navigate('/capture')}
            className="flex-[2]"
          >Continue →</Button>
        </div>
      </div>
    </PhoneFrame>
  );
}

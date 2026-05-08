import { Card, Chip, Toggle, LanguageToggle } from '../components/ui';
import { useApp } from '../lib/store';

const CHANNEL_DEFS = [
  { key: 'email',    label: 'Email',                 sym: '@' },
  { key: 'twitter',  label: 'X / Twitter',           sym: '𝕏' },
  { key: 'whatsapp', label: 'WhatsApp',              sym: 'W' },
  { key: 'phone',    label: 'Phone (SMS fallback)',  sym: '☎' },
  { key: 'aadhaar',  label: 'Aadhaar (optional)',    sym: '⊞', soft: '— add to enable RTI auto-filing' }
];

const PREFS = [
  { key: 'autoBundle',    label: 'Auto-file with neighbours', hint: 'When ≥3 nearby reports' },
  { key: 'autoTweet7d',   label: 'Auto-tweet at 7 days',      hint: 'If no agency response' },
  { key: 'fileAnonymous', label: 'File anonymously by default', hint: 'Hide name on public board' }
];

export default function Settings() {
  const { user, channels, setChannel, preferences, togglePreference } = useApp();
  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <h1 className="font-hand text-coffee text-2xl font-bold tracking-tight">Settings</h1>
      <div className="font-kn text-coffee/65 text-[11px] mb-4">ಸೆಟ್ಟಿಂಗ್‌ಗಳು</div>

      {/* profile */}
      <Card tone="mist" padding="p-3" className="flex gap-2.5 items-center mb-5">
        <div className="w-11 h-11 rounded-full bg-olive text-mist flex items-center justify-center font-hand text-[22px] font-bold border-[1.5px] border-line">
          {user.name.split(' ').map(s => s[0]).join('').slice(0, 2)}
        </div>
        <div className="flex-1">
          <div className="font-sans font-semibold text-coffee text-[13px]">{user.name}</div>
          <div className="font-mono text-[10px] text-olive">citizen-id · {user.id}</div>
          <div className="font-sans text-[10px] text-coffee/65">Ward {user.wardId} · Yelahanka</div>
        </div>
        <button className="font-sans text-[10px] font-semibold text-olive underline">Edit</button>
      </Card>

      {/* channels */}
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">Channels we'll file from</div>
      <Card padding="p-0" className="mb-5">
        {CHANNEL_DEFS.map((c, i) => {
          const conn = channels[c.key];
          const on = !!conn?.connected;
          return (
            <div key={c.key} className={'flex items-center gap-2.5 px-3 py-2.5 ' + (i < CHANNEL_DEFS.length - 1 ? 'border-b border-dotted border-beige' : '')}>
              <div className={'w-6 h-6 rounded-full border-[1.4px] border-line flex items-center justify-center font-sans text-[11px] font-semibold ' + (on ? 'bg-mist' : 'bg-transparent')}>{c.sym}</div>
              <div className="flex-1 min-w-0">
                <div className="font-sans text-[12px] font-semibold text-coffee">{c.label}</div>
                <div className={'font-mono text-[10px] truncate ' + (on ? 'text-coffee/65' : 'text-coffee/45')}>
                  {on ? (conn.value || '—') : (c.soft || 'tap to connect')}
                </div>
              </div>
              {c.key === 'aadhaar' ? (
                <button className="font-sans text-[10px] font-semibold text-olive">+ Add</button>
              ) : (
                <Toggle on={on} onChange={(v) => setChannel(c.key, { connected: v, value: v ? (conn?.value || `connected-${c.key}`) : '' })} ariaLabel={`Toggle ${c.label}`} />
              )}
            </div>
          );
        })}
      </Card>

      {/* preferences */}
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">Filing preferences</div>
      <Card padding="p-0" className="mb-5">
        {PREFS.map((p, i) => (
          <div key={p.key} className={'flex items-center gap-2.5 px-3 py-2.5 ' + (i < PREFS.length - 1 ? 'border-b border-dotted border-beige' : '')}>
            <div className="flex-1">
              <div className="font-sans text-[12px] font-semibold text-coffee">{p.label}</div>
              <div className="font-sans text-[10px] text-coffee/65">{p.hint}</div>
            </div>
            <Toggle on={preferences[p.key]} onChange={() => togglePreference(p.key)} ariaLabel={p.label} />
          </div>
        ))}
      </Card>

      {/* language */}
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">Language</div>
      <div className="mb-5"><LanguageToggle /></div>

      <div className="font-sans text-[10px] text-coffee/55 text-center mb-1.5">v1.0.0 · Made for Bengaluru · open source</div>
      <button className="block w-full font-sans text-[12px] text-olive font-semibold underline">Sign out</button>
    </div>
  );
}

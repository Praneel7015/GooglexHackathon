import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Chip, Toggle, LanguageToggle } from '../components/ui';
import { useApp } from '../lib/store';
import { useT } from '../lib/i18n';
import { signOut as firebaseSignOut } from '../lib/firebase';

const CHANNEL_DEFS = [
  { key: 'email',   label: 'Email',       sym: '@' },
  { key: 'twitter', label: 'X / Twitter', sym: '𝕏' },
];

const PREFS = [
  { key: 'autoBundle',    label: 'Auto-file with neighbours', hint: 'When ≥3 nearby reports' },
  { key: 'autoTweet7d',   label: 'Auto-tweet at 7 days',      hint: 'If no agency response' },
  { key: 'fileAnonymous', label: 'File anonymously by default', hint: 'Hide name on public board' }
];

function ChannelRow({ def, conn, setChannel, isLast }) {
  const on = !!conn?.connected;
  const savedValue = conn?.value || '';
  const [editing, setEditing] = useState(!on);
  const [draft, setDraft] = useState(savedValue);

  const placeholder = def.key === 'email' ? 'your@email.com' : '@handle';
  const inputType  = def.key === 'email' ? 'email' : 'text';

  const isValid = def.key === 'email'
    ? draft.includes('@') && draft.includes('.')
    : draft.trim().length > 0;

  const save = () => {
    if (!isValid) return;
    const val = def.key === 'twitter'
      ? (draft.startsWith('@') ? draft.trim() : '@' + draft.trim())
      : draft.trim();
    setChannel(def.key, { connected: true, value: val });
    setEditing(false);
  };

  const toggle = (v) => {
    if (!v) {
      setChannel(def.key, { connected: false, value: '' });
      setDraft('');
      setEditing(true);
    } else {
      if (savedValue) {
        setChannel(def.key, { connected: true, value: savedValue });
        setEditing(false);
      } else {
        setEditing(true);
      }
    }
  };

  return (
    <div className={'px-3 py-3 ' + (!isLast ? 'border-b border-dotted border-beige' : '')}>
      <div className="flex items-center gap-2.5">
        <div className={'w-6 h-6 rounded-full border-[1.4px] border-line flex items-center justify-center font-sans text-[11px] font-semibold shrink-0 ' + (on ? 'bg-mist' : 'bg-transparent')}>{def.sym}</div>
        <div className="flex-1 min-w-0">
          <div className="font-sans text-[12px] font-semibold text-coffee">{def.label}</div>
          {!editing && on && (
            <div className="font-mono text-[10px] text-coffee/65 truncate">{savedValue}</div>
          )}
          {!on && !editing && (
            <div className="font-mono text-[10px] text-coffee/40">not connected</div>
          )}
        </div>
        <Toggle on={on} onChange={toggle} ariaLabel={`Toggle ${def.label}`} />
      </div>
      {editing && (
        <div className="flex gap-2 mt-2 ml-8">
          <input
            type={inputType}
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') setEditing(false); }}
            autoFocus
            placeholder={placeholder}
            className="flex-1 bg-mist border border-line rounded px-2 py-1 font-sans text-[12px] text-coffee focus:outline-none focus:border-olive"
          />
          <button
            onClick={save}
            disabled={!isValid}
            className="px-2.5 py-1 bg-olive text-mist font-sans text-[11px] font-semibold rounded disabled:opacity-40"
          >Save</button>
          {on && savedValue && (
            <button onClick={() => setEditing(false)} className="font-sans text-[10px] text-coffee/50 underline">Cancel</button>
          )}
        </div>
      )}
      {!editing && on && (
        <button
          onClick={() => { setDraft(savedValue); setEditing(true); }}
          className="ml-8 mt-1 font-sans text-[10px] text-olive underline"
        >edit</button>
      )}
    </div>
  );
}

export default function Settings() {
  const T = useT();
  const { user, channels, setChannel, preferences, togglePreference, signOut } = useApp();
  const navigate = useNavigate();
  const [editingName, setEditingName] = useState(false);
  const [draftName, setDraftName] = useState(user.name || '');

  const handleSignOut = async () => {
    try { await firebaseSignOut(); } catch (_) {}
    signOut();
    navigate('/auth');
  };

  const saveName = () => {
    const trimmed = draftName.trim();
    if (trimmed) {
      useApp.setState(s => ({ user: { ...s.user, name: trimmed } }));
    }
    setEditingName(false);
  };
  return (
    <div className="max-w-md mx-auto p-4 md:p-6">
      <h1 className="font-hand text-coffee text-2xl font-bold tracking-tight">{T('settings.heading')}</h1>
      <div className="font-kn text-coffee/65 text-[11px] mb-4">{T('settings.subtitle')}</div>

      {/* profile */}
      <Card tone="mist" padding="p-3" className="flex gap-2.5 items-center mb-5">
        <div className="w-11 h-11 rounded-full bg-olive text-mist flex items-center justify-center font-hand text-[22px] font-bold border-[1.5px] border-line shrink-0">
          {(draftName || user.name).split(' ').map(s => s[0]).join('').slice(0, 2) || '?'}
        </div>
        <div className="flex-1 min-w-0">
          {editingName ? (
            <div className="flex gap-2 items-center">
              <input
                type="text"
                value={draftName}
                onChange={e => setDraftName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') saveName(); if (e.key === 'Escape') { setDraftName(user.name); setEditingName(false); } }}
                autoFocus
                placeholder="Your name"
                className="flex-1 bg-paper border border-olive rounded px-2 py-1 font-sans text-[13px] text-coffee focus:outline-none"
              />
              <button
                onClick={saveName}
                disabled={!draftName.trim()}
                className="px-2.5 py-1 bg-olive text-mist font-sans text-[11px] font-semibold rounded disabled:opacity-40"
              >Save</button>
            </div>
          ) : (
            <>
              <div className="font-sans font-semibold text-coffee text-[13px]">{user.name}</div>
              <div className="font-mono text-[10px] text-olive">citizen-id · {user.id}</div>
              {user.email && (
                <div className="font-sans text-[10px] text-coffee/65">{user.email}</div>
              )}
              <div className="font-sans text-[10px] text-coffee/65">Ward {user.wardId} · Yelahanka</div>
            </>
          )}
        </div>
        {!editingName && (
          <button
            className="font-sans text-[10px] font-semibold text-olive underline shrink-0"
            onClick={() => { setDraftName(user.name); setEditingName(true); }}
          >Edit</button>
        )}
      </Card>

      {/* channels */}
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">{T('settings.channels')}</div>
      <Card padding="p-0" className="mb-5">
        {CHANNEL_DEFS.map((c, i) => (
          <ChannelRow
            key={c.key}
            def={c}
            conn={channels[c.key]}
            setChannel={setChannel}
            isLast={i === CHANNEL_DEFS.length - 1}
          />
        ))}
      </Card>

      {/* preferences */}
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">{T('settings.prefs')}</div>
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
      <div className="text-[10px] uppercase tracking-wider font-sans text-coffee/55 mb-1.5">{T('settings.language')}</div>
      <div className="mb-5"><LanguageToggle /></div>

      <div className="font-sans text-[10px] text-coffee/55 text-center mb-1.5">{T('settings.version')}</div>
      <button
        onClick={handleSignOut}
        className="block w-full font-sans text-[12px] text-olive font-semibold underline"
      >{T('settings.signout')}</button>
    </div>
  );
}

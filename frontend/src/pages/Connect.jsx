import { PhoneFrame, Card, Chip, Button } from '../components/ui';
import { useApp } from '../lib/store';
import { useNavigate } from 'react-router-dom';

const CHANNELS = [
  { key: 'email',    label: 'Email',         hint: 'sneha.r@gmail.com' },
  { key: 'twitter',  label: 'X / Twitter',   hint: 'tap to connect' },
  { key: 'whatsapp', label: 'WhatsApp',      hint: 'tap to connect' },
  { key: 'phone',    label: 'Phone number',  hint: 'for SMS escalation' }
];

export default function Connect() {
  const channels = useApp(s => s.channels);
  const setChannel = useApp(s => s.setChannel);
  const navigate = useNavigate();
  const anyConnected = Object.values(channels).some(c => c.connected);

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        {/* progress dots */}
        <div className="flex gap-1.5 justify-center mb-3">
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-olive border border-line" />
          <span className="w-2 h-2 rounded-full bg-transparent border border-line" />
        </div>

        <Chip>Step 3 of 4 · ಸಂಪರ್ಕಿಸಿ</Chip>
        <h1 className="font-hand text-coffee text-[26px] leading-tight font-bold tracking-tight mt-1.5">
          Connect the<br />channels we'll<br />file from.
        </h1>
        <div className="font-kn text-coffee/70 text-[11px] mt-1.5 mb-3">ನಿಮ್ಮ ಪರವಾಗಿ ದೂರು ಸಲ್ಲಿಸಲು</div>
        <p className="font-sans text-[11.5px] text-coffee/75 leading-relaxed mb-4">
          We'll never post without your sign-off. Connect at least one — more channels = more pressure on agencies.
        </p>

        <div className="space-y-2 flex-1 overflow-y-auto">
          {CHANNELS.map(c => {
            const conn = channels[c.key];
            const done = conn?.connected;
            return (
              <Card
                key={c.key}
                tone={done ? 'mist' : 'paper'}
                padding="p-3"
                className={'flex items-center gap-3 cursor-pointer ' + (done ? 'border-olive' : '')}
                onClick={() => setChannel(c.key, { connected: !done, value: done ? '' : (conn?.value || c.hint) })}
              >
                <span className={[
                  'w-6 h-6 rounded-full border-[1.4px] flex items-center justify-center font-sans font-bold text-[11px]',
                  done ? 'bg-olive border-olive text-mist' : 'bg-transparent border-line text-coffee'
                ].join(' ')}>{done ? '✓' : ''}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-sans font-semibold text-coffee text-[12px]">{c.label}</div>
                  <div className={'font-mono text-[10px] truncate ' + (done ? 'text-olive' : 'text-coffee/55')}>{done ? conn.value : c.hint}</div>
                </div>
                <span className="font-sans text-[10px] text-olive font-semibold">{done ? 'Edit' : 'Connect →'}</span>
              </Card>
            );
          })}
        </div>

        <div className="font-hand text-center text-olive text-[13px] mt-3">
          {anyConnected ? '✓ ready to file' : '↓ at least one is required'}
        </div>

        <div className="flex gap-2 mt-3">
          <Button variant="secondary" onClick={() => navigate(-1)} className="flex-1">← Back</Button>
          <Button
            variant="primary"
            disabled={!anyConnected}
            onClick={() => navigate('/capture')}
            className="flex-[2]"
          >Continue →</Button>
        </div>
      </div>
    </PhoneFrame>
  );
}

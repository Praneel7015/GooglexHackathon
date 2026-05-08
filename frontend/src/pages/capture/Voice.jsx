import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame, Card, Chip } from '../../components/ui';
import StepHeader from '../../components/StepHeader';
import StepFooter from '../../components/StepFooter';
import { useApp } from '../../lib/store';
import { useT } from '../../lib/i18n';

const WAVE_SEED = [4, 9, 16, 22, 30, 40, 32, 46, 28, 38, 18, 26, 12, 30, 42, 52, 40, 30, 20, 14, 28, 38, 46, 30, 22, 16, 10, 18, 26, 34, 28, 20, 12, 6];
function Waveform({ recording }) {
  const w = 220, h = 40;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h} className="block">
      {WAVE_SEED.map((v, i) => (
        <rect key={i} x={i * 6 + 4} y={(h - v) / 2} width={3} height={v} rx={1.5} fill={recording ? '#71816d' : '#c9b79c'} style={recording ? { animation: `pulse-soft 1.4s ${i * 30}ms ease-in-out infinite` } : undefined} />
      ))}
    </svg>
  );
}

export default function Voice() {
  const T = useT();
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState(null);
  const recRef = useRef(null), chunksRef = useRef([]), timerRef = useRef(null), streamRef = useRef(null);
  const navigate = useNavigate();
  const cur = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);

  useEffect(() => {
    // No hardcoded transcript — backend will classify from photo
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, [cur.transcript, patch]);

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const rec = new MediaRecorder(stream);
      chunksRef.current = [];
      rec.ondataavailable = e => e.data.size && chunksRef.current.push(e.data);
      rec.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        patch({ voiceBlob: blob, voiceDuration: elapsed });
        if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      };
      rec.start();
      recRef.current = rec;
      setRecording(true); setElapsed(0);
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    } catch (e) { setError(e.message || 'Mic blocked — type your description below.'); }
  };
  const stop = () => {
    if (recRef.current && recRef.current.state !== 'inactive') recRef.current.stop();
    clearInterval(timerRef.current); timerRef.current = null;
    setRecording(false);
  };
  const fmt = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <StepHeader kicker={T('voice.step')} title={T('voice.heading')} />

        <div className="flex gap-2.5 items-center mt-3 mb-3">
          {cur.photo ? <img src={cur.photo} alt="" className="w-12 h-12 object-cover border-[1.5px] border-line rounded" /> : <div className="img-x w-12 h-12" />}
          <div>
            <div className="font-sans text-[10px] text-coffee/70">{T('cap.captured')} {cur.photoTime || 'just now'}</div>
            <div className="font-mono text-[10px] text-coffee">{cur.gps?.map(n => n.toFixed(3)).join('° N, ') || '—'}° E</div>
          </div>
        </div>

        <Card tone="mist" padding="px-3 py-2.5" className="mb-2.5">
          <div className="flex justify-between font-sans text-[9px] text-coffee/70 mb-1">
            <span>{recording ? T('cap.recording') : (cur.voiceBlob ? T('cap.recorded') : T('cap.tap'))}</span>
            <span className="font-mono">{fmt(elapsed)}</span>
          </div>
          <div className="flex items-center gap-2.5">
            <button onClick={recording ? stop : start} aria-label={recording ? 'Stop' : 'Record'} className={['w-9 h-9 rounded-full border-[1.5px] border-line text-mist text-[14px] flex items-center justify-center', recording ? 'bg-rust shadow-[0_0_0_4px_rgba(201,90,60,.25)]' : 'bg-coffee'].join(' ')}>{recording ? '■' : '●'}</button>
            <Waveform recording={recording} />
          </div>
          {error && <div className="font-sans text-[10px] text-rust mt-1.5">{error}</div>}
        </Card>

        <Card dashed padding="p-2.5" className="mb-2.5">
          <textarea value={cur.transcript} onChange={e => patch({ transcript: e.target.value })} rows={2} className="w-full bg-transparent border-0 resize-none italic font-sans text-[11px] text-coffee/65 mt-1.5 p-0 focus:outline-none" />
        </Card>

        <div className="font-sans text-[9px] uppercase tracking-wider text-coffee/55 mb-1">{T('cap.autoclass')}</div>
        <div className="flex gap-1.5 flex-wrap">
          <Chip tone="olive">{cur.issue}</Chip>
          <Chip tone="coffee">Severity {cur.severity}</Chip>
          <Chip dashed>{cur.agencyCode}</Chip>
        </div>

        <StepFooter back={() => navigate('/capture')} primary={() => navigate('/agents')} />
      </div>
    </PhoneFrame>
  );
}

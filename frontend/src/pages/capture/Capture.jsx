import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame, Chip } from '../../components/ui';
import { useApp } from '../../lib/store';
import { useT } from '../../lib/i18n';

export default function Capture() {
  const T = useT();
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);
  const [ready, setReady] = useState(false);
  const navigate = useNavigate();
  const patch = useApp(s => s.patchCurrent);
  const reset = useApp(s => s.resetCurrent);

  useEffect(() => { reset(); }, [reset]);

  useEffect(() => {
    let cancelled = false;
    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } }, audio: false
        });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
          setReady(true);
        }
      } catch (e) { setError(e.message || 'Camera unavailable'); }
    }
    start();
    return () => {
      cancelled = true;
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  const capture = () => {
    let dataUrl = null;
    const v = videoRef.current;
    if (v && ready) {
      const c = document.createElement('canvas');
      c.width = v.videoWidth || 640; c.height = v.videoHeight || 480;
      c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
      dataUrl = c.toDataURL('image/jpeg', 0.85);
    }
    patch({
      photo: dataUrl,
      photoTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      gps: [13.0995, 77.5963],
      ward: 95
    });
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    navigate('/voice');
  };

  return (
    <PhoneFrame>
      <div className="relative h-full bg-ink overflow-hidden flex flex-col">
        <div className="absolute inset-0">
          {error ? (
            <div className="img-x absolute inset-0">
              <div className="absolute inset-0 flex items-center justify-center text-center px-6 text-coffee/65 font-hand text-[13px]">
                {T('cap.blocked')}
              </div>
            </div>
          ) : (
            <video ref={videoRef} muted playsInline autoPlay className="w-full h-full object-cover" style={{ filter: 'saturate(.85)' }} />
          )}
          <div className="absolute inset-0 bg-olive opacity-[.12] mix-blend-multiply pointer-events-none" />
        </div>

        <div className="relative z-10 flex justify-center pt-2">
          <Chip tone="coffee" className="text-[10px]">
            <span className="w-2 h-2 rounded-full bg-olive inline-block" />
            {T('cap.autolocated')}
          </Chip>
        </div>
        <div className="relative z-10 text-center px-3 mt-3">
          <div className="font-kn text-mist text-[13px]" style={{ textShadow: '0 1px 2px rgba(0,0,0,.6)' }}>ಸಮಸ್ಯೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ</div>
          <div className="font-sans text-mist text-[11px] mt-0.5" style={{ textShadow: '0 1px 2px rgba(0,0,0,.6)' }}>{T('capture.heading')}</div>
        </div>

        {[[16, 80], [null, 80, 16], [16, null, null, 180], [null, null, 16, 180]].map((p, i) => {
          const [l, t, r, b] = p;
          return <div key={i} className="absolute z-10" style={{
            left: l, top: t, right: r, bottom: b, width: 18, height: 18,
            borderTop: i < 2 ? '2px solid #fbf8f1' : undefined,
            borderBottom: i >= 2 ? '2px solid #fbf8f1' : undefined,
            borderLeft: l != null ? '2px solid #fbf8f1' : undefined,
            borderRight: r != null ? '2px solid #fbf8f1' : undefined
          }} />;
        })}

        <div className="relative z-10 mt-auto pb-7 flex items-center justify-around">
          <div className="border-[1.5px] border-line bg-paper w-9 h-9 rounded" />
          <button onClick={capture} aria-label="Capture" className="w-16 h-16 rounded-full bg-olive border-[3px] border-paper active:scale-95 transition-transform" style={{ boxShadow: '0 0 0 1.5px #2a221b' }} />
          <div className="bg-coffee text-mist border-[1.5px] border-line w-9 h-9 rounded-full flex items-center justify-center text-[14px]">🎙</div>
        </div>
        <div className="relative z-10 text-center pb-2 font-hand text-[12px] text-mist/85" style={{ textShadow: '0 1px 2px rgba(0,0,0,.6)' }}>
          {T('cap.step')}
        </div>
      </div>
    </PhoneFrame>
  );
}

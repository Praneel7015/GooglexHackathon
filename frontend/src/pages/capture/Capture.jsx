import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame, Chip } from '../../components/ui';
import { useApp } from '../../lib/store';
import { useT } from '../../lib/i18n';

// Defined outside Capture so React doesn't remount it on every render
function BottomBar({ T, onCapture, onUploadChange }) {
  return (
    <>
      <div className="flex items-center justify-around px-8"
        style={{ position:'absolute', bottom:32, left:0, right:0, zIndex:20 }}>
        <label className="border-[1.5px] border-line bg-paper w-9 h-9 rounded flex items-center justify-center cursor-pointer active:scale-95 transition-transform overflow-hidden">
          <input type="file" accept="image/*" className="hidden" onChange={onUploadChange} />
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#342a21" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </label>
        <button
          onClick={onCapture}
          type="button"
          aria-label="Capture"
          className="w-16 h-16 rounded-full bg-olive border-[3px] border-paper active:scale-95 transition-transform"
          style={{ boxShadow:'0 0 0 1.5px #2a221b' }}
        />
        <div className="bg-coffee text-mist border-[1.5px] border-line w-9 h-9 rounded-full flex items-center justify-center text-[14px]">🎙</div>
      </div>
    </>
  );
}

export default function Capture() {
  const T = useT();
  const mobileVideoRef  = useRef(null);
  const desktopVideoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);
  const [ready, setReady] = useState(false);
  const navigate = useNavigate();
  const cur   = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);
  const reset = useApp(s => s.resetCurrent);

  useEffect(() => { reset(); }, [reset]);

  // GPS
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      pos => patch({ gps: [pos.coords.latitude, pos.coords.longitude] }),
      () => {}
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Camera — attach stream to whichever video elements are mounted
  useEffect(() => {
    let cancelled = false;
    async function start() {
      const constraints = [
        { video: { facingMode: { exact: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
        { video: { facingMode: { ideal: 'environment' } }, audio: false },
        { video: true, audio: false },
      ];
      let stream = null;
      for (const c of constraints) {
        try { stream = await navigator.mediaDevices.getUserMedia(c); break; }
        catch (_) { /* try next */ }
      }
      if (!stream) { setError('Camera unavailable'); return; }
      if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
      streamRef.current = stream;

      // Attach to both refs — whichever is mounted gets the feed
      const attach = (el) => {
        if (!el) return;
        el.srcObject = stream;
        el.onloadedmetadata = () => {
          el.play().catch(() => {});
          setReady(true);
        };
      };
      attach(mobileVideoRef.current);
      attach(desktopVideoRef.current);
    }
    start();
    return () => {
      cancelled = true;
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    };
  }, []);

  const goBack = (e) => {
    e.stopPropagation();
    if (window.history.length > 1) navigate(-1);
    else navigate('/');
  };

  const capture = () => {
    // Use whichever video is active
    const v = mobileVideoRef.current ?? desktopVideoRef.current;
    let dataUrl = null;
    if (v && ready) {
      const c = document.createElement('canvas');
      c.width = v.videoWidth || 640;
      c.height = v.videoHeight || 480;
      c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
      dataUrl = c.toDataURL('image/jpeg', 0.85);
    }
    patch({
      photo: dataUrl,
      photoTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      gps: cur.gps || [12.9716, 77.5946],
      ward: null,
    });
    if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
    navigate('/voice');
  };

  const onUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      patch({
        photo: ev.target.result,
        photoTime: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        gps: [13.0995, 77.5963],
        ward: 95,
      });
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      navigate('/voice');
    };
    reader.readAsDataURL(file);
  };

  const brackets = [[16,100],[null,100,16],[16,null,null,170],[null,null,16,170]];

  /* ─────────────────────────────────────────────────────────────────
     MOBILE  (<md): standalone full-screen, NO PhoneFrame involved.
     PhoneFrame is wrapped in "hidden md:block" below so its own
     md:hidden div never fires here, preventing the duplicate-ref bug.
  ───────────────────────────────────────────────────────────────── */
  return (
    <>
      {/* MOBILE */}
      <div
        className="md:hidden"
        style={{ position:'relative', width:'100%', height:'100dvh', overflow:'hidden', background:'#0f0d0b' }}
      >
        {/* Back */}
        <button
          onClick={goBack}
          type="button"
          aria-label="Go back"
          className="w-10 h-10 rounded-full bg-black/50 text-white flex items-center justify-center backdrop-blur-md border border-white/20 active:scale-90 transition-transform touch-manipulation"
          style={{ position:'absolute', top:'calc(env(safe-area-inset-top, 0px) + 12px)', left:16, zIndex:50 }}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>

        {/* Live feed */}
        {!error && (
          <video
            ref={mobileVideoRef}
            muted
            playsInline
            autoPlay
            style={{ position:'absolute', top:0, left:0, width:'100%', height:'100%', objectFit:'cover', filter:'saturate(.9)', zIndex:1 }}
          />
        )}

        {/* Spinner */}
        {!error && !ready && (
          <div style={{ position:'absolute', inset:0, zIndex:10 }}
            className="flex flex-col items-center justify-center bg-ink">
            <div className="w-8 h-8 rounded-full border-2 border-mist/20 border-t-mist animate-spin mb-3"/>
            <span className="font-mono text-[10px] text-mist/55 tracking-wider">STARTING CAMERA…</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ position:'absolute', inset:0, zIndex:10 }}
            className="flex items-center justify-center text-center px-6 text-coffee/65 font-hand text-[13px]">
            {T('cap.blocked')}
          </div>
        )}

        {/* Tint */}
        <div style={{ position:'absolute', inset:0, zIndex:2, pointerEvents:'none' }} className="bg-olive opacity-[.08] mix-blend-multiply"/>

        {/* HUD */}
        <div style={{ position:'absolute', top:12, left:0, right:0, zIndex:20 }} className="flex justify-center">
          <Chip tone="coffee" className="text-[10px]">
            <span className="w-2 h-2 rounded-full bg-olive inline-block"/>
            {T('cap.autolocated')}
          </Chip>
        </div>
        <div style={{ position:'absolute', top:50, left:0, right:0, zIndex:20 }} className="text-center px-3">
          <div className="font-kn text-mist text-[13px]" style={{ textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>ಸಮಸ್ಯೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ</div>
          <div className="font-sans text-mist text-[11px] mt-0.5" style={{ textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>{T('capture.heading')}</div>
        </div>

        {/* Corner brackets */}
        {brackets.map(([l,t,r,b], i) => (
          <div key={i} style={{
            position:'absolute', zIndex:20,
            left:l, top:t, right:r, bottom:b, width:18, height:18,
            borderTop:    i < 2  ? '2px solid #fbf8f1' : undefined,
            borderBottom: i >= 2 ? '2px solid #fbf8f1' : undefined,
            borderLeft:   l != null ? '2px solid #fbf8f1' : undefined,
            borderRight:  r != null ? '2px solid #fbf8f1' : undefined,
          }}/>
        ))}

        <BottomBar T={T} onCapture={capture} onUploadChange={onUpload}/>
        <div className="text-center font-hand text-[12px] text-mist/85"
          style={{ position:'absolute', bottom:10, left:0, right:0, zIndex:20, textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>
          {T('cap.step')}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
          DESKTOP (≥md): hidden on mobile so PhoneFrame's own md:hidden
          div never renders — eliminating the duplicate-video-ref bug.
      ───────────────────────────────────────────────────────────────── */}
      <div className="hidden md:block">
        <PhoneFrame>
          <div className="relative flex flex-col flex-1 min-h-0 bg-ink overflow-hidden">
            <button
              onClick={goBack}
              type="button"
              aria-label="Go back"
              className="absolute left-4 top-12 z-50 w-10 h-10 rounded-full bg-black/50 text-white flex items-center justify-center backdrop-blur-md border border-white/20 active:scale-90 transition-transform"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
            </button>

            <div className="absolute inset-0">
              {error ? (
                <div className="absolute inset-0 flex items-center justify-center text-center px-6 text-coffee/65 font-hand text-[13px]">
                  {T('cap.blocked')}
                </div>
              ) : (
                <>
                  <video
                    ref={desktopVideoRef}
                    muted
                    playsInline
                    autoPlay
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ filter:'saturate(.9)' }}
                  />
                  {!ready && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-ink">
                      <div className="w-8 h-8 rounded-full border-2 border-mist/20 border-t-mist animate-spin mb-3"/>
                      <span className="font-mono text-[10px] text-mist/55 tracking-wider">STARTING CAMERA…</span>
                    </div>
                  )}
                </>
              )}
              <div className="absolute inset-0 bg-olive opacity-[.08] mix-blend-multiply pointer-events-none"/>
            </div>

            <div className="relative z-10 flex justify-center pt-2">
              <Chip tone="coffee" className="text-[10px]">
                <span className="w-2 h-2 rounded-full bg-olive inline-block"/>
                {T('cap.autolocated')}
              </Chip>
            </div>
            <div className="relative z-10 text-center px-3 mt-3">
              <div className="font-kn text-mist text-[13px]" style={{ textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>ಸಮಸ್ಯೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ</div>
              <div className="font-sans text-mist text-[11px] mt-0.5" style={{ textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>{T('capture.heading')}</div>
            </div>

            {[[16,80],[null,80,16],[16,null,null,180],[null,null,16,180]].map(([l,t,r,b], i) => (
              <div key={i} className="absolute z-10" style={{
                left:l, top:t, right:r, bottom:b, width:18, height:18,
                borderTop:    i < 2  ? '2px solid #fbf8f1' : undefined,
                borderBottom: i >= 2 ? '2px solid #fbf8f1' : undefined,
                borderLeft:   l != null ? '2px solid #fbf8f1' : undefined,
                borderRight:  r != null ? '2px solid #fbf8f1' : undefined,
              }}/>
            ))}

            <div className="relative z-10 mt-auto pb-7 flex items-center justify-around">
              <label className="border-[1.5px] border-line bg-paper w-9 h-9 rounded flex items-center justify-center cursor-pointer active:scale-95 transition-transform overflow-hidden">
                <input type="file" accept="image/*" className="hidden" onChange={onUpload}/>
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#342a21" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21 15 16 10 5 21"/>
                </svg>
              </label>
              <button onClick={capture} type="button" aria-label="Capture"
                className="w-16 h-16 rounded-full bg-olive border-[3px] border-paper active:scale-95 transition-transform"
                style={{ boxShadow:'0 0 0 1.5px #2a221b' }}/>
              <div className="bg-coffee text-mist border-[1.5px] border-line w-9 h-9 rounded-full flex items-center justify-center text-[14px]">🎙</div>
            </div>
            <div className="relative z-10 text-center pb-2 font-hand text-[12px] text-mist/85" style={{ textShadow:'0 1px 2px rgba(0,0,0,.6)' }}>
              {T('cap.step')}
            </div>
          </div>
        </PhoneFrame>
      </div>
    </>
  );
}

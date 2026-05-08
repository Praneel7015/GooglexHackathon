import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Chip } from '../components/ui';
import { useApp } from '../lib/store';

const CARDS = [
  {
    title: 'Photograph any\ncivic issue.',
    kn: 'ಯಾವುದೇ ನಾಗರಿಕ ಸಮಸ್ಯೆಯ ಫೋಟೋ',
    body: 'Pothole, garbage, broken light, water leak — point and shoot. We\'ll do the rest.',
    illustration: 'phone capturing pothole'
  },
  {
    title: 'AI files it across\n30+ agencies.',
    kn: 'ಎಐ 30+ ಏಜೆನ್ಸಿಗಳ ಮೂಲಕ ಸಲ್ಲಿಸುತ್ತದೆ',
    body: 'BBMP, BESCOM, BWSSB and more. We pick the right one and bundle with your neighbours.',
    illustration: 'agency constellation'
  },
  {
    title: 'Track it publicly\nuntil it\'s fixed.',
    kn: 'ಸಾರ್ವಜನಿಕವಾಗಿ ಟ್ರ್ಯಾಕ್ ಮಾಡಿ',
    body: '30-day escalation ladder. Day 7 councillor tag, Day 14 RTI, Day 21 media. Officials notice.',
    illustration: 'ward map · resolution'
  }
];

const SWIPE_THRESHOLD = 40;

export default function Onboarding() {
  const [idx, setIdx] = useState(0);
  const [dragX, setDragX] = useState(0);
  const dragStart = useRef(null);
  const isDragging = useRef(false);
  const navigate = useNavigate();
  const setOnboarded = useApp(s => s.setOnboarded);
  const last = idx === CARDS.length - 1;

  const goTo = (i) => setIdx(Math.max(0, Math.min(CARDS.length - 1, i)));
  const next = () => last ? (setOnboarded(true), navigate('/connect')) : goTo(idx + 1);
  const skip = () => { setOnboarded(true); navigate('/capture'); };

  const onPointerDown = (e) => {
    dragStart.current = e.clientX;
    isDragging.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e) => {
    if (!isDragging.current) return;
    setDragX(e.clientX - dragStart.current);
  };

  const onPointerUp = (e) => {
    if (!isDragging.current) return;
    isDragging.current = false;
    const delta = e.clientX - dragStart.current;
    dragStart.current = null;
    setDragX(0);
    if (delta < -SWIPE_THRESHOLD) goTo(idx + 1);
    else if (delta > SWIPE_THRESHOLD) goTo(idx - 1);
  };

  const stripOffset = -(idx * 100) + (dragX / 3.5);

  return (
    // Fills the available height given by AppShell, centered on desktop
    <div className="flex items-center justify-center min-h-[calc(100dvh-56px)] md:min-h-[calc(100dvh-0px)] bg-paper p-4">
      <div className="w-full max-w-sm flex flex-col gap-4">
        <div className="flex justify-between items-center">
          <Chip>Welcome · ಸ್ವಾಗತ</Chip>
          <button onClick={skip} className="font-sans text-[11px] text-coffee/65 underline">Skip</button>
        </div>

        {/* Viewport — clips the strip */}
        <div
          className="overflow-hidden rounded-md border-[1.5px] border-line bg-mist cursor-grab active:cursor-grabbing select-none touch-pan-y"
          style={{ height: '360px' }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          {/* Strip — all cards laid out in a row */}
          <div
            className="flex h-full"
            style={{
              width: `${CARDS.length * 100}%`,
              transform: `translateX(${stripOffset / CARDS.length}%)`,
              transition: isDragging.current ? 'none' : 'transform 0.38s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
              willChange: 'transform',
            }}
          >
            {CARDS.map((card, i) => (
              <div
                key={i}
                className="flex flex-col items-center justify-start text-center px-5 pt-6 pb-4"
                style={{ width: `${100 / CARDS.length}%` }}
              >
                <div className="img-x w-full h-28 mb-5 relative rounded-sm flex-shrink-0">
                  <div className="absolute inset-0 flex items-center justify-center font-hand text-coffee/55 text-[13px]">
                    [ {card.illustration} ]
                  </div>
                </div>
                <h1 className="font-hand text-[26px] leading-tight text-coffee whitespace-pre-line">{card.title}</h1>
                <div className="font-kn text-[11px] text-coffee/65 mt-1.5">{card.kn}</div>
                <p className="font-sans text-[12px] text-coffee/75 mt-3 leading-snug max-w-[240px]">{card.body}</p>

                <div className="flex gap-2 mt-auto pt-4">
                  {CARDS.map((_, d) => (
                    <span
                      key={d}
                      className={[
                        'rounded-full transition-all duration-300',
                        d === idx
                          ? 'w-5 h-2 bg-olive'
                          : 'w-2 h-2 bg-transparent border border-line/50'
                      ].join(' ')}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={() => goTo(idx - 1)} disabled={idx === 0}>← Back</Button>
          <Button variant="primary" onClick={next}>{last ? 'Get started →' : 'Next →'}</Button>
        </div>
      </div>
    </div>
  );
}

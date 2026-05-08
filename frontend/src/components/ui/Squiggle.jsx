export default function Squiggle({ width = 200, height = 14, color = '#71816d', strokeWidth = 2, className = '' }) {
  const w = width, h = height;
  const d = `M0 ${h/2} Q ${w*.1} 0, ${w*.2} ${h/2} T ${w*.4} ${h/2} T ${w*.6} ${h/2} T ${w*.8} ${h/2} T ${w} ${h/2}`;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className={className} aria-hidden>
      <path d={d} stroke={color} strokeWidth={strokeWidth} fill="none" strokeLinecap="round" />
    </svg>
  );
}

// Header used across the capture flow — kicker + heading + optional Kannada.
export default function StepHeader({ kicker, title, kn, className = '' }) {
  return (
    <div className={className}>
      {kicker && <div className="text-[10px] font-sans font-semibold uppercase tracking-wider text-olive">{kicker}</div>}
      {title && <h1 className="font-hand text-[26px] leading-[1.05] text-coffee mt-0.5">{title}</h1>}
      {kn && <div className="font-kn text-[11px] text-coffee/65 mt-1">{kn}</div>}
    </div>
  );
}

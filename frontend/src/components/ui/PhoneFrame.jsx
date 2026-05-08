// PhoneFrame — on a desktop viewport we show the app inside a hand-drawn
// phone shell so the design language matches the wireframes. On mobile
// we render full-bleed. The breakpoint is `md` (≥768).

export default function PhoneFrame({ children, full = false, className = '' }) {
  return (
    <>
      {/* mobile / explicit full-bleed: no frame */}
      <div className={`md:hidden flex flex-col h-[100dvh] w-full bg-paper relative ${className}`}>
        {children}
      </div>
      {/* desktop: phone-shaped chrome */}
      <div className={`hidden ${full ? '' : 'md:flex'} md:items-center md:justify-center md:py-8 ${className}`}>
        <div className="phone-frame w-[380px] h-[780px] relative overflow-hidden flex flex-col">
          <div className="absolute top-1.5 left-1/2 -translate-x-1/2 w-20 h-4 bg-ink rounded-full z-10" />
          <div className="absolute top-2.5 left-5 right-5 flex justify-between font-sans text-[10px] font-semibold text-ink z-10">
            <span>9:41</span>
            <span>···  ▮▮▮</span>
          </div>
          <div className="absolute inset-x-3.5 top-9 bottom-5 overflow-hidden flex flex-col">
            {children}
          </div>
          <div className="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-24 h-1 bg-ink/40 rounded-full" />
        </div>
      </div>
    </>
  );
}

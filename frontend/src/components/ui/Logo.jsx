export default function Logo({ size = 28, withText = true, dark = false }) {
  const text = dark ? 'text-mist' : 'text-coffee';
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className="rounded-full border-[1.5px] border-line bg-olive flex items-center justify-center text-mist font-hand font-bold leading-none"
        style={{ width: size, height: size, fontSize: Math.round(size * 0.62) }}
        aria-hidden
      >N</span>
      {withText && (
        <span className={`font-hand font-bold tracking-tight ${text}`} style={{ fontSize: Math.round(size * 0.85) }}>
          NammaCity
        </span>
      )}
    </span>
  );
}

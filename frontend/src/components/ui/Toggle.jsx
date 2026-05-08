// Sketchy switch — a real <button role="switch"> for a11y.
export default function Toggle({ on, onChange, label, ariaLabel }) {
  return (
    <button
      role="switch"
      aria-checked={!!on}
      aria-label={ariaLabel || label}
      onClick={() => onChange?.(!on)}
      className={[
        'relative h-[20px] w-[34px] rounded-full border-[1.4px] border-line',
        'transition-colors duration-150',
        on ? 'bg-olive' : 'bg-paper'
      ].join(' ')}
    >
      <span
        className={[
          'absolute top-[1px] h-[14px] w-[14px] rounded-full border border-line',
          'transition-all duration-150',
          on ? 'right-[1px] bg-paper' : 'left-[1px] bg-beige'
        ].join(' ')}
      />
    </button>
  );
}

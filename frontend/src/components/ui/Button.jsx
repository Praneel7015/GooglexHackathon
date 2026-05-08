// Button — single primitive used app-wide. Variants drive intent.
// Always renders a real <button> for a11y; pass `as="a"` if you need a link.

const VARIANTS = {
  primary:   'bg-olive text-mist border-line hover:bg-olive-dark active:translate-y-px',
  secondary: 'bg-paper text-coffee border-line hover:bg-mist active:translate-y-px',
  ghost:     'bg-transparent text-coffee border-transparent hover:bg-mist/60',
  dark:      'bg-coffee text-mist border-line hover:bg-ink',
  danger:    'bg-rust text-mist border-line hover:brightness-110'
};

const SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-3 text-[15px]'
};

export default function Button({
  variant = 'primary', size = 'md', as = 'button',
  full = false, className = '', children, ...rest
}) {
  const Cmp = as;
  const cls = [
    'inline-flex items-center justify-center gap-2 font-sans font-semibold',
    'border-[1.5px] rounded-lg transition-[background,transform] select-none',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    VARIANTS[variant], SIZES[size],
    full ? 'w-full' : '',
    className
  ].join(' ');
  return <Cmp className={cls} {...rest}>{children}</Cmp>;
}

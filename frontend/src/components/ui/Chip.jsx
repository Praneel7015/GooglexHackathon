const TONES = {
  paper:  'bg-paper text-coffee border-line',
  olive:  'bg-olive text-mist border-line',
  coffee: 'bg-coffee text-mist border-line',
  mist:   'bg-mist text-coffee border-line',
  beige:  'bg-beige text-coffee border-line',
  ghost:  'bg-transparent text-coffee border-line'
};

export default function Chip({ tone = 'paper', dashed = false, className = '', children, ...rest }) {
  const cls = [
    'inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-sans font-medium',
    'rounded-full border-[1.4px] uppercase tracking-wider',
    dashed ? 'border-dashed' : '',
    TONES[tone], className
  ].join(' ');
  return <span className={cls} {...rest}>{children}</span>;
}

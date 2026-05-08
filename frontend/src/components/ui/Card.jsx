// Card — sketchy bordered container. Used for everything from list rows
// to hero panels. Tone controls fill colour.

const TONES = {
  paper:  'bg-paper text-coffee',
  mist:   'bg-mist text-coffee',
  beige:  'bg-beige text-coffee',
  olive:  'bg-olive text-mist',
  coffee: 'bg-coffee text-mist',
  ghost:  'bg-transparent text-coffee'
};

export default function Card({
  tone = 'paper', dashed = false, padding = 'p-4',
  className = '', children, ...rest
}) {
  const cls = [
    'border-[1.5px] border-line rounded-md relative',
    dashed ? 'border-dashed' : '',
    TONES[tone], padding, className
  ].join(' ');
  return <div className={cls} {...rest}>{children}</div>;
}

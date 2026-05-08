// Form field — input or textarea wrapped with sketchy borders.
export default function Field({ label, hint, multiline, className = '', ...rest }) {
  const Tag = multiline ? 'textarea' : 'input';
  return (
    <label className={'block ' + className}>
      {label && (
        <span className="block text-[10px] uppercase tracking-wider font-sans font-semibold text-olive mb-1">
          {label}
        </span>
      )}
      <Tag
        {...rest}
        className={[
          'w-full border-[1.5px] border-line rounded-md bg-paper px-3 py-2',
          'font-sans text-[13px] text-coffee placeholder:text-coffee/40',
          'focus:outline-none focus:border-olive focus:ring-2 focus:ring-olive/30',
          multiline ? 'min-h-[88px] resize-y' : ''
        ].join(' ')}
      />
      {hint && <span className="block mt-1 text-[10px] font-sans text-coffee/60">{hint}</span>}
    </label>
  );
}

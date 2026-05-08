// Sticky footer used across the multi-step capture flow.
import Button from './ui/Button';

export default function StepFooter({
  back, backLabel = 'Back',
  primary, primaryLabel = 'Continue', primaryDisabled = false,
  hint
}) {
  return (
    <div className="mt-auto pt-2">
      {hint && <div className="text-[11px] font-sans text-coffee/60 text-center pb-2">{hint}</div>}
      <div className="flex gap-2">
        {back && (
          <Button onClick={back} variant="secondary" className="flex-1">← {backLabel}</Button>
        )}
        {primary && (
          <Button onClick={primary} variant="primary" disabled={primaryDisabled}
            className={back ? 'flex-[2]' : 'flex-1'}>{primaryLabel} →</Button>
        )}
      </div>
    </div>
  );
}

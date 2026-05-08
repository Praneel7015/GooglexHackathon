import Button from './ui/Button';
import { useT } from '../lib/i18n';

export default function StepFooter({
  back, backLabelKey = 'cta.back',
  primary, primaryLabelKey = 'cta.continue', primaryDisabled = false,
  hint
}) {
  const T = useT();
  return (
    <div className="mt-auto pt-2">
      {hint && <div className="text-[11px] font-sans text-coffee/60 text-center pb-2">{hint}</div>}
      <div className="flex gap-2">
        {back && (
          <Button onClick={back} variant="secondary" className="flex-1">← {T(backLabelKey)}</Button>
        )}
        {primary && (
          <Button onClick={primary} variant="primary" disabled={primaryDisabled}
            className={back ? 'flex-[2]' : 'flex-1'}>{T(primaryLabelKey)} →</Button>
        )}
      </div>
    </div>
  );
}

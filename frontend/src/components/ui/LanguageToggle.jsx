import { useApp } from '../../lib/store';

const LANGS = [
  { code: 'KN', label: 'ಕನ್ನಡ' },
  { code: 'EN', label: 'EN' },
  { code: 'HI', label: 'हिं' }
];

export default function LanguageToggle({ tone = 'light', compact = false }) {
  const { language, setLanguage } = useApp();
  const isDark = tone === 'dark';
  return (
    <div className={`inline-flex border-[1.4px] border-line rounded-full overflow-hidden ${isDark ? 'border-mist/40' : ''}`}>
      {LANGS.map(({ code, label }) => {
        const active = code === language;
        const padX = compact ? 'px-2' : 'px-2.5';
        return (
          <button
            key={code}
            onClick={() => setLanguage(code)}
            className={[
              padX, 'py-1 font-sans text-[10px]',
              active
                ? (isDark ? 'bg-mist text-coffee font-bold' : 'bg-coffee text-mist font-bold')
                : (isDark ? 'text-mist' : 'text-coffee')
            ].join(' ')}
          >{label}</button>
        );
      })}
    </div>
  );
}

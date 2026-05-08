// Visual representation of the 6-stage pipeline. Pure presentational —
// stage state is driven by a parent that uses runPipeline().
import { AGENT_STAGES } from '../lib/agents';

export default function AgentPipeline({ activeIndex = 0, outputs = {} }) {
  return (
    <div className="relative pl-1">
      <div className="absolute left-[14px] top-2 bottom-2 w-px border-l border-dashed border-beige" />
      {AGENT_STAGES.map((s, i) => {
        const status = i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'queued';
        return (
          <div
            key={s.key}
            className={`flex gap-3 py-2 items-start transition-opacity duration-300 ${status === 'queued' ? 'opacity-50' : 'opacity-100'}`}
          >
            <div className="w-7 flex justify-center pt-0.5">
              <span
                className={[
                  'block w-3.5 h-3.5 rounded-full border-[1.5px] border-line',
                  status === 'done'   ? 'bg-paper'   : '',
                  status === 'active' ? 'bg-olive shadow-[0_0_0_4px_rgba(113,129,109,.25)] animate-pulse-soft' : '',
                  status === 'queued' ? 'bg-paper'   : ''
                ].join(' ')}
                aria-hidden
              >
                {status === 'done' && (
                  <svg viewBox="0 0 14 14" className="w-full h-full">
                    <path d="M3 7 L6 10 L11 4" stroke="#71816d" strokeWidth="2" fill="none" strokeLinecap="round" />
                  </svg>
                )}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between gap-2 font-sans text-[12px] font-semibold text-coffee">
                <span>{s.name}</span>
                <span className="font-mono text-[10px] text-coffee/55">
                  {status === 'active' ? '· · ·' : status === 'done' ? '✓' : ''}
                </span>
              </div>
              <div className="font-sans text-[11px] text-coffee/70 leading-snug mt-0.5">
                {status === 'queued' ? 'queued' : (outputs[s.key] || s.hint)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

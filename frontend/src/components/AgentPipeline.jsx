import { AGENT_STAGES } from '../lib/agents';

export default function AgentPipeline({ activeIndex = 0, outputs = {} }) {
  return (
    <div className="w-full max-w-[340px] mx-auto relative mt-2">
      {/* Background continuous line */}
      <div className="absolute left-1/2 top-3 bottom-6 w-[2px] -ml-[1px] bg-line/20 rounded-full" />
      
      {AGENT_STAGES.map((s, i) => {
        const status = i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'queued';
        const isLast = i === AGENT_STAGES.length - 1;
        const isLeft = i % 2 === 0;

        return (
          <div
            key={s.key}
            className={`relative flex w-full transition-opacity duration-300 ${status === 'queued' ? 'opacity-60' : 'opacity-100'}`}
          >
            {/* Foreground line segment */}
            {!isLast && (
              <div 
                className={`absolute left-1/2 top-[22px] bottom-[-4px] w-[2px] -ml-[1px] transition-colors duration-500 z-0 ${status === 'done' ? 'bg-olive' : 'bg-transparent'}`} 
              />
            )}

            {/* Left Column */}
            <div className={`w-1/2 pr-6 pt-0.5 pb-7 ${isLeft ? 'text-right' : ''}`}>
              {isLeft && (
                <>
                  <div className="font-sans text-[13px] font-semibold text-coffee">{s.name}</div>
                  <div className="font-sans text-[11px] text-coffee/70 leading-relaxed mt-0.5">
                    {status === 'queued' ? 'queued' : (outputs[s.key] || s.hint)}
                  </div>
                </>
              )}
            </div>

            {/* Center Circle */}
            <div className="absolute left-1/2 top-1 -ml-[9px] z-10 bg-paper py-1">
              <span
                className={[
                  'flex items-center justify-center w-[18px] h-[18px] rounded-full border-[2px] transition-colors duration-300',
                  status === 'done'   ? 'bg-olive border-olive text-paper' : 
                  status === 'active' ? 'bg-paper border-olive shadow-[0_0_0_4px_rgba(113,129,109,.15)] animate-pulse-soft' : 
                  'bg-paper border-line/50'
                ].join(' ')}
                aria-hidden
              >
                {status === 'done' && (
                  <svg viewBox="0 0 14 14" className="w-[10px] h-[10px]">
                    <path d="M3 7.5 L5.5 10 L11 4" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </span>
            </div>

            {/* Right Column */}
            <div className={`w-1/2 pl-6 pt-0.5 pb-7 ${!isLeft ? 'text-left' : ''}`}>
              {!isLeft && (
                <>
                  <div className="font-sans text-[13px] font-semibold text-coffee">{s.name}</div>
                  <div className="font-sans text-[11px] text-coffee/70 leading-relaxed mt-0.5">
                    {status === 'queued' ? 'queued' : (outputs[s.key] || s.hint)}
                  </div>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

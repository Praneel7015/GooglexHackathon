import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame } from '../../components/ui';
import StepHeader from '../../components/StepHeader';
import AgentPipeline from '../../components/AgentPipeline';
import { runPipeline, AGENT_STAGES } from '../../lib/agents';
import { useApp } from '../../lib/store';
import { findNearby } from '../../lib/seed';

export default function Agents() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [outputs, setOutputs] = useState({});
  const navigate = useNavigate();
  const cur = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);

  useEffect(() => {
    const cancel = runPipeline(cur, {
      onStage: (i, stage, output) => {
        setActiveIndex(i + 1);
        setOutputs(o => ({ ...o, [stage.key]: output }));
        if (stage.key === 'crowd') {
          const nearby = findNearby({ ll: cur.gps || [13.0995, 77.5963], issue: cur.issue, id: 'NEW' });
          patch({ nearby, bundleSize: nearby.length });
        }
      },
      onDone: () => setTimeout(() => navigate('/confirm'), 600),
      perStageMs: 900
    });
    return cancel;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <StepHeader kicker="Step 3 · Filing" title={'The agents are\nworking on it.'} kn="ಏಜೆಂಟ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ" />
        <div className="mt-4 flex-1">
          <AgentPipeline activeIndex={activeIndex} outputs={outputs} />
        </div>
        <div className="text-right font-hand text-olive text-[13px] -rotate-2 -mt-2">~ live ~</div>
        <div className="font-mono text-center text-[10px] text-coffee/55 mt-1">
          {activeIndex >= AGENT_STAGES.length ? 'pipeline complete' : `${activeIndex} / ${AGENT_STAGES.length} agents done`}
        </div>
      </div>
    </PhoneFrame>
  );
}

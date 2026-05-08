import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame } from '../../components/ui';
import StepHeader from '../../components/StepHeader';
import AgentPipeline from '../../components/AgentPipeline';
import { runPipeline, AGENT_STAGES } from '../../lib/agents';
import { useApp } from '../../lib/store';
import { findNearby } from '../../lib/seed';
import { useT } from '../../lib/i18n';

export default function Agents() {
  const T = useT();
  const [activeIndex, setActiveIndex] = useState(0);
  const [outputs, setOutputs] = useState({});
  const navigate = useNavigate();
  const cur = useApp(s => s.current);
  const patch = useApp(s => s.patchCurrent);

  // Capture latest values in refs so the pipeline effect only runs once on mount
  const curRef = useRef(cur);
  const patchRef = useRef(patch);
  const navigateRef = useRef(navigate);

  useEffect(() => {
    const snapshot = curRef.current;
    const cancel = runPipeline(snapshot, {
      onStage: (i, stage, output) => {
        setActiveIndex(i + 1);
        setOutputs(o => ({ ...o, [stage.key]: output }));
        if (stage.key === 'crowd') {
          const nearby = findNearby({ ll: snapshot.gps || [13.0995, 77.5963], issue: snapshot.issue, id: 'NEW' });
          patchRef.current({ nearby, bundleSize: nearby.length });
        }
      },
      onDone: () => setTimeout(() => navigateRef.current('/confirm'), 600),
      perStageMs: 900
    });
    return cancel;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PhoneFrame>
      <div className="flex flex-col h-full p-4">
        <StepHeader kicker={T('agents.step')} title={T('agents.heading')} />
        <div className="mt-4 flex-1">
          <AgentPipeline activeIndex={activeIndex} outputs={outputs} />
        </div>
        <div className="text-right font-hand text-olive text-[13px] -rotate-2 -mt-2">{T('ag.live')}</div>
        <div className="font-mono text-center text-[10px] text-coffee/55 mt-1">
          {activeIndex >= AGENT_STAGES.length ? T('ag.done') : T('ag.progress', { done: activeIndex, total: AGENT_STAGES.length })}
        </div>
      </div>
    </PhoneFrame>
  );
}

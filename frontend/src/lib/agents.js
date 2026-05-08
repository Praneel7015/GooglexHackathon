// Mock agent runner. In production, each step calls Google ADK / Gemini.
// For the demo, each stage resolves on a timer with deterministic output.

import { findNearby, AGENCIES, ROUTING } from './seed';

export const AGENT_STAGES = [
  { key: 'reporter', name: 'Reporter',         hint: 'Multimodal classification' },
  { key: 'geo',      name: 'Geo',              hint: 'Reverse-geocode + ward map' },
  { key: 'routing',  name: 'Routing',          hint: 'Pick agency from 30+' },
  { key: 'crowd',    name: 'Crowd Validation', hint: 'Bundle similar nearby (★ moat)' },
  { key: 'drafting', name: 'Drafting',         hint: 'Letter · tweet · email · RTI' },
  { key: 'submit',   name: 'Submission',       hint: 'Multi-channel dispatch' }
];

// Fake agent execution. Returns an unsubscribe function.
// `onStage(index, stage, output)` is called as each stage completes.
// `onDone()` fires once the final stage resolves.
export function runPipeline(complaint, { onStage, onDone, perStageMs = 900 }) {
  let cancelled = false;
  let i = 0;
  let timer = null;

  const fire = () => {
    if (cancelled || i >= AGENT_STAGES.length) {
      if (!cancelled) onDone?.();
      return;
    }
    const stage = AGENT_STAGES[i];
    const output = stageOutput(stage.key, complaint);
    onStage?.(i, stage, output);
    i += 1;
    timer = setTimeout(fire, perStageMs);
  };
  // small initial delay so the UI can mount
  timer = setTimeout(fire, 250);

  return () => { cancelled = true; if (timer) clearTimeout(timer); };
}

function stageOutput(key, c) {
  switch (key) {
    case 'reporter':
      return `Captured · ${c.issue || 'pothole'} · severity ${c.severity || 4}`;
    case 'geo':
      return `Mapped to Ward ${c.ward || 95} · ${c.gps ? c.gps.map(n => n.toFixed(3)).join(', ') : 'GPS missing → vision fallback'}`;
    case 'routing': {
      const agency = AGENCIES.find(a => a.code === (c.agencyCode || ROUTING[c.issue])) || AGENCIES[0];
      return `${agency.name} · ${agency.handle || agency.email}`;
    }
    case 'crowd': {
      const nearby = findNearby({
        ll: c.gps || [13.0995, 77.5963],
        issue: c.issue || 'Pothole',
        id: c.id || 'NEW'
      });
      return `Bundling ${nearby.length} nearby reports · joint complaint forming`;
    }
    case 'drafting':
      return 'Tweet · email · BBMP Sahaaya pre-fill drafted';
    case 'submit':
      return 'Dispatched · Twitter ✓ · Email ✓ · Portal ↗';
    default:
      return '';
  }
}

// Simulate channel-by-channel submission (for the Confirm screen).
// Returns timeline of channels that flip from "pending" to "sent".
export function runSubmission(complaint, onChannel, opts = {}) {
  const { perChannelMs = 600 } = opts;
  const channels = ['twitter', 'email', 'portal', 'whatsapp'];
  let cancelled = false, i = 0, timer = null;
  const tick = () => {
    if (cancelled || i >= channels.length) return;
    onChannel?.(channels[i]);
    i += 1;
    timer = setTimeout(tick, perChannelMs);
  };
  timer = setTimeout(tick, 300);
  return () => { cancelled = true; if (timer) clearTimeout(timer); };
}

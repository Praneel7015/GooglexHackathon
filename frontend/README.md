# NammaCity — Frontend (PWA)

Production-style React + Vite + Tailwind PWA for [NammaCity](../NammaCity-Master-Build-Doc.md). Installable on Android / iOS, works offline, real camera + voice capture, animated multi-agent pipeline, live ward dashboard.

## Run

```
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build
npm run preview
```

## Routes

| Path                | Purpose                                       | Shell        |
|---------------------|-----------------------------------------------|--------------|
| `/`                 | Public landing                                | Public       |
| `/install`          | PWA install QR + steps                        | Public       |
| `/onboard`          | 3-card onboarding swipe                       | (frame only) |
| `/connect`          | Connect channels (email · X · WhatsApp · …)   | (frame only) |
| `/capture`          | 1A · live camera + shutter                    | (frame only) |
| `/voice`            | 1B · MediaRecorder + transcript               | (frame only) |
| `/agents`           | 1C · animated 6-stage pipeline                | (frame only) |
| `/confirm`          | 1D · channel-by-channel dispatch              | (frame only) |
| `/crowd`            | "You're not alone" bundling animation         | (frame only) |
| `/dashboard`        | Live ward map · stats · trending issues       | App shell    |
| `/leaderboard`      | 198 wards ranked by resolution rate           | App shell    |
| `/officer/:id`      | Public officer scorecard                      | App shell    |
| `/track`            | 30-day escalation timeline                    | App shell    |
| `/track/:id`        | …for a specific complaint                     | App shell    |
| `/settings`         | Account · channels · preferences              | App shell    |

## Design tokens

Tailwind config exposes the brand palette as classes: `bg-mist`, `bg-beige`,
`bg-olive`, `bg-coffee`, `bg-paper`, `text-mist|coffee|olive|...`. Hand-drawn
fonts: `font-hand` (Caveat), `font-sketch` (Kalam), `font-kn` (Noto Sans
Kannada), `font-mono` (JetBrains Mono).

Reusable primitives in [`src/components/ui/`](./src/components/ui) (Button,
Card, Chip, Toggle, Field, PhoneFrame, LanguageToggle, Logo, Squiggle).

## State

[`src/lib/store.js`](./src/lib/store.js) — Zustand with localStorage persist.
- Onboarding · channels · preferences · language · user
- In-flight complaint (`current`) + filed history (`filed`)

## Mock backend

- [`src/lib/seed.js`](./src/lib/seed.js) — 200 deterministic synthetic
  complaints across 10 Bangalore wards, ward councillors, agency table.
- [`src/lib/agents.js`](./src/lib/agents.js) — `runPipeline()` simulates the
  6-stage ADK pipeline; `runSubmission()` flips channels. Drop in real
  Gemini / Twitter / Gmail calls when wiring backend.

## PWA

- `vite-plugin-pwa` generates the service worker + manifest at build time.
- Caches Google Fonts and Carto map tiles. Offline-installable from `/install`.
- Add real PNG icons (192 × 192 and 512 × 512) in `public/` if you need
  legacy-Android compatibility — current setup uses SVG icons.

## Wiring to the real backend

Each agent stage in [`agents.js`](./src/lib/agents.js) is a plain async
function returning a string. To replace with the real ADK pipeline:

```js
import { GoogleGenAI } from '@google/genai';
const reporter = async (c) => callGeminiVision(c.photo, c.transcript);
```

Then have your FastAPI / ADK orchestrator stream stage results over a
WebSocket and update the store. The UI already redraws from store mutations.

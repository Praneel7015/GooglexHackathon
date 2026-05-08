import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Top-level app store — what the user does flows through here.
export const useApp = create(persist((set, get) => ({
  // ── Onboarding / account ──────────────────────────────────────────
  language: 'EN', // 'EN' | 'KN' | 'HI' | 'TA'
  onboarded: false,
  channels: {
    email:    { connected: false, value: '' },
    twitter:  { connected: false, value: '' },
    whatsapp: { connected: false, value: '' },
    phone:    { connected: false, value: '' },
    aadhaar:  { connected: false, value: '' }
  },
  preferences: {
    autoBundle:   true,
    autoTweet7d:  true,
    fileAnonymous:false
  },
  user: { name: '', id: null, wardId: null },

  // ── In-flight complaint ───────────────────────────────────────────
  current: {
    id:         null,
    photo:      null,         // dataURL
    photoTime:  null,
    voiceBlob:  null,
    voiceDuration: 0,
    transcript: '',
    issue:      null,           // auto-classified by Reporter Agent
    severity:   null,           // auto-classified by Reporter Agent
    agencyCode: null,           // auto-routed by Routing Agent
    ward:       null,         // ward id
    gps:        null,         // [lat, lon]
    bundleSize: 0,
    nearby:     [],
    submittedAt:null,
    channels:   { twitter: false, email: false, portal: false, whatsapp: false }
  },

  // ── Filed complaints (this device) ────────────────────────────────
  filed: [],

  // ── Mutators ──────────────────────────────────────────────────────
  setLanguage: (lang) => set({ language: lang }),

  setOnboarded: (v) => set({ onboarded: v }),

  setChannel: (key, patch) => set((s) => ({
    channels: { ...s.channels, [key]: { ...s.channels[key], ...patch } }
  })),

  togglePreference: (key) => set((s) => ({
    preferences: { ...s.preferences, [key]: !s.preferences[key] }
  })),

  resetCurrent: () => set({
    current: {
      id: null, photo: null, photoTime: null, voiceBlob: null, voiceDuration: 0,
      transcript: '', issue: null, severity: null, agencyCode: null,
      ward: null, gps: null, bundleSize: 0, nearby: [], backendResult: null,
      submittedAt: null,
      channels: { twitter: false, email: false, portal: false, whatsapp: false }
    }
  }),

  patchCurrent: (patch) => set((s) => ({ current: { ...s.current, ...patch } })),

  patchChannel: (key, value) => set((s) => ({
    current: { ...s.current, channels: { ...s.current.channels, [key]: value } }
  })),

  fileCurrent: () => {
    const { current, filed } = get();
    // Use real backend complaint_id if available
    const id = current.backendResult?.complaint_id || current.id || `NMC-${2000 + filed.length}`;

    // Build timeline from backend escalation if available, else default
    const backendTimeline = current.backendResult?.escalation?.timeline;
    const timeline = backendTimeline
      ? backendTimeline.map(t => ({
          day: t.stage === 'submitted' ? 0 : t.stage === 'councillor_tagged' ? 7 :
               t.stage === 'rti_filed' ? 14 : t.stage === 'mla_tagged' ? 21 : 30,
          label: t.action,
          status: t.completed ? 'sent' : 'queued',
        }))
      : [
          { day: 0,  label: `Filed · ${current.agencyCode || 'BBMP'}`, status: 'sent' },
          { day: 3,  label: 'Twitter escalation · @BBMPCOMM', status: 'sent' },
          { day: 7,  label: 'Cc Ward Engineer', status: 'active' },
          { day: 14, label: 'CC councillor + RTI draft', status: 'queued' },
          { day: 21, label: 'Press alert · The Hindu civic desk', status: 'queued' },
          { day: 30, label: 'Public dashboard auto-elevation', status: 'queued' },
        ];

    const filedItem = {
      ...current,
      id,
      submittedAt: Date.now(),
      timeline,
    };
    set({ filed: [filedItem, ...filed], current: { ...current, id } });
    return filedItem;
  }
}), {
  name: 'nammacity-state',
  partialize: (s) => ({
    language: s.language, onboarded: s.onboarded, channels: s.channels,
    preferences: s.preferences, user: s.user, filed: s.filed
  })
}));

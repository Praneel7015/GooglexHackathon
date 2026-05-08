import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Top-level app store — what the user does flows through here.
export const useApp = create(persist((set, get) => ({
  // ── Onboarding / account ──────────────────────────────────────────
  language: 'EN', // 'EN' | 'KN' | 'HI' | 'TA'
  onboarded: false,
  channels: {
    email:    { connected: true,  value: 'sneha.r@gmail.com' },
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
  user: { name: 'Sneha Reddy', id: '1A-9381', wardId: 95 },

  // ── In-flight complaint ───────────────────────────────────────────
  current: {
    id:         null,
    photo:      null,         // dataURL
    photoTime:  null,
    voiceBlob:  null,
    voiceDuration: 0,
    transcript: '',
    issue:      'Pothole',
    severity:   4,
    agencyCode: 'BBMP-ROADS',
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
      transcript: '', issue: 'Pothole', severity: 4, agencyCode: 'BBMP-ROADS',
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
    const id = current.id || `NMC-${2000 + filed.length}`;
    const filedItem = {
      ...current,
      id,
      submittedAt: Date.now(),
      timeline: [
        { day: 0,  label: `Filed · ${current.agencyCode}`, status: 'sent' },
        { day: 3,  label: 'Twitter escalation · @BBMPCOMM', status: 'sent' },
        { day: 7,  label: 'Cc Ward Engineer', status: 'active' },
        { day: 14, label: 'CC councillor + RTI draft', status: 'queued' },
        { day: 21, label: 'Press alert · The Hindu civic desk', status: 'queued' },
        { day: 30, label: 'Public dashboard auto-elevation', status: 'queued' }
      ]
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

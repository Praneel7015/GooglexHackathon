/**
 * NammaCity API client — wraps all backend calls.
 * Falls back to null on network errors (frontend shows mock data as fallback).
 */

const BASE_URL = import.meta.env.VITE_API_URL
  || import.meta.env.VITE_API_BASE_URL
  || 'http://localhost:8000';

// Pipeline can take up to 60s (multiple Gemini calls in parallel)
const REPORT_TIMEOUT_MS = 60_000;
const DEFAULT_TIMEOUT_MS = 15_000;

async function safeFetch(url, opts = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    if (!res.ok) {
      console.warn('[api] HTTP error:', res.status, url);
      return null;
    }
    return await res.json();
  } catch (e) {
    if (e.name === 'AbortError') {
      console.warn('[api] request timed out:', url);
    } else {
      console.warn('[api] fetch failed:', url, e.message);
    }
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  /** Submit a complaint photo through the full 7-agent pipeline. */
  submitReport: async ({ photo, fallback_lat, fallback_lng, user_name, user_email, voice_note }) => {
    const fd = new FormData();
    fd.append('photo', photo);
    if (fallback_lat != null) fd.append('fallback_lat', String(fallback_lat));
    if (fallback_lng != null) fd.append('fallback_lng', String(fallback_lng));
    if (user_name) fd.append('user_name', user_name);
    if (user_email) fd.append('user_email', user_email);
    if (voice_note) fd.append('voice_note', voice_note);

    return safeFetch(`${BASE_URL}/api/v1/report`, { method: 'POST', body: fd }, REPORT_TIMEOUT_MS);
  },

  /** Dashboard totals + ward leaderboard. */
  getDashboardStats: () => safeFetch(`${BASE_URL}/api/v1/dashboard/stats`),

  /** All complaints + clusters for the Leaflet map. */
  getDashboardMap: (filters = {}) => {
    const params = new URLSearchParams(
      Object.fromEntries(Object.entries(filters).filter(([, v]) => v != null))
    );
    return safeFetch(`${BASE_URL}/api/v1/dashboard/map?${params}`);
  },

  /** Paginated complaint list. */
  listComplaints: (filters = {}) => {
    const params = new URLSearchParams(
      Object.fromEntries(Object.entries(filters).filter(([, v]) => v != null))
    );
    return safeFetch(`${BASE_URL}/api/v1/complaints?${params}`);
  },

  /** Single complaint with escalation timeline. */
  getComplaint: (id) => safeFetch(`${BASE_URL}/api/v1/complaints/${id}`),

  /** Health check. */
  health: () => safeFetch(`${BASE_URL}/health`),
};

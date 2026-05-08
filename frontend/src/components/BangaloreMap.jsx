import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { WARDS, COMPLAINTS } from '../lib/seed';

// Reusable map. `mode='clusters'` shows ward-cluster blooms (dashboard).
//                `mode='points'`   shows individual complaints (zoomed).
// `interactive` controls whether you can drag/zoom.
export default function BangaloreMap({
  mode = 'clusters',
  interactive = true,
  highlightWardId,
  className = ''
}) {
  const ref = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const cleanupMap = () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };

    const initMap = () => {
      if (mapRef.current) return true;
      if (el.offsetWidth === 0 || el.offsetHeight === 0) return false;
      const map = L.map(el, {
        center: [12.9716, 77.5946], zoom: 11,
        zoomControl: interactive, attributionControl: true,
        scrollWheelZoom: interactive, dragging: interactive,
        doubleClickZoom: interactive, touchZoom: interactive,
        boxZoom: interactive, keyboard: interactive
      });
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        subdomains: 'abcd', maxZoom: 19,
        attribution: '© OpenStreetMap · CARTO'
      }).addTo(map);

      drawLayer(map, mode, highlightWardId);
      mapRef.current = map;
      return true;
    };

    if (initMap()) {
      return cleanupMap;
    }

    const ro = new ResizeObserver(() => {
      if (initMap()) ro.disconnect();
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      cleanupMap();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-draw if mode/highlight changes after mount
  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;
    map.eachLayer(layer => {
      if (layer instanceof L.Marker || layer instanceof L.CircleMarker) map.removeLayer(layer);
    });
    drawLayer(map, mode, highlightWardId);
  }, [mode, highlightWardId]);

  return (
    <div className={`relative ${className}`}>
      <div ref={ref} className="absolute inset-0 bg-mist" />
      {/* warm overlay */}
      <div className="absolute inset-0 bg-olive opacity-[0.08] mix-blend-multiply pointer-events-none" />
      <div className="absolute inset-0 bg-mist opacity-[0.45] mix-blend-soft-light pointer-events-none" />
    </div>
  );
}

function drawLayer(map, mode, highlightWardId) {
  if (mode === 'points') {
    COMPLAINTS.forEach(c => {
      L.circleMarker(c.ll, {
        radius: 4,
        weight: 1,
        color: '#2a221b',
        fillColor: c.status === 'resolved' ? '#71816d' : c.status === 'escalated' ? '#c95a3c' : '#342a21',
        fillOpacity: .8
      }).addTo(map);
    });
    return;
  }
  // clusters
  WARDS.forEach(w => {
    const tones = {
      olive:  { fill: '#71816d', halo: 'rgba(113,129,109,.35)' },
      coffee: { fill: '#342a21', halo: 'rgba(52,42,33,.28)' },
      beige:  { fill: '#c9b79c', halo: 'rgba(201,183,156,.55)' }
    };
    const t = tones[w.tone];
    const r = Math.max(18, Math.min(40, 12 + Math.sqrt(w.open) * 1.1));
    const inner = Math.max(10, r * 0.5);
    const isActive = w.id === highlightWardId;
    const html = `
      <div style="position:relative;width:${r * 2}px;height:${r * 2}px;transform:translate(-50%,-50%);">
        <div style="position:absolute;inset:0;border-radius:50%;background:${t.halo};${isActive ? 'animation:pulse-soft 1.6s ease-in-out infinite;' : ''}"></div>
        <div style="position:absolute;left:50%;top:50%;width:${inner * 2}px;height:${inner * 2}px;transform:translate(-50%,-50%);
          border-radius:50%;background:${t.fill};border:1.4px solid #2a221b;
          display:flex;align-items:center;justify-content:center;
          font-family:'JetBrains Mono',monospace;font-size:${inner > 12 ? 11 : 9}px;font-weight:700;color:#fbf8f1;">${w.open}</div>
        <div style="position:absolute;left:50%;top:${r * 2 + 2}px;transform:translateX(-50%);
          font-family:Caveat,cursive;font-size:13px;color:#342a21;white-space:nowrap;
          text-shadow:0 0 3px #f1e0c5,0 0 6px #f1e0c5;">${w.name}</div>
      </div>`;
    L.marker(w.ll, {
      icon: L.divIcon({ html, className: '', iconSize: [0, 0] }),
      interactive: false
    }).addTo(map);
  });
}

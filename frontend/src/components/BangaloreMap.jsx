/**
 * BangaloreMap — renders the Leaflet map via an iframe to avoid
 * React StrictMode / lifecycle conflicts with Leaflet's DOM management.
 * The actual map logic lives in /public/map.html.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function BangaloreMap({
  mode = 'clusters',
  interactive = true,
  highlightWardId,
  className = ''
}) {
  const src = `/map.html?api=${encodeURIComponent(API_BASE)}&mode=${mode}`;

  return (
    <div className={`absolute inset-0 ${className}`}>
      <iframe
        src={src}
        title="Bangalore Map"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          border: 'none',
          zIndex: 1,
        }}
        allow="geolocation"
      />
      <div className="absolute inset-0 bg-olive opacity-[0.08] mix-blend-multiply pointer-events-none" style={{ zIndex: 2 }} />
    </div>
  );
}
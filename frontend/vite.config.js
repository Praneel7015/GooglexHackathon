import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icon-mask.svg'],
      manifest: {
        name: 'NammaCity — ನಮ್ಮಸಿಟಿ',
        short_name: 'NammaCity',
        description: "Bengaluru's civic operating system. Photograph any civic issue, get it filed across 30+ agencies, bundled with your neighbours, tracked publicly.",
        theme_color: '#342a21',
        background_color: '#f1e0c5',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          { src: '/favicon.svg',   sizes: '64x64',   type: 'image/svg+xml' },
          { src: '/icon-mask.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any maskable' }
        ],
        categories: ['government', 'social', 'utilities']
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\/.*/i,
            handler: 'CacheFirst',
            options: { cacheName: 'google-fonts', expiration: { maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 365 } }
          },
          {
            urlPattern: /^https:\/\/[a-d]\.basemaps\.cartocdn\.com\/.*/i,
            handler: 'CacheFirst',
            options: { cacheName: 'map-tiles', expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 } }
          }
        ]
      }
    })
  ],
  server: { port: 5173, host: true }
});

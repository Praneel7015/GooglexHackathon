/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        mist:   '#f1e0c5',
        beige:  '#c9b79c',
        olive:  '#71816d',
        'olive-dark': '#5a6c56',
        coffee: '#342a21',
        ink:    '#1a1614',
        paper:  '#fbf8f1',
        line:   '#2a221b',
        sand:   '#e6e0d2',
        rust:   '#c95a3c'
      },
      fontFamily: {
        hand:  ['"Caveat"', 'cursive'],
        sketch:['"Kalam"', '"Caveat"', 'cursive'],
        sans:  ['"Inter"', 'system-ui', 'sans-serif'],
        mono:  ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        kn:    ['"Noto Sans Kannada"', 'sans-serif']
      },
      boxShadow: {
        sketch: '0 12px 30px rgba(52,42,33,.12)',
        deep:   '0 24px 60px rgba(52,42,33,.18)',
        inset:  'inset 0 0 0 6px #fbf8f1'
      },
      animation: {
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
        'fade-in':    'fade-in .35s ease-out',
        'rise-in':    'rise-in .45s ease-out',
        'pop-in':     'pop-in .35s cubic-bezier(.34,1.56,.64,1)'
      },
      keyframes: {
        'pulse-soft': { '0%,100%': { opacity: '1', transform: 'scale(1)' }, '50%': { opacity: '.55', transform: 'scale(.96)' } },
        'fade-in':    { from: { opacity: '0' }, to: { opacity: '1' } },
        'rise-in':    { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'pop-in':     { from: { opacity: '0', transform: 'scale(.85)' }, to: { opacity: '1', transform: 'scale(1)' } }
      }
    }
  },
  plugins: []
};

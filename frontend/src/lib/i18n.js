// Tiny i18n. We don't pull a library — just a lookup with fallback to EN.
// Keep keys short and namespaced.

const dict = {
  EN: {
    'app.tagline': 'The city, filing back.',
    'app.tagline.sub': "Bengaluru's civic operating system.",
    'cta.install': 'Install the app',
    'cta.dashboard': 'Open dashboard',
    'cta.continue': 'Continue',
    'cta.back': 'Back',
    'cta.next': 'Next',
    'cta.skip': 'Skip',
    'cta.start': 'Get started',
    'capture.heading': 'Photograph the issue',
    'capture.step': 'Step 1 of 4',
    'voice.heading': "Tell us what's going on.",
    'voice.step': 'Step 2 · Add context',
    'agents.heading': 'The agents are working on it.',
    'agents.step': 'Step 3 · Filing',
    'confirm.heading': 'Filed on behalf of you and {n} neighbours.',
    'confirm.step': 'Step 4 · Filed',
    'track.heading': 'Track this complaint',
    'dash.live': "Bengaluru's Civic Pulse · Live",
    'lb.heading': 'How is your ward actually performing?',
    'crowd.heading': "You're not alone here.",
    'install.heading': 'Carry the city in your pocket.',
    'settings.heading': 'Settings'
  },
  KN: {
    'app.tagline': 'ನಗರ, ಮರು ದೂರು ಹಾಕುತ್ತಿದೆ.',
    'app.tagline.sub': 'ಬೆಂಗಳೂರಿನ ನಾಗರಿಕ ಆಪರೇಟಿಂಗ್ ಸಿಸ್ಟಮ್.',
    'cta.install': 'ಸ್ಥಾಪಿಸಿ',
    'cta.dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    'cta.continue': 'ಮುಂದೆ',
    'cta.back': 'ಹಿಂದೆ',
    'cta.next': 'ಮುಂದಿನದು',
    'cta.skip': 'ಬಿಟ್ಟುಬಿಡಿ',
    'cta.start': 'ಪ್ರಾರಂಭಿಸಿ',
    'capture.heading': 'ಸಮಸ್ಯೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ',
    'capture.step': 'ಹಂತ 1 / 4',
    'voice.heading': 'ಏನಾಗಿದೆ ಎಂಬುದನ್ನು ಹೇಳಿ.',
    'voice.step': 'ಹಂತ 2 · ಸಂದರ್ಭ',
    'agents.heading': 'ಏಜೆಂಟ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ.',
    'agents.step': 'ಹಂತ 3 · ಸಲ್ಲಿಕೆ',
    'confirm.heading': 'ನೀವು ಮತ್ತು {n} ನೆರೆಹೊರೆಯವರ ಪರವಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ.',
    'confirm.step': 'ಹಂತ 4 · ಸಲ್ಲಿಸಲಾಗಿದೆ',
    'track.heading': 'ಈ ದೂರನ್ನು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ',
    'dash.live': 'ಬೆಂಗಳೂರಿನ ನಾಗರಿಕ ನಾಡಿಮಿಡಿತ · ಲೈವ್',
    'lb.heading': 'ನಿಮ್ಮ ವಾರ್ಡ್ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ?',
    'crowd.heading': 'ನೀವು ಒಬ್ಬಂಟಿಯಲ್ಲ.',
    'install.heading': 'ನಗರವನ್ನು ಜೇಬಿನಲ್ಲಿ ಇಟ್ಟುಕೊಳ್ಳಿ.',
    'settings.heading': 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು'
  },
  HI: {
    'app.tagline': 'शहर, वापस शिकायत कर रहा है।',
    'install.heading': 'शहर को अपनी जेब में रखें।'
  },
  TA: {
    'app.tagline': 'நகரம், மீண்டும் புகார் செய்கிறது.',
    'install.heading': 'நகரத்தை உங்கள் சட்டையில்.'
  }
};

export function t(lang, key, vars = {}) {
  const v = (dict[lang] && dict[lang][key]) || dict.EN[key] || key;
  return v.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
}

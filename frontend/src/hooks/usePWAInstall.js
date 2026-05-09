import { useState, useEffect } from 'react';

/**
 * usePWAInstall
 *
 * Captures the browser's `beforeinstallprompt` event so we can trigger
 * the native "Add to Home Screen" dialog from our own UI button.
 *
 * Returns:
 *  - installPrompt: the deferred event (null if not eligible yet / already installed)
 *  - triggerInstall: call this to show the native dialog
 *  - isInstalled: true once user accepted or app is already in standalone mode
 */
export function usePWAInstall() {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(
    // Already running as a standalone PWA?
    window.matchMedia('(display-mode: standalone)').matches
  );

  useEffect(() => {
    const handler = (e) => {
      // Prevent the mini-infobar from appearing automatically on mobile
      e.preventDefault();
      setInstallPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handler);

    // Track when user installs from the native prompt or OS
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setInstallPrompt(null);
    });

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const triggerInstall = async () => {
    if (!installPrompt) return;
    await installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;
    if (outcome === 'accepted') {
      setIsInstalled(true);
      setInstallPrompt(null);
    }
  };

  return { installPrompt, triggerInstall, isInstalled };
}

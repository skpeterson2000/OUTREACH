import { useEffect, useRef, useCallback } from 'react';

interface UseIdleDetectorOptions {
  idleTime?: number; // milliseconds before considered idle
  onIdle: () => void; // callback when idle detected
  enabled?: boolean; // allow disabling the detector
}

/**
 * Hook to detect user inactivity and trigger a callback
 * Tracks mouse movement, keyboard input, and touch events
 */
export const useIdleDetector = ({
  idleTime = 4 * 60 * 1000, // default 4 minutes
  onIdle,
  enabled = true,
}: UseIdleDetectorOptions) => {
  const timeoutRef = useRef<number | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    if (enabled) {
      timeoutRef.current = setTimeout(() => {
        onIdle();
      }, idleTime);
    }
  }, [idleTime, onIdle, enabled]);

  useEffect(() => {
    if (!enabled) {
      // Clear timeout if detector is disabled
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      return;
    }

    // Activity event handlers
    const handleActivity = () => {
      resetTimer();
    };

    // Listen for various user activity events
    const events = [
      'mousedown',
      'mousemove',
      'keypress',
      'keydown',
      'scroll',
      'touchstart',
      'click',
    ];

    events.forEach((event) => {
      document.addEventListener(event, handleActivity);
    });

    // Start the initial timer
    resetTimer();

    // Cleanup
    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, resetTimer]);

  // Return function to manually reset the timer
  return {
    resetTimer,
    getLastActivity: () => lastActivityRef.current,
  };
};

import { useEffect } from 'react';

/**
 * useScrollReveal
 * Automatically observes elements marked with scroll reveal classes
 * and triggers hardware-accelerated reveal animations when scrolled into view.
 */
export const useScrollReveal = (dependency?: unknown) => {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const selector = '.reveal-on-scroll, .reveal-up, .reveal-left, .reveal-right, .reveal-scale';

    const initObserver = () => {
      const elements = document.querySelectorAll<HTMLElement>(selector);
      if (elements.length === 0) return;

      if (prefersReducedMotion) {
        elements.forEach((el) => el.classList.add('is-revealed'));
        return;
      }

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-revealed');
              observer.unobserve(entry.target);
            }
          });
        },
        {
          threshold: 0.06,
          rootMargin: '0px 0px -24px 0px'
        }
      );

      elements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        // If element is already well inside current view, reveal immediately with subtle stagger
        if (rect.top <= window.innerHeight * 0.92 && rect.bottom >= 0) {
          el.classList.add('is-revealed');
        } else {
          observer.observe(el);
        }
      });

      return () => {
        observer.disconnect();
      };
    };

    // Small tick to ensure React JSX tree has mounted to the DOM
    const timer = setTimeout(initObserver, 50);
    return () => clearTimeout(timer);
  }, [dependency]);
};

export default useScrollReveal;


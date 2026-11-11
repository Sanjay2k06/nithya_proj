import { useEffect } from 'react';

/**
 * useParallax
 * Tracks smooth mouse coordinates and viewport scroll to drive dynamic
 * parallax background depth and tilt effects via CSS custom variables.
 */
export const useParallax = () => {
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    let rafId: number;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      // Normalize to -1 ... 1 from screen center
      targetX = (e.clientX / window.innerWidth - 0.5) * 2;
      targetY = (e.clientY / window.innerHeight - 0.5) * 2;
    };

    const handleScroll = () => {
      const scrollProgress = window.scrollY / Math.max(1, document.body.scrollHeight - window.innerHeight);
      document.documentElement.style.setProperty('--scroll-progress', scrollProgress.toFixed(4));
      document.documentElement.style.setProperty('--scroll-y-px', `${window.scrollY}px`);
    };

    const animate = () => {
      // Smooth lerp
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      document.documentElement.style.setProperty('--parallax-x', `${(currentX * 18).toFixed(2)}px`);
      document.documentElement.style.setProperty('--parallax-y', `${(currentY * 18).toFixed(2)}px`);

      rafId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });
    rafId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      cancelAnimationFrame(rafId);
    };
  }, []);
};

export default useParallax;


/**
 * Navigation utilities for smooth scrolling and keyboard navigation
 */

export const scrollToElement = (elementId: string, smooth: boolean = true) => {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' });
  }
};

export const scrollToTop = (smooth: boolean = true) => {
  window.scrollTo({ top: 0, behavior: smooth ? 'smooth' : 'auto' });
};

export const scrollToBottom = (smooth: boolean = true) => {
  const height = document.documentElement.scrollHeight;
  window.scrollTo({ top: height, behavior: smooth ? 'smooth' : 'auto' });
};

export const getScrollPercentage = (): number => {
  const windowHeight = window.innerHeight;
  const documentHeight = document.documentElement.scrollHeight;
  const scrollTop = window.scrollY;
  return ((scrollTop + windowHeight) / documentHeight) * 100;
};

export const setupKeyboardNavigation = (callbacks: {
  onArrowUp?: () => void;
  onArrowDown?: () => void;
  onHome?: () => void;
  onEnd?: () => void;
  onPageUp?: () => void;
  onPageDown?: () => void;
}) => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      callbacks.onArrowUp?.();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      callbacks.onArrowDown?.();
    } else if (e.key === 'Home') {
      e.preventDefault();
      callbacks.onHome?.();
    } else if (e.key === 'End') {
      e.preventDefault();
      callbacks.onEnd?.();
    } else if (e.key === 'PageUp') {
      e.preventDefault();
      callbacks.onPageUp?.();
    } else if (e.key === 'PageDown') {
      e.preventDefault();
      callbacks.onPageDown?.();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
};

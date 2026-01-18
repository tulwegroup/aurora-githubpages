import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, ChevronsUp, ChevronsDown } from 'lucide-react';
import { scrollToTop, scrollToBottom, scrollToElement, getScrollPercentage, setupKeyboardNavigation } from '../utils/navigation';

interface ScrollNavigationProps {
  sections?: string[]; // Array of section IDs
  showScrollPercentage?: boolean;
}

const ScrollNavigation: React.FC<ScrollNavigationProps> = ({ sections = [], showScrollPercentage = true }) => {
  const [scrollPercent, setScrollPercent] = useState(0);
  const [showButtons, setShowButtons] = useState(false);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollPercent(getScrollPercentage());
      setShowButtons(window.scrollY > 300);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const cleanup = setupKeyboardNavigation({
      onHome: () => scrollToTop(),
      onEnd: () => scrollToBottom(),
      onPageUp: () => {
        if (currentSectionIndex > 0) {
          const newIndex = currentSectionIndex - 1;
          setCurrentSectionIndex(newIndex);
          scrollToElement(sections[newIndex]);
        }
      },
      onPageDown: () => {
        if (currentSectionIndex < sections.length - 1) {
          const newIndex = currentSectionIndex + 1;
          setCurrentSectionIndex(newIndex);
          scrollToElement(sections[newIndex]);
        }
      },
      onArrowUp: () => window.scrollBy(0, -100),
      onArrowDown: () => window.scrollBy(0, 100),
    });

    return cleanup;
  }, [currentSectionIndex, sections]);

  const scrollSmallUp = () => window.scrollBy({ top: -150, behavior: 'smooth' });
  const scrollSmallDown = () => window.scrollBy({ top: 150, behavior: 'smooth' });
  const scrollLargeUp = () => window.scrollBy({ top: -500, behavior: 'smooth' });
  const scrollLargeDown = () => window.scrollBy({ top: 500, behavior: 'smooth' });

  return (
    <>
      {/* Floating Navigation Bar */}
      {showButtons && (
        <div className="fixed right-4 bottom-4 flex flex-col gap-2 z-50">
          {/* Scroll Percentage */}
          {showScrollPercentage && (
            <div className="bg-aurora-600/80 backdrop-blur-md border border-aurora-500 rounded px-3 py-2 text-xs font-mono text-white text-center min-w-[60px]">
              {Math.round(scrollPercent)}%
            </div>
          )}

          {/* Quick Scroll Buttons */}
          <button
            onClick={scrollLargeUp}
            className="bg-aurora-600 hover:bg-aurora-500 text-white p-3 rounded-lg shadow-lg transition-all flex items-center justify-center"
            title="Page Up (or press Page Up)"
          >
            <ChevronsUp size={18} />
          </button>

          <button
            onClick={scrollSmallUp}
            className="bg-aurora-700 hover:bg-aurora-600 text-white p-3 rounded-lg shadow-lg transition-all flex items-center justify-center"
            title="Scroll Up (or press ↑)"
          >
            <ChevronUp size={18} />
          </button>

          <button
            onClick={scrollSmallDown}
            className="bg-aurora-700 hover:bg-aurora-600 text-white p-3 rounded-lg shadow-lg transition-all flex items-center justify-center"
            title="Scroll Down (or press ↓)"
          >
            <ChevronDown size={18} />
          </button>

          <button
            onClick={scrollLargeDown}
            className="bg-aurora-600 hover:bg-aurora-500 text-white p-3 rounded-lg shadow-lg transition-all flex items-center justify-center"
            title="Page Down (or press Page Down)"
          >
            <ChevronsDown size={18} />
          </button>

          {/* To Top Button */}
          <button
            onClick={() => scrollToTop()}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 rounded text-xs font-bold transition-all"
            title="Go to top (or press Home)"
          >
            ↑ TOP
          </button>

          {/* To Bottom Button */}
          <button
            onClick={() => scrollToBottom()}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-2 rounded text-xs font-bold transition-all"
            title="Go to bottom (or press End)"
          >
            ↓ BTM
          </button>
        </div>
      )}

      {/* Section Quick Nav - shown when there are sections */}
      {sections.length > 0 && showButtons && (
        <div className="fixed left-4 bottom-4 flex flex-col gap-1 z-50 max-h-[300px] overflow-y-auto">
          <div className="text-xs font-bold text-aurora-300 mb-2 px-2">SECTIONS</div>
          {sections.map((sectionId, idx) => (
            <button
              key={sectionId}
              onClick={() => {
                setCurrentSectionIndex(idx);
                scrollToElement(sectionId);
              }}
              className={`px-3 py-1 rounded text-xs font-mono transition-all ${
                currentSectionIndex === idx
                  ? 'bg-aurora-500 text-white'
                  : 'bg-aurora-800/50 hover:bg-aurora-700 text-aurora-300'
              }`}
            >
              {idx + 1}
            </button>
          ))}
        </div>
      )}

      {/* Keyboard Shortcuts Hint */}
      {showButtons && (
        <div className="fixed top-4 right-4 bg-aurora-900/80 backdrop-blur-md border border-aurora-700 rounded p-3 text-xs text-aurora-300 font-mono max-w-[200px] z-40">
          <div className="font-bold text-aurora-400 mb-1">⌨️ SHORTCUTS</div>
          <div>↑↓ Scroll • Pg↑↓ Jump</div>
          <div>Home/End • Top/Btm</div>
        </div>
      )}
    </>
  );
};

export default ScrollNavigation;

import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface FocusRingProps {
  targetElement: HTMLElement | null;
  dwellProgress: number; // 0-1, where 1 = dwell complete
  isVisible: boolean;
}

export const FocusRing: React.FC<FocusRingProps> = ({
  targetElement,
  dwellProgress,
  isVisible,
}) => {
  const ringRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!targetElement || !ringRef.current || !isVisible) {
      return;
    }

    const updatePosition = () => {
      const rect = targetElement.getBoundingClientRect();
      const ring = ringRef.current;
      if (!ring) return;

      ring.style.left = `${rect.left}px`;
      ring.style.top = `${rect.top}px`;
      ring.style.width = `${rect.width}px`;
      ring.style.height = `${rect.height}px`;
    };

    updatePosition();

    // Update on scroll/resize
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [targetElement, isVisible]);

  if (!isVisible || !targetElement) {
    return null;
  }

  return (
    <motion.div
      ref={ringRef}
      className='fixed pointer-events-none z-40'
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        border: '3px solid #6366f1',
        borderRadius: '8px',
        boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.3), 0 0 20px rgba(99, 102, 241, 0.5)',
      }}
    >
      {/* Pulse animation */}
      <motion.div
        className='absolute inset-0 border-2 border-[#6366f1] rounded-lg'
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.8, 0.4, 0.8],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Dwell progress ring */}
      {dwellProgress > 0 && (
        <motion.div
          className='absolute inset-0 border-4 border-[#22c55e] rounded-lg'
          style={{
            clipPath: `inset(0 ${100 - dwellProgress * 100}% 0 0)`,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        />
      )}
    </motion.div>
  );
};

export default FocusRing;



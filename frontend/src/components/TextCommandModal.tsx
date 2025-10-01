import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TextCommandModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (text: string) => Promise<void>;
}

export const TextCommandModal: React.FC<TextCommandModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Focus input when modal opens
      setTimeout(() => inputRef.current?.focus(), 100);
    } else {
      // Clear text when modal closes
      setText('');
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onSubmit(text.trim());
      onClose();
    } catch (error) {
      console.error('Error submitting command:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className='fixed inset-0 bg-black/60 backdrop-blur-sm z-40'
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className='fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md mx-4'
          >
            <div className='bg-[#111115] rounded-xl border border-[#27272a] p-6'>
              <div className='flex justify-between items-center mb-5'>
                <h3 className='text-lg font-semibold text-[#fafafa]'>
                  Voice Command
                </h3>
                <button
                  onClick={onClose}
                  className='text-[#71717a] hover:text-[#e4e4e7] transition-colors p-1'
                  aria-label='Close modal'
                >
                  <svg
                    className='w-5 h-5'
                    fill='none'
                    stroke='currentColor'
                    viewBox='0 0 24 24'
                  >
                    <path
                      strokeLinecap='round'
                      strokeLinejoin='round'
                      strokeWidth={2}
                      d='M6 18L18 6M6 6l12 12'
                    />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                <input
                  ref={inputRef}
                  type='text'
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder='e.g., "add todo buy milk" or "switch to ambient"'
                  className='w-full px-4 py-2.5 bg-[#18181b] text-[#e4e4e7] border border-[#27272a] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6366f1] focus:border-transparent placeholder:text-[#52525b] text-sm'
                  disabled={isSubmitting}
                />

                <div className='flex gap-2 mt-4'>
                  <button
                    type='button'
                    onClick={onClose}
                    className='flex-1 px-4 py-2 bg-transparent border border-[#27272a] text-[#a1a1aa] rounded-lg hover:bg-[#18181b] hover:text-[#e4e4e7] transition-all text-sm font-medium'
                    disabled={isSubmitting}
                  >
                    Cancel
                  </button>
                  <button
                    type='submit'
                    disabled={!text.trim() || isSubmitting}
                    className='flex-1 px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#5558e3] disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-medium'
                  >
                    {isSubmitting ? 'Processing...' : 'Send'}
                  </button>
                </div>
              </form>

              <div className='mt-5 pt-4 border-t border-[#27272a]'>
                <p className='text-xs text-[#71717a] mb-2 font-medium'>
                  Examples:
                </p>
                <ul className='space-y-1.5 text-xs text-[#a1a1aa]'>
                  <li className='flex items-center gap-2'>
                    <span className='text-[#52525b]'>•</span>
                    add todo buy groceries
                  </li>
                  <li className='flex items-center gap-2'>
                    <span className='text-[#52525b]'>•</span>
                    switch to morning
                  </li>
                  <li className='flex items-center gap-2'>
                    <span className='text-[#52525b]'>•</span>
                    switch to ambient
                  </li>
                </ul>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default TextCommandModal;

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
}) => {
  return (
    <div
      className={`bg-[#111115] border border-[#27272a] rounded-xl p-5 ${className}`}
    >
      {title && (
        <h3 className='text-base font-semibold mb-4 text-[#fafafa]'>{title}</h3>
      )}
      {children}
    </div>
  );
};

export default Card;

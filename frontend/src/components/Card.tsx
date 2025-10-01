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
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 ${className}`}
    >
      {title && <h3 className='text-lg font-semibold mb-3'>{title}</h3>}
      {children}
    </div>
  );
};

export default Card;

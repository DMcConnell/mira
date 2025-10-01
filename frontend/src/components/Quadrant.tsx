import React from 'react';

interface QuadrantProps {
  children: React.ReactNode;
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  className?: string;
}

export const Quadrant: React.FC<QuadrantProps> = ({
  children,
  position,
  className = '',
}) => {
  const positionClasses = {
    'top-left': 'row-start-1 col-start-1',
    'top-right': 'row-start-1 col-start-2',
    'bottom-left': 'row-start-2 col-start-1',
    'bottom-right': 'row-start-2 col-start-2',
  };

  return (
    <div className={`${positionClasses[position]} ${className}`}>
      {children}
    </div>
  );
};

export default Quadrant;

import React from 'react';

interface BrandLogoProps {
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  className,
  orientation = 'horizontal',
}) => (
  <img
    src={
      orientation === 'vertical'
        ? '/jyohar-innollege-vertical.png'
        : '/jyohar-innollege-horizontal.png'
    }
    alt="Jyohar Tech and Innollege"
    className={className}
  />
);

export default BrandLogo;

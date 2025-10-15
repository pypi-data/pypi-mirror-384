import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import styles from './AnimatedComponents.module.css';

interface ShimmerButtonProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: 'primary' | 'outline';
  className?: string;
}

export default function ShimmerButton({
  children,
  href,
  onClick,
  variant = 'primary',
  className
}: ShimmerButtonProps) {
  const Component = href ? 'a' : 'button';

  return (
    <Component
      href={href}
      onClick={onClick}
      className={clsx(
        styles.shimmerButton,
        variant === 'outline' && styles.outline,
        className
      )}
    >
      <motion.span
        className={styles.shimmerEffect}
        animate={{
          x: [-100, 400],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'linear',
        }}
      />
      <span className={styles.buttonContent}>{children}</span>
    </Component>
  );
}

import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import styles from './AnimatedComponents.module.css';

interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
}

export default function GradientText({ children, className }: GradientTextProps) {
  return (
    <motion.span
      className={clsx(styles.gradientText, className)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
    >
      {children}
    </motion.span>
  );
}

import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import styles from './AnimatedComponents.module.css';

interface AnimatedCardProps {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}

export default function AnimatedCard({ children, delay = 0, className }: AnimatedCardProps) {
  return (
    <motion.div
      className={clsx(styles.animatedCard, className)}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      whileHover={{
        scale: 1.02,
        boxShadow: '0 20px 40px rgba(96, 165, 250, 0.15)'
      }}
    >
      {children}
    </motion.div>
  );
}

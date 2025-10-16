import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface GlitchTextProps {
  mainTool?: string;
  alternateTools?: string[];
  glitchInterval?: number; // milliseconds between glitches
  glitchDuration?: number; // how long the glitch lasts
}

const DEFAULT_ALTERNATE_TOOLS = ['Codex', 'Gemini', 'Cursor', 'Copilot'];

export default function GlitchText({
  mainTool = 'Claude Code',
  alternateTools = DEFAULT_ALTERNATE_TOOLS,
  glitchInterval = 5000,
  glitchDuration = 200,
}: GlitchTextProps) {
  const [currentText, setCurrentText] = useState(mainTool);
  const [isGlitching, setIsGlitching] = useState(false);

  useEffect(() => {
    const glitchTimer = setInterval(() => {
      setIsGlitching(true);

      // Pick a random alternate tool
      const randomTool = alternateTools[Math.floor(Math.random() * alternateTools.length)];
      setCurrentText(randomTool);

      // Return to main tool after glitch duration
      setTimeout(() => {
        setCurrentText(mainTool);
        setIsGlitching(false);
      }, glitchDuration);
    }, glitchInterval);

    return () => clearInterval(glitchTimer);
  }, [mainTool, alternateTools, glitchInterval, glitchDuration]);

  return (
    <span style={{ display: 'inline-block', position: 'relative' }}>
      <AnimatePresence mode="wait">
        <motion.span
          key={currentText}
          initial={{ opacity: 0.8 }}
          animate={{
            opacity: 1,
            x: isGlitching ? [0, -3, 3, -2, 2, -1, 1, 0] : 0,
            filter: isGlitching
              ? [
                  'hue-rotate(0deg)',
                  'hue-rotate(90deg)',
                  'hue-rotate(180deg)',
                  'hue-rotate(270deg)',
                  'hue-rotate(0deg)',
                ]
              : 'hue-rotate(0deg)',
          }}
          exit={{ opacity: 0 }}
          transition={{
            duration: isGlitching ? glitchDuration / 1000 : 0.2,
            ease: 'easeInOut',
          }}
          style={{
            textShadow: isGlitching
              ? '3px 0 rgba(255, 0, 0, 0.7), -3px 0 rgba(0, 255, 255, 0.7)'
              : 'none',
            textDecoration: isGlitching ? 'none' : 'inherit',
          }}
        >
          {currentText}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

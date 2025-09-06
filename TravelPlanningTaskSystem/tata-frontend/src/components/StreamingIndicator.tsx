import React from 'react';
import { motion } from 'framer-motion';

const StreamingIndicator: React.FC = () => {
  return (
    <div className="streaming-indicator">
      <motion.div
        className="pulse-dot"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <span>AI思考中...</span>
    </div>
  );
};

export default StreamingIndicator;
import React from 'react';

const StreamingIndicator: React.FC = () => {
  return (
    <div className="streaming-indicator">
      <span></span>
      <span></span>
      <span></span>
      <span style={{ marginLeft: '0.5rem', fontSize: '14px', color: 'var(--primary-600)' }}>AI思考中...</span>
    </div>
  );
};

export default StreamingIndicator;
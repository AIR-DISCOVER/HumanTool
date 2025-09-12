export const getStepIcon = (type: string): string => {
  switch (type) {
    case 'thinking': return '🤔';
    case 'agenda_update': return '📋';
    case 'tool_call': return '🔧';
    case 'tool_result': return '✅';
    case 'draft_update': return '📝';
    default: return '💭';
  }
};

export const getToolStatusIcon = (status: string): string => {
  switch (status) {
    case 'calling': return '⏳';
    case 'completed': return '✅';
    case 'error': return '❌';
    default: return '🔧';
  }
};

export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
};

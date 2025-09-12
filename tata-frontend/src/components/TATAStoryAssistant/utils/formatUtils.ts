import { AgendaTask } from '../types';

export const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleTimeString();
};

export const getTaskStatusIcon = (status: string): string => {
  switch (status) {
    case 'completed': return '✅';
    case 'in_progress': return '🔄';
    case 'pending': return '📋';
    default: return '📋';
  }
};

export const getTaskStatusColor = (status: string): string => {
  switch (status) {
    case 'completed': return '#10B981';
    case 'in_progress': return '#3B82F6';
    case 'pending': return '#F59E0B';
    default: return '#6B7280';
  }
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

export const getWordCount = (text: string): number => {
  return text.length;
};

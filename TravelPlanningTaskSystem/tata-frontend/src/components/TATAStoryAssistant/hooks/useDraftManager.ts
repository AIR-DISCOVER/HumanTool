import { useState, useCallback } from 'react';
import { DraftContent } from '../types';

interface UseDraftManagerProps {
  sessionId: string;
  drafts: Record<string, DraftContent>;
  setDrafts: React.Dispatch<React.SetStateAction<Record<string, DraftContent>>>;
}

export const useDraftManager = ({ sessionId, drafts, setDrafts }: UseDraftManagerProps) => {
  const [editingDraft, setEditingDraft] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const handleEditDraft = useCallback((draftId: string) => {
    setEditingDraft(draftId);
    setEditContent(drafts[draftId]?.content || '');
  }, [drafts]);

  const handleSaveDraft = useCallback(async () => {
    if (!editingDraft) return;

    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      await fetch(`${apiBaseURL}/api/drafts/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          draft_id: editingDraft,
          content: editContent
        })
      });

      setDrafts(prev => ({
        ...prev,
        [editingDraft]: {
          ...prev[editingDraft],
          content: editContent,
          last_updated: Date.now(),
          updated_by: 'user'
        }
      }));

      setEditingDraft(null);
      setEditContent('');
    } catch (error) {
      console.error('Failed to update draft:', error);
    }
  }, [editingDraft, editContent, sessionId, setDrafts]);

  const handleCancelEdit = useCallback(() => {
    setEditingDraft(null);
    setEditContent('');
  }, []);

  const exportDrafts = useCallback(async () => {
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseURL}/api/drafts/${sessionId}/export`, {
        method: 'POST'
      });
      const data = await response.json();
      
      const blob = new Blob([data.export_content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `TATA-Story-${new Date().toISOString().split('T')[0]}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export drafts:', error);
    }
  }, [sessionId]);

  return {
    editingDraft,
    editContent,
    setEditContent,
    handleEditDraft,
    handleSaveDraft,
    handleCancelEdit,
    exportDrafts
  };
};

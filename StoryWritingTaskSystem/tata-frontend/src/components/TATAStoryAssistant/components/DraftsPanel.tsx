import React, { useState } from 'react';
import { DraftContent } from '../types';
import { getWordCount, truncateText } from '../utils/formatUtils';

interface DraftsPanelProps {
  drafts: Record<string, DraftContent>;
  editingDraft: string | null;
  editContent: string;
  setEditContent: (content: string) => void;
  onEditDraft: (draftId: string) => void;
  onSaveDraft: () => void;
  onCancelEdit: () => void;
  onExportDrafts: () => void;
}

export const DraftsPanel: React.FC<DraftsPanelProps> = ({
  drafts,
  editingDraft,
  editContent,
  setEditContent,
  onEditDraft,
  onSaveDraft,
  onCancelEdit,
  onExportDrafts
}) => {
  const [expandedDrafts, setExpandedDrafts] = useState<Set<string>>(new Set());

  const toggleExpand = (draftId: string) => {
    const newExpanded = new Set(expandedDrafts);
    if (newExpanded.has(draftId)) {
      newExpanded.delete(draftId);
    } else {
      newExpanded.add(draftId);
    }
    setExpandedDrafts(newExpanded);
  };

  const renderDraftCard = (draftId: string, draft: DraftContent) => {
    const safeContent = draft?.content || '';
    const safeUpdatedBy = draft?.updated_by || 'ai';
    const isExpanded = expandedDrafts.has(draftId);
    const isLongContent = safeContent.length > 200;
    
    return (
      <div key={draftId} className="draft-card">
        <div className="draft-header">
          <h4 className="draft-title">{draftId.replace(/_/g, ' ')}</h4>
          <div className="draft-meta">
            <span className="word-count">{getWordCount(safeContent)} 字符</span>
            <span className={`update-badge ${safeUpdatedBy}`}>
              {safeUpdatedBy === 'user' ? '用户编辑' : 'AI生成'}
            </span>
            {isLongContent && (
              <button
                onClick={() => toggleExpand(draftId)}
                className="expand-btn"
                title={isExpanded ? "收起" : "展开"}
              >
                {isExpanded ? '🔼' : '🔽'}
              </button>
            )}
            <button
              onClick={() => onEditDraft(draftId)}
              className="edit-btn"
              disabled={editingDraft === draftId}
              title="编辑草稿"
            >
              ✏️
            </button>
          </div>
        </div>
        
        <div className="draft-content">
          {editingDraft === draftId ? (
            <div className="edit-mode">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="edit-textarea"
                autoFocus
                style={{ minHeight: isLongContent ? '300px' : '150px' }}
              />
              <div className="edit-actions">
                <button onClick={onSaveDraft} className="save-btn">
                  💾 保存
                </button>
                <button onClick={onCancelEdit} className="cancel-btn">
                  ❌ 取消
                </button>
              </div>
            </div>
          ) : (
            <div className="draft-text">
              {(() => {
                const displayContent = (isLongContent && !isExpanded) 
                  ? truncateText(safeContent, 200) 
                  : safeContent;
                
                return displayContent.split('\n').map((line, index) => (
                  <p key={index} className="draft-paragraph">
                    {line}
                  </p>
                ));
              })()}
              
              {isLongContent && !isExpanded && (
                <div className="content-fade">
                  <button 
                    onClick={() => toggleExpand(draftId)}
                    className="show-more-btn"
                  >
                    显示更多...
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="panel-window drafts-panel">
      <div className="panel-header">
        <h3>📝 草稿内容</h3>
        {Object.keys(drafts).length > 0 && (
          <button onClick={onExportDrafts} className="export-btn">
            📥 导出
          </button>
        )}
      </div>
      <div className="panel-content">
        {Object.keys(drafts).length === 0 ? (
          <div className="empty-state small">
            <div className="empty-icon">📄</div>
            <h4>暂无草稿</h4>
            <p>AI生成的草稿内容将在这里显示</p>
          </div>
        ) : (
          <div className="drafts-list">
            {Object.entries(drafts)
              .sort(([,a], [,b]) => b.last_updated - a.last_updated)
              .map(([draftId, draft]) => 
                renderDraftCard(draftId, draft)
              )}
          </div>
        )}
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Image as ImageIcon, Trophy, Download, Edit3, Save, X } from 'lucide-react';

interface DisplayWindowProps {
  drafts: Record<string, any>;
  updateDraft: (draftId: string, content: string) => void;
  displayTab: 'drafts' | 'images' | 'results';
  setDisplayTab: (tab: 'drafts' | 'images' | 'results') => void;
  sessionId: string;
}

const DisplayWindow: React.FC<DisplayWindowProps> = ({
  drafts,
  updateDraft,
  displayTab,
  setDisplayTab,
  sessionId
}) => {
  const [editingDraft, setEditingDraft] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const startEditing = (draftId: string, content: string) => {
    setEditingDraft(draftId);
    setEditContent(content);
  };

  const saveEdit = () => {
    if (editingDraft) {
      updateDraft(editingDraft, editContent);
      setEditingDraft(null);
      setEditContent('');
    }
  };

  const cancelEdit = () => {
    setEditingDraft(null);
    setEditContent('');
  };

  const exportDrafts = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/drafts/${sessionId}/export`, {
        method: 'POST'
      });
      const result = await response.json();
      
      // 创建下载链接
      const blob = new Blob([result.export_content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `story_${sessionId}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export drafts:', error);
    }
  };

  return (
    <div className="display-window">
      {/* 标签页导航 */}
      <div className="tab-nav">
        <button
          className={`tab-button ${displayTab === 'drafts' ? 'active' : ''}`}
          onClick={() => setDisplayTab('drafts')}
        >
          <FileText size={18} />
          草稿
          {Object.keys(drafts).length > 0 && <span className="tab-badge">{Object.keys(drafts).length}</span>}
        </button>
        <button
          className={`tab-button ${displayTab === 'images' ? 'active' : ''}`}
          onClick={() => setDisplayTab('images')}
        >
          <ImageIcon size={18} />
          图像
        </button>
        <button
          className={`tab-button ${displayTab === 'results' ? 'active' : ''}`}
          onClick={() => setDisplayTab('results')}
        >
          <Trophy size={18} />
          成果
        </button>
      </div>

      {/* 内容区域 */}
      <div className="tab-content">
        <AnimatePresence mode="wait">
          {displayTab === 'drafts' && (
            <motion.div
              key="drafts"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="drafts-view"
            >
              <div className="section-header">
                <h3>📝 草稿内容</h3>
                {Object.keys(drafts).length > 0 && (
                  <button onClick={exportDrafts} className="export-btn">
                    <Download size={16} />
                    导出
                  </button>
                )}
              </div>

              {Object.keys(drafts).length === 0 ? (
                <div className="empty-state">
                  <FileText size={48} className="empty-icon" />
                  <h3>暂无草稿</h3>
                  <p>AI生成的草稿内容将在这里显示</p>
                </div>
              ) : (
                <div className="drafts-list">
                  {Object.entries(drafts).map(([draftId, draft]) => (
                    <motion.div
                      key={draftId}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="draft-card"
                    >
                      <div className="draft-header">
                        <h4 className="draft-title">{draftId.replace(/_/g, ' ')}</h4>
                        <div className="draft-meta">
                          <span className="word-count">{draft.content.length} 字符</span>
                          <span className={`update-badge ${draft.updated_by === 'user' ? 'user' : 'ai'}`}>
                            {draft.updated_by === 'user' ? '用户编辑' : 'AI生成'}
                          </span>
                          <button
                            onClick={() => startEditing(draftId, draft.content)}
                            className="edit-btn"
                            disabled={editingDraft === draftId}
                          >
                            <Edit3 size={14} />
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
                            />
                            <div className="edit-actions">
                              <button onClick={saveEdit} className="save-btn">
                                <Save size={14} />
                                保存
                              </button>
                              <button onClick={cancelEdit} className="cancel-btn">
                                <X size={14} />
                                取消
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="draft-text">
                            {draft.content.split('\n').map((line: string, index: number) => (
                              <p key={index}>{line}</p>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="draft-footer">
                        <span className="last-updated">
                          最后更新: {new Date(draft.last_updated).toLocaleString()}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {displayTab === 'images' && (
            <motion.div
              key="images"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="images-view"
            >
              <div className="section-header">
                <h3>🖼️ 图像画廊</h3>
              </div>
              
              <div className="empty-state">
                <ImageIcon size={48} className="empty-icon" />
                <h3>图像生成功能</h3>
                <p>即将推出图像生成功能，敬请期待</p>
              </div>
            </motion.div>
          )}

          {displayTab === 'results' && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="results-view"
            >
              <div className="section-header">
                <h3>🏆 创作成果</h3>
              </div>

              {Object.keys(drafts).length === 0 ? (
                <div className="empty-state">
                  <Trophy size={48} className="empty-icon" />
                  <h3>创作成果汇总</h3>
                  <p>完成的故事和创作成果将在这里展示</p>
                </div>
              ) : (
                <div className="results-summary">
                  <div className="stats-grid">
                    <div className="stat-card">
                      <div className="stat-number">{Object.keys(drafts).length}</div>
                      <div className="stat-label">草稿数量</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-number">
                        {Object.values(drafts).reduce((total: number, draft: any) => total + draft.content.length, 0)}
                      </div>
                      <div className="stat-label">总字符数</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-number">
                        {Object.values(drafts).filter((draft: any) => draft.updated_by === 'user').length}
                      </div>
                      <div className="stat-label">用户编辑</div>
                    </div>
                  </div>

                  <div className="final-story">
                    <h4>📖 完整故事预览</h4>
                    <div className="story-preview">
                      {Object.entries(drafts).map(([draftId, draft], index) => (
                        <div key={draftId} className="story-section">
                          <h5>{draftId.replace(/_/g, ' ')}</h5>
                          <p>{(draft as any).content.substring(0, 200)}...</p>
                          {index < Object.keys(drafts).length - 1 && <hr />}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default DisplayWindow;
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { AgendaSummary, AgendaTask } from '../types';
import { getTaskStatusIcon, getTaskStatusColor } from '../utils/formatUtils';
import './XMindMap.css'; // 引入思维导图专用样式

interface AgendaPanelProps {
  currentAgenda: AgendaSummary | null; // 更新为可空类型
}

export const AgendaPanel: React.FC<AgendaPanelProps> = ({ currentAgenda }) => {
  const [expandedBranches, setExpandedBranches] = useState<Set<string>>(new Set(['goals', 'in_progress', 'pending', 'completed']));
  
  // 画布拖拽相关状态
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  // 所有 Hooks 必须在组件顶层调用
  const toggleBranch = (branchId: string) => {
    const newExpanded = new Set(expandedBranches);
    if (newExpanded.has(branchId)) {
      newExpanded.delete(branchId);
    } else {
      newExpanded.add(branchId);
    }
    setExpandedBranches(newExpanded);
  };

  // 拖拽开始 - 简化版本
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return; // 只响应左键
    e.preventDefault();
    
    setIsDragging(true);
    setDragStart({
      x: e.clientX - canvasOffset.x,
      y: e.clientY - canvasOffset.y
    });
  }, [canvasOffset]);

  // 拖拽移动 - 简化版本
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const newOffset = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    };
    
    setCanvasOffset(newOffset);
  }, [isDragging, dragStart]);

  // 拖拽结束 - 添加延迟避免闪烁
  const handleMouseUp = useCallback(() => {
    // 延迟一小段时间再移除拖拽状态，避免CSS过渡闪烁
    setTimeout(() => {
      setIsDragging(false);
    }, 10);
  }, []);

  // 缩放功能
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.5, Math.min(2, scale * delta));
    
    // 计算缩放后的偏移调整
    const scaleChange = newScale / scale;
    const newOffsetX = centerX - (centerX - canvasOffset.x) * scaleChange;
    const newOffsetY = centerY - (centerY - canvasOffset.y) * scaleChange;
    
    setScale(newScale);
    setCanvasOffset({ x: newOffsetX, y: newOffsetY });
  }, [scale, canvasOffset]);

  // 重置视图
  const resetView = useCallback(() => {
    setCanvasOffset({ x: 0, y: 0 });
    setScale(1);
  }, []);

  // 居中视图
  const centerView = useCallback(() => {
    if (!containerRef.current || !canvasRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const canvasRect = canvasRef.current.getBoundingClientRect();
    
    const centerX = (containerRect.width - canvasRect.width * scale) / 2;
    const centerY = (containerRect.height - canvasRect.height * scale) / 2;
    
    setCanvasOffset({ x: centerX, y: centerY });
  }, [scale]);

  // 绑定事件监听器
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMoveGlobal = (e: MouseEvent) => handleMouseMove(e);
    const handleMouseUpGlobal = () => handleMouseUp();
    const handleWheelGlobal = (e: WheelEvent) => handleWheel(e);

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMoveGlobal);
      document.addEventListener('mouseup', handleMouseUpGlobal);
    }

    container.addEventListener('wheel', handleWheelGlobal, { passive: false });

    return () => {
      document.removeEventListener('mousemove', handleMouseMoveGlobal);
      document.removeEventListener('mouseup', handleMouseUpGlobal);
      container.removeEventListener('wheel', handleWheelGlobal);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleWheel]);

  // 早期返回：所有 Hooks 调用完成后再进行条件判断
  if (!currentAgenda || currentAgenda.total_tasks === 0) {
    return (
      <div className="panel-window agenda-panel xmind-panel">
        <div className="panel-header">
          <h3>🧠 任务思维导图</h3>
        </div>
        <div className="panel-content">
          <div className="empty-state small">
            <div className="empty-icon">🧠</div>
            <h4>思维导图准备中</h4>
            <p>创作任务将以思维导图形式展示</p>
          </div>
        </div>
      </div>
    );
  }

  // 渲染思维导图的单个节点
  const renderMapNode = (text: string, type: string, count?: number, isSubNode: boolean = false) => {
    let color = '#6366f1'; // 默认紫色
    
    switch (type) {
      case 'goals':
        color = '#f59e0b'; // 金色
        break;
      case 'in_progress':
        color = '#3b82f6'; // 蓝色
        break;
      case 'pending':
        color = '#6b7280'; // 灰色
        break;
      case 'completed':
        color = '#10b981'; // 绿色
        break;
    }
    
    return (
      <div 
        className={`xmind-node ${type} ${isSubNode ? 'sub-node' : 'main-node'}`}
        style={{'--node-color': color} as React.CSSProperties}
      >
        <div className="node-content">
          <span className="node-text">{text}</span>
          {count !== undefined && <span className="node-count">({count})</span>}
        </div>
      </div>
    );
  };
  
  // 渲染任务节点（第三层）
  const renderTaskNode = (task: AgendaTask, index: number, depth: number = 2) => {
    const statusColor = getTaskStatusColor(task.status);
    
    return (
      <div key={index} className={`xmind-node task-node depth-${depth}`} style={{ '--node-color': statusColor } as React.CSSProperties}>
        <div className="node-content">
          <span className="node-text">{task.description}</span>
        </div>
        
        {task.result && (
          <div className="node-result">
            <span className="result-text">{task.result}</span>
          </div>
        )}
        
        {/* 如果任务有子任务，渲染第三层 */}
        {task.subtasks && task.subtasks.length > 0 && (
          <div className="subtask-container">
            {task.subtasks.slice(0, 3).map((subtask, subIndex) => (
              <div key={subIndex} className="subtask-branch">
                <div className="subtask-branch-line"></div>
                {renderSubtaskNode(subtask, subIndex)}
              </div>
            ))}
            {task.subtasks.length > 3 && (
              <div className="more-subtasks-node">
                <div className="subtask-branch-line"></div>
                <div className="xmind-node more-node depth-3">
                  <div className="node-content">
                    <span className="node-text">还有 {task.subtasks.length - 3} 个子任务...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // 渲染子任务节点（第三层）
  const renderSubtaskNode = (subtask: any, index: number) => {
    const statusColor = getTaskStatusColor(subtask.status || 'pending');
    
    return (
      <div key={index} className="xmind-node subtask-node depth-3" style={{ '--node-color': statusColor } as React.CSSProperties}>
        <div className="node-content">
          <span className="node-text">{subtask.description || subtask.name}</span>
        </div>
        
        {subtask.result && (
          <div className="node-result">
            <span className="result-text">{subtask.result}</span>
          </div>
        )}
      </div>
    );
  };

  // 修改分支渲染函数，支持子任务展开
  const renderBranch = (title: string, type: string, tasks: AgendaTask[], count: number) => {
    const isExpanded = expandedBranches.has(type);
    
    return (
      <div key={type} className={`xmind-branch ${type}-branch depth-1`} style={{'--node-color': getTaskStatusColor(type)} as React.CSSProperties}>
        <div className="branch-line"></div>
        
        <div className="branch-main-node" onClick={() => toggleBranch(type)}>
          {renderMapNode(title, type, count, false)}
          <div className={`toggle-icon ${isExpanded ? 'expanded' : 'collapsed'}`}>
            {isExpanded ? '−' : '+'}
          </div>
        </div>
        
        {isExpanded && tasks.length > 0 && (
          <div className="branch-tasks depth-2">
            {tasks.slice(0, 5).map((task, index) => (
              <div key={index} className="task-branch">
                <div className="task-branch-line"></div>
                <div className="task-container">
                  <div className="task-main-node" onClick={() => toggleTaskExpansion(task.id || `${type}-${index}`)}>
                    {renderTaskNode(task, index, 2)}
                    {task.subtasks && task.subtasks.length > 0 && (
                      <div className={`task-toggle-icon ${expandedBranches.has(`task-${task.id || `${type}-${index}`}`) ? 'expanded' : 'collapsed'}`}>
                        {expandedBranches.has(`task-${task.id || `${type}-${index}`}`) ? '−' : '+'}
                      </div>
                    )}
                  </div>
                  
                  {/* 第三层：子任务 */}
                  {expandedBranches.has(`task-${task.id || `${type}-${index}`}`) && task.subtasks && task.subtasks.length > 0 && (
                    <div className="subtask-list depth-3">
                      {task.subtasks.slice(0, 3).map((subtask, subIndex) => (
                        <div key={subIndex} className="subtask-branch">
                          <div className="subtask-branch-line"></div>
                          {renderSubtaskNode(subtask, subIndex)}
                        </div>
                      ))}
                      {task.subtasks.length > 3 && (
                        <div className="more-subtasks-node">
                          <div className="subtask-branch-line"></div>
                          <div className="xmind-node more-node depth-3">
                            <div className="node-content">
                              <span className="node-text">还有 {task.subtasks.length - 3} 个子任务...</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {tasks.length > 5 && (
              <div className="more-tasks-node">
                <div className="task-branch-line"></div>
                <div className="xmind-node more-node depth-2">
                  <div className="node-content">
                    <span className="node-text">还有 {tasks.length - 5} 个任务...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // 添加任务展开控制函数
  const toggleTaskExpansion = (taskId: string) => {
    const branchKey = `task-${taskId}`;
    const newExpanded = new Set(expandedBranches);
    if (newExpanded.has(branchKey)) {
      newExpanded.delete(branchKey);
    } else {
      newExpanded.add(branchKey);
    }
    setExpandedBranches(newExpanded);
  };

  const centerTitle = "任务进度";

  return (
    <div className="panel-window agenda-panel xmind-panel">
      <div className="panel-header">
        <div className="header-left">
          <h3>🧠 任务思维导图</h3>
          <div className="agenda-stats">
            <span className="stats-item">完成度 {Math.round(currentAgenda.completion_rate)}%</span>
          </div>
        </div>
        
        {/* 控制按钮 */}
        <div className="mindmap-controls">
          <button 
            className="control-btn" 
            onClick={centerView}
            title="居中视图"
          >
            🎯
          </button>
          <button 
            className="control-btn" 
            onClick={resetView}
            title="重置视图"
          >
            🔄
          </button>
          <div className="zoom-indicator">
            {Math.round(scale * 100)}%
          </div>
        </div>
      </div>
      
      <div className="panel-content xmind-content">
        <div 
          className={`xmind-viewport ${isDragging ? 'dragging' : ''}`}
          ref={containerRef}
          onMouseDown={handleMouseDown}
          style={{
            cursor: isDragging ? 'grabbing' : 'grab'
          }}
        >
          <div 
            className="xmind-canvas"
            ref={canvasRef}
            style={{
              transform: `translate(${canvasOffset.x}px, ${canvasOffset.y}px) scale(${scale})`,
              transformOrigin: '0 0'
            }}
          >
            <div className="xmind-container">
              {/* 中心节点 */}
              <div className="xmind-center">
                <div className="center-node">
                  <div className="center-content">
                    <span className="center-icon">📖</span>
                    <span className="center-title">{centerTitle}</span>
                  </div>
                  <div className="center-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{width: `${currentAgenda.completion_rate}%`}}
                      ></div>
                    </div>
                    <span className="progress-text">{Math.round(currentAgenda.completion_rate)}%</span>
                  </div>
                </div>
                
                {/* 分支容器 */}
                <div className="xmind-branches">
                  {/* 核心目标分支 */}
                  {renderBranch(
                    '核心目标', 
                    'goals', 
                    currentAgenda.tasks_by_status?.goals || [], 
                    currentAgenda.goals_count || 0
                  )}
                  
                  {/* 进行中分支 */}
                  {renderBranch(
                    '进行中', 
                    'in_progress', 
                    currentAgenda.tasks_by_status?.in_progress || [], 
                    currentAgenda.in_progress_count || 0
                  )}
                  
                  {/* 待处理分支 */}
                  {renderBranch(
                    '待处理', 
                    'pending', 
                    currentAgenda.tasks_by_status?.pending || [], 
                    currentAgenda.pending_count || 0
                  )}
                  
                  {/* 已完成分支 */}
                  {renderBranch(
                    '已完成', 
                    'completed', 
                    currentAgenda.tasks_by_status?.completed || [], 
                    currentAgenda.completed_count || 0
                  )}
                </div>
              </div>
            </div>
          </div>
          
          {/* 操作提示 */}
          <div className="viewport-hint">
            <span>🖱️ 拖拽移动 | 🔍 滚轮缩放</span>
          </div>
        </div>
      </div>
    </div>
  );
};
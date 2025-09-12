import React, { useCallback, useEffect } from 'react';

interface InputAreaProps {
  currentMessage: string;
  setCurrentMessage: (message: string) => void;
  isProcessing: boolean;
  onSendMessage: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  messageInputRef: React.RefObject<HTMLTextAreaElement | null>;
}

export const InputArea: React.FC<InputAreaProps> = ({
  currentMessage,
  setCurrentMessage,
  isProcessing,
  onSendMessage,
  onKeyPress,
  messageInputRef
}) => {
  
  // 🎯 自动调整文本域高度
  const adjustTextareaHeight = useCallback(() => {
    const textarea = messageInputRef.current;
    if (!textarea) return;
    
    // 重置高度以获得正确的滚动高度
    textarea.style.height = 'auto';
    
    // 计算内容所需的高度
    const scrollHeight = textarea.scrollHeight;
    
    // 设置动态高度，限制最大高度
    const minHeight = 48; // 最小高度 (约2行)
    const maxHeight = 200; // 最大高度 (约8-10行)
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    
    textarea.style.height = `${newHeight}px`;
    
    // 如果内容超出最大高度，显示滚动条
    textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
  }, [messageInputRef]);

  // 🎯 监听内容变化并调整高度
  useEffect(() => {
    adjustTextareaHeight();
  }, [currentMessage, adjustTextareaHeight]);

  // 🎯 处理输入变化
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCurrentMessage(e.target.value);
    // 延迟调整高度，确保内容已更新
    setTimeout(adjustTextareaHeight, 0);
  }, [setCurrentMessage, adjustTextareaHeight]);

  // 🎯 处理按键事件 - 移除重复的发送逻辑
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // 🎯 只处理高度调整，发送逻辑完全交给父组件
    if (e.key === 'Enter' && !e.shiftKey) {
      // 不在这里阻止默认行为，让父组件处理
    }
    
    // 调用父组件的按键处理逻辑
    onKeyPress(e);
  }, [onKeyPress]);

  return (
    <div className="input-area">
      <div className="input-container">
        <textarea
          ref={messageInputRef}
          value={currentMessage}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown} // 🎯 改为 onKeyDown
          placeholder="请输入您的需求... Shift+Enter换行，Enter发送"
          className="message-input auto-resize"
          disabled={isProcessing}
          rows={1}
          style={{
            resize: 'none',
            minHeight: '48px',
            maxHeight: '200px',
          }}
        />
        <button
          onClick={onSendMessage}
          disabled={isProcessing || !currentMessage.trim()}
          className="send-button"
        >
          {isProcessing ? '⏳' : '📤'}
        </button>
      </div>
    </div>
  );
};

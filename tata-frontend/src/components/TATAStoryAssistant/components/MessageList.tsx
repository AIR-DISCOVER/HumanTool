import React, { useEffect } from 'react';
import { Message } from '../types';
import { MessageCard } from './MessageCard';
import StreamingIndicator from '../../StreamingIndicator';

interface MessageListProps {
  messages: Message[];
  chatEndRef: React.RefObject<HTMLDivElement | null>;
  isConfigured?: boolean;
  isProcessing?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, chatEndRef, isConfigured = false, isProcessing = false }) => {
  // 当消息数组发生变化时，自动滚动到底部
  useEffect(() => {
    const scrollToBottom = () => {
      if (chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ 
          behavior: 'smooth',
          block: 'end'
        });
      }
    };

    // 延迟滚动，确保DOM已更新
    const timeoutId = setTimeout(scrollToBottom, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, chatEndRef]);

  if (messages.length === 0) {
    // 如果已配置且正在处理，显示加载状态
    if (isConfigured && isProcessing) {
      return (
        <div className="loading-state">
          <StreamingIndicator />
          <h3>正在为您准备创作环境...</h3>
          <p>请稍等，我们马上开始！</p>
        </div>
      );
    }
    
    // 否则显示默认的空状态
    return (
      <div className="empty-state">
        <div className="empty-icon">💬</div>
        <h3>开始您的协作之旅</h3>
        <p>请告诉我您想进行什么任务？</p>
        <p>我将协助您完成整个创作过程~</p>
      </div>
    );
  }

  return (
    <div className="chat-messages">
      {messages.map((message) => (
        <MessageCard key={message.id} message={message} />
      ))}
      <div ref={chatEndRef} className="chat-end-marker" />
    </div>
  );
};

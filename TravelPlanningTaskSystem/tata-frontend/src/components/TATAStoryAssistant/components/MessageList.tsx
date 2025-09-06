import React, { useEffect } from 'react';
import { Message } from '../types';
import { MessageCard } from './MessageCard';

interface MessageListProps {
  messages: Message[];
  chatEndRef: React.RefObject<HTMLDivElement | null>;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, chatEndRef }) => {
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

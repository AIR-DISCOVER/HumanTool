import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Message, ThinkingStep, ToolCall, DraftContent, AgendaSummary } from './types';
import { useStreamHandler } from './hooks/useStreamHandler';
import { useChatManager } from './hooks/useChatManager';

// 组件导入
import { StatusBar } from './components/StatusBar';
import { MessageList } from './components/MessageList';
import { InputArea } from './components/InputArea';
import { AccountSelector } from './components/AccountSelector';
import ConfigModal from '../ConfigModal';

import '../TATAStoryAssistant.css';

interface TATAStoryAssistantProps {
  initialMessages?: any[];
  initialSessionId?: string | null;
  currentConfig?: {user_profile: string; writing_query: string} | null;
}

export function TATAStoryAssistant({ 
  initialMessages = [], 
  initialSessionId = null,
  currentConfig: externalConfig = null
}: TATAStoryAssistantProps) {
  // 基础状态
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [sessionId, setSessionId] = useState<string>(initialSessionId || `session_${Date.now()}`);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  
  // 账号选择相关状态
  const [currentAccount, setCurrentAccount] = useState(externalConfig?.user_profile || 'user_main'); // 默认账号
  const [currentWritingCategory, setCurrentWritingCategory] = useState('supernatural'); // 默认超自然力量
  const [showAccountSelector, setShowAccountSelector] = useState(false);
  
  // 配置弹窗相关状态
  const [showConfigModal, setShowConfigModal] = useState(!externalConfig); // 如果有外部配置则不显示弹窗
  const [isConfigured, setIsConfigured] = useState(!!externalConfig); // 如果有外部配置则已配置
  const [currentConfig, setCurrentConfig] = useState<{user_profile: string; writing_query: string} | null>(externalConfig);
  
  // 数据状态
  const [currentThinkingSteps, setCurrentThinkingSteps] = useState<ThinkingStep[]>([]);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [currentAgenda, setCurrentAgenda] = useState<AgendaSummary | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [currentDrafts, setCurrentDrafts] = useState<DraftContent[]>([]);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);
  const [showDebug, setShowDebug] = useState(false);
  
  // refs
  const chatEndRef = useRef<HTMLDivElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);
  
  // 使用自定义hooks
  const { handleStreamResponse } = useStreamHandler({
    setMessages,
    setCurrentThinkingSteps,
    setCurrentToolCalls,
    setCurrentAgenda,
    setIsProcessing,
    setDebugInfo,
    currentThinkingSteps,
    currentToolCalls,
    messageInputRef,
    chatEndRef
  });
  
  const { 
    handleSendMessage
  } = useChatManager({
    sessionId,
    messages,
    setMessages,
    currentMessage,
    setCurrentMessage,
    isProcessing,
    setIsProcessing,
    setCurrentThinkingSteps,
    setCurrentToolCalls,
    setDebugInfo,
    handleStreamResponse,
    setConnectionStatus,
    currentAccount
  });
  
  // 处理配置提交
  const handleConfigSubmit = useCallback((config: {user_profile: string; writing_query: string}) => {
    // 从writing_query中提取写作类别
    let writingCategory = 'supernatural';
    if (config.writing_query.includes('人类曾经拥有强大的魔法力量')) {
      writingCategory = 'supernatural';
    } else if (config.writing_query.includes('科学发现了一种药物，可以阻止所有衰老的影响')) {
      writingCategory = 'sideeffects';
    }
    
    setCurrentConfig(config);
    setCurrentAccount(config.user_profile);
    setCurrentWritingCategory(writingCategory);
    setIsConfigured(true);
    setShowConfigModal(false);
    console.log('配置已设置:', config, '写作类别:', writingCategory);
  }, []);

  // 自动发送配置初始化请求
  useEffect(() => {
    const initializeChat = async () => {
      if (messages.length === 0 && !isProcessing && isConfigured && currentConfig) {
        // 构造配置初始化消息，使用JSON格式让后端识别为配置初始化请求
        const configMessage = JSON.stringify({
          user_profile: currentConfig.user_profile,
          writing_request: currentConfig.writing_query,
          writing_category: currentWritingCategory
        });

        // 发送配置初始化请求
        try {
          const apiBaseURL = process.env.REACT_APP_API_URL || '/api';
          const response = await fetch(`${apiBaseURL}/chat/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'text/event-stream',
            },
            body: JSON.stringify({
              message: configMessage,
              session_id: sessionId,
              user_id: currentConfig.user_profile
            })
          });

          if (response.ok && response.body) {
            const aiMessageId = `ai_init_${Date.now()}`;
            const initMessage = {
              id: aiMessageId,
              type: 'ai' as const,
              content: '正在初始化...',
              timestamp: Date.now(),
              thinking_steps: [],
              tool_calls: [],
              is_streaming: true
            };
            setMessages([initMessage]);
            setIsProcessing(true);
            
            await handleStreamResponse(response, aiMessageId);
          }
        } catch (error) {
          console.error('自动初始化失败:', error);
        }
      }
    };

    initializeChat();
  }, [isConfigured, currentConfig, currentWritingCategory, messages.length, isProcessing, sessionId, handleStreamResponse]);

  // 监听外部配置变化
  useEffect(() => {
    if (externalConfig) {
      setCurrentConfig(externalConfig);
      // 🎯 关键修复: if (externalConfig.user_profile && externalConfig.user_profile !== currentAccount) {
      if (externalConfig.user_profile && externalConfig.user_profile !== currentAccount) {
        setCurrentAccount(externalConfig.user_profile);
        setDebugInfo(prev => [...prev, `从ConfigModal更新账号: ${externalConfig.user_profile}`]);
        console.log('从ConfigModal更新账号:', externalConfig.user_profile);
      }
    }
  }, [externalConfig, currentAccount, setDebugInfo]);

  // 自动滚动到底部
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, currentThinkingSteps, currentToolCalls]);
  
  // 账号切换处理
  const handleAccountChange = useCallback((newAccount: string, writingCategory?: string) => {
    setCurrentAccount(newAccount);
    if (writingCategory) {
      setCurrentWritingCategory(writingCategory);
    }
    setShowAccountSelector(false);
    
    // 切换账号时清空聊天历史，重新初始化
    setMessages([]);
    setCurrentThinkingSteps([]);
    setCurrentToolCalls([]);
    setCurrentAgenda(null);
    setCurrentDrafts([]);
    
    console.log('切换到账号:', newAccount, '创作类别:', writingCategory);
  }, []);
  
  // 处理按键事件
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);
  
  return (
    <div className="tata-container">
      {/* 调试信息面板 - 开发时使用 */}
      {showDebug && process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
        <div style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          width: '300px',
          maxHeight: '400px',
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontSize: '12px',
          overflow: 'auto',
          zIndex: 1000
        }}>
          {/* 添加关闭按钮 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
            <span style={{ fontWeight: 'bold' }}>🔍 调试信息:</span>
            <button 
              onClick={() => setShowDebug(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              ×
            </button>
          </div>
          {debugInfo.map((info, index) => (
            <div key={index} style={{ marginBottom: '5px', borderBottom: '1px solid #333', paddingBottom: '5px' }}>
              {info}
            </div>
          ))}
        </div>
      )}
      
      <StatusBar 
        sessionId={sessionId}
        connectionStatus={connectionStatus}
        messageCount={messages.length}
        currentAccount={currentAccount}
        onSettingsClick={() => setShowAccountSelector(true)}
      />

      {/* 初始配置弹窗 */}
      <ConfigModal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSubmit={handleConfigSubmit}
      />

      {/* 账号选择弹窗 */}
      <AccountSelector
        isOpen={showAccountSelector}
        onClose={() => setShowAccountSelector(false)}
        currentAccount={currentAccount}
        currentWritingCategory={currentWritingCategory}
        onAccountChange={handleAccountChange}
      />

      {/* 主内容区域 - 全屏聊天面板 */}
      <div className="main-content">
        {/* 聊天面板 */}
        <div className="chat-panel full-width">
          <div className="chat-window">
            <div className="panel-header">
              <h3>💬 对话交流 Chat</h3>
            </div>
            <div className="panel-content">
              <MessageList 
                messages={messages} 
                chatEndRef={chatEndRef}
                isConfigured={isConfigured}
                isProcessing={isProcessing}
              />
              <InputArea
                currentMessage={currentMessage}
                setCurrentMessage={setCurrentMessage}
                isProcessing={isProcessing}
                onSendMessage={handleSendMessage}
                onKeyPress={handleKeyPress}
                messageInputRef={messageInputRef}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TATAStoryAssistant;
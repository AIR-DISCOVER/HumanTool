import { useCallback } from 'react';
import { Message, ThinkingStep, ToolCall } from '../types';
import { generateSessionId } from '../utils/messageUtils';

interface UseChatManagerProps {
  sessionId: string;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  currentMessage: string;
  setCurrentMessage: React.Dispatch<React.SetStateAction<string>>;
  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  setCurrentThinkingSteps: React.Dispatch<React.SetStateAction<ThinkingStep[]>>;
  setCurrentToolCalls: React.Dispatch<React.SetStateAction<ToolCall[]>>;
  setDebugInfo: React.Dispatch<React.SetStateAction<string[]>>;
  handleStreamResponse: (response: Response, aiMessageId: string) => Promise<void>;
  // 🎯 添加连接状态setter
  setConnectionStatus?: React.Dispatch<React.SetStateAction<'connected' | 'disconnected' | 'connecting'>>;
  // 🎯 添加当前账号
  currentAccount?: string;
}

export const useChatManager = ({
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
  currentAccount = 'user_main' // 🎯 默认账号
}: UseChatManagerProps) => {

  const handleSendMessage = useCallback(async () => {
    if (!currentMessage.trim() || isProcessing) return;

    const messageToSend = currentMessage.trim();
    setCurrentMessage('');
    setIsProcessing(true);

    // 🎯 精确修复：设置连接状态
    setConnectionStatus?.('connecting');

    // 添加用户消息
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: messageToSend,
      timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);

    // 添加AI消息占位符
    const aiMessageId = `ai_${Date.now()}`;
    const streamingMessage: Message = {
      id: aiMessageId,
      type: 'ai',
      content: '',
      timestamp: Date.now(),
      thinking_steps: [],
      tool_calls: [],
      is_streaming: true
    };
    setMessages(prev => [...prev, streamingMessage]);

    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || '/api';
      const apiURL = `${apiBaseURL}/chat`;
      
      console.log("🌐 [DEBUG] API URL:", apiURL);
      setDebugInfo(prev => [...prev, `🌐 发送请求到: ${apiURL}`]);
      
      const requestData = {
        message: messageToSend,
        session_id: sessionId,
        user_id: currentAccount, // 🎯 使用当前选择的账号作为user_id
        stream: true,
        // 🎯 添加额外的用户上下文信息
        user_context: {
          account_type: currentAccount,
          session_start: Date.now(),
          message_count: messages.length
        }
      };
      
      console.log("📦 [DEBUG] 请求数据:", requestData);
      setDebugInfo(prev => [...prev, `📦 请求数据: ${JSON.stringify(requestData)}`]);
      setDebugInfo(prev => [...prev, `👤 使用账号: ${currentAccount}`]); // 🎯 调试信息

      console.log("📡 [DEBUG] 开始发送fetch请求");
      const response = await fetch(apiURL, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify(requestData)
      });

      console.log("📡 [DEBUG] Fetch响应接收:", response.status, response.statusText);
      console.log("📄 [DEBUG] 响应头:", {
        'content-type': response.headers.get('content-type'),
        'transfer-encoding': response.headers.get('transfer-encoding'),
        'connection': response.headers.get('connection')
      });

      setDebugInfo(prev => [...prev, `📡 响应状态: ${response.status} ${response.statusText}`]);
      setDebugInfo(prev => [...prev, `📄 响应头: ${response.headers.get('content-type')}`]);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ [DEBUG] HTTP错误响应:", errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      if (!response.body) {
        console.error("❌ [DEBUG] 响应没有body");
        throw new Error('No response body');
      }

      console.log("✅ [DEBUG] 响应验证通过，开始处理流");
      setDebugInfo(prev => [...prev, `🌊 开始处理流式响应`]);
      await handleStreamResponse(response, aiMessageId);

      // 🎯 请求成功后设置为已连接
      setConnectionStatus?.('connected');
      
    } catch (error) {
      // 🎯 请求失败后设置为未连接
      setConnectionStatus?.('disconnected');
      
      console.error('❌ [DEBUG] Chat error:', error);
      console.error('❌ [DEBUG] Error stack:', error instanceof Error ? error.stack : 'No stack');
      setDebugInfo(prev => [...prev, `❌ 错误: ${error}`]);
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        type: 'error',
        content: `发送消息时出错: ${error instanceof Error ? error.message : '未知错误'}。请检查后端服务器是否在 http://localhost:8000 运行。`,
        timestamp: Date.now()
      };
      setMessages(prev => prev.slice(0, -1).concat([errorMessage]));
    } finally {
      setIsProcessing(false);
      setDebugInfo(prev => [...prev, `✅ 请求处理完成`]);
    }
  }, [currentMessage, isProcessing, sessionId, handleStreamResponse, setMessages, setCurrentMessage, setIsProcessing, setCurrentThinkingSteps, setCurrentToolCalls, setDebugInfo, setConnectionStatus, currentAccount, messages.length]); // 🎯 添加依赖

  return {
    handleSendMessage
  };
};

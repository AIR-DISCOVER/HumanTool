import React, { useState } from 'react';
import ConfigModal from './components/ConfigModal';
import TATAStoryAssistant from './components/TATAStoryAssistant/TATAStoryAssistant';
import './App.css';

function App() {
  const [showConfigModal, setShowConfigModal] = useState(true);
  const [messages, setMessages] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentConfig, setCurrentConfig] = useState<{user_profile: string; travel_query: string} | null>(null);

  const handleConfigSubmit = async (config: { user_profile: string; travel_query: string }) => {
    try {
      // 保存配置信息
      setCurrentConfig(config);
      
      const configMessage = JSON.stringify(config);
      
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          message: configMessage,
          session_id: null,
          user_id: config.user_profile
        })
      });

      if (response.ok && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let configResult = '';

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();
                if (data === '[DONE]') {
                  break;
                }

                try {
                  const parsed = JSON.parse(data);
                  if (parsed.type === 'final') {
                    configResult = parsed.content;
                    setCurrentSessionId(parsed.metadata?.session_id);
                  }
                } catch (e) {
                  // 忽略解析错误
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }

        if (configResult) {
          const newMessage = {
            id: Date.now(),
            type: 'ai' as const,
            content: configResult,
            timestamp: new Date().toISOString(),
            isMarkdown: true
          };
          
          setMessages([newMessage]);
          setShowConfigModal(false);
        }
      }
    } catch (error) {
      console.error('配置初始化失败:', error);
      throw error;
    }
  };

  return (
    <div className="App">
      <ConfigModal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSubmit={handleConfigSubmit}
      />
      
      <TATAStoryAssistant 
        initialMessages={messages}
        initialSessionId={currentSessionId}
        currentConfig={currentConfig}
      />
    </div>
  );
}

export default App;

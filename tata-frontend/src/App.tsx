import React, { useState } from 'react';
import TATAStoryAssistant from './components/TATAStoryAssistant/TATAStoryAssistant';
import './App.css';

function App() {
  const [messages, setMessages] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  return (
    <div className="App">
      <TATAStoryAssistant 
        initialMessages={messages}
        initialSessionId={currentSessionId}
        currentConfig={null}
      />
    </div>
  );
}

export default App;

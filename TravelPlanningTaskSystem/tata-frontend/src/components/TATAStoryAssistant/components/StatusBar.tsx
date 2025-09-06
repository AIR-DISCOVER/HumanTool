import React from 'react';
import { Settings, Wifi, WifiOff, Loader } from 'lucide-react';

interface StatusBarProps {
  sessionId: string;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  messageCount: number;
  currentAccount?: string; // 🎯 新增当前账号
  onSettingsClick?: () => void; // 🎯 新增设置按钮点击处理
}

export const StatusBar: React.FC<StatusBarProps> = ({ 
  sessionId, 
  connectionStatus, 
  messageCount,
  currentAccount = 'user_main', // 🎯 默认账号
  onSettingsClick 
}) => {
  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi size={16} />;
      case 'connecting':
        return <Loader size={16} className="spinning" />;
      case 'disconnected':
      default:
        return <WifiOff size={16} />;
    }
  };

  const getConnectionText = () => {
    switch (connectionStatus) {
      case 'connected':
        return '已连接';
      case 'connecting':
        return '连接中';
      case 'disconnected':
      default:
        return '未连接';
    }
  };

  // 🎯 获取账号显示名称
  const getAccountDisplayName = (accountId: string) => {
    const accountNames: Record<string, string> = {
      'user_novice': '新手创作者',
      'user_intermediate': '进阶创作者',
      'user_expert': '专业创作者',
      'user_main': '默认用户'
    };
    return accountNames[accountId] || accountId;
  };

  return (
    <div className="status-bar">
      <div className="status-left">
        <div className={`connection-status ${connectionStatus}`}>
          {getConnectionIcon()}
          <span>{getConnectionText()}</span>
        </div>
        
        {/* 🎯 当前账号显示 */}
        <div className="current-account-info">
          <span className="account-label">当前账号:</span>
          <span className="account-name">{getAccountDisplayName(currentAccount)}</span>
        </div>
      </div>
      
      <div className="status-right">
        <div className="status-info">
          <span>会话: {sessionId.slice(-8)}</span>
          <span>消息: {messageCount}</span>
        </div>
        
        {/* 🎯 设置按钮 */}
        <button 
          className="settings-btn"
          onClick={onSettingsClick}
          title="账号设置"
        >
          <Settings size={16} />
          <span>设置</span>
        </button>
      </div>
    </div>
  );
};

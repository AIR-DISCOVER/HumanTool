import React, { useState, useEffect } from 'react';
import { X, Settings, RefreshCw, Check } from 'lucide-react';

interface Account {
  id: string;
  name: string;
  description?: string;
  experiment_group?: string;
}

interface AccountSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  currentAccount: string;
  onAccountChange: (accountId: string) => void;
}

// 🎯 移除硬编码账号列表 - 完全从数据库获取
const DEFAULT_ACCOUNTS: Account[] = [];

export const AccountSelector: React.FC<AccountSelectorProps> = ({
  isOpen,
  onClose,
  currentAccount,
  onAccountChange
}) => {
  const [selectedAccount, setSelectedAccount] = useState(currentAccount);
  const [accounts, setAccounts] = useState<Account[]>(DEFAULT_ACCOUNTS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 🎯 从数据库加载用户列表
  const loadAccountsFromDatabase = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseURL}/api/users/accounts`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📊 API返回的账号数据:', data);
        
        if (data.accounts && Array.isArray(data.accounts)) {
          setAccounts(data.accounts);
          console.log(`✅ 成功加载 ${data.accounts.length} 个账号`);
        } else {
          console.warn('数据库返回格式异常，使用默认账号列表');
          setError('数据格式异常，使用默认账号列表');
        }
      } else {
        console.warn(`API请求失败: ${response.status}`, await response.text());
        setError(`服务器错误 (${response.status})，使用默认账号列表`);
      }
    } catch (error) {
      console.warn('加载账号列表失败，使用默认配置:', error);
      setError('无法连接到服务器，显示默认账号列表');
    } finally {
      setIsLoading(false);
    }
  };

  // 🎯 向服务器发送账号选择
  const saveAccountSelection = async (accountId: string) => {
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseURL}/api/users/select-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          timestamp: Date.now(),
          session_context: {
            previous_account: currentAccount,
            selection_time: new Date().toISOString()
          }
        })
      });

      if (response.ok) {
        console.log('✅ 账号选择已保存到服务器');
      } else {
        console.error('保存账号选择失败:', response.status);
      }
    } catch (error) {
      console.error('保存账号选择时出错:', error);
    }
  };

  // 组件打开时加载账号列表
  useEffect(() => {
    if (isOpen) {
      loadAccountsFromDatabase();
    }
  }, [isOpen]);

  const handleConfirm = async () => {
    if (selectedAccount !== currentAccount) {
      // 先保存到服务器
      await saveAccountSelection(selectedAccount);
      // 然后通知父组件
      onAccountChange(selectedAccount);
    }
    onClose();
  };

  const handleRefresh = () => {
    loadAccountsFromDatabase();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content account-selector-modal">
        <div className="modal-header">
          <div className="modal-title-section">
            <Settings size={20} className="modal-icon" />
            <h3>🧪 选择账号</h3>
          </div>
          <div className="modal-header-actions">
            <button 
              onClick={handleRefresh} 
              className="refresh-button"
              disabled={isLoading}
              title="刷新账号列表"
            >
              <RefreshCw size={16} className={isLoading ? 'spinning' : ''} />
            </button>
            <button onClick={onClose} className="close-button">
              <X size={20} />
            </button>
          </div>
        </div>
        
        <div className="modal-body">
          <p className="account-selector-description">
            请选择您的账号：
          </p>

          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
            </div>
          )}
          
          {isLoading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>正在加载账号列表...</span>
            </div>
          ) : (
            <div className="accounts-list">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className={`account-card simple ${selectedAccount === account.id ? 'selected' : ''}`}
                  onClick={() => setSelectedAccount(account.id)}
                >
                  <div className="account-info">
                    <div className="account-header">
                      <div className="account-name">{account.name}</div>
                      {account.experiment_group && (
                        <span className="experiment-group">组别: {account.experiment_group}</span>
                      )}
                    </div>
                    {account.description && (
                      <div className="account-description">{account.description}</div>
                    )}
                  </div>
                  <div className="account-selector-check">
                    {selectedAccount === account.id && <Check size={18} />}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button onClick={onClose} className="cancel-button">
            取消
          </button>
          <button 
            onClick={handleConfirm} 
            className="confirm-button"
            disabled={selectedAccount === currentAccount || isLoading}
          >
            {selectedAccount === currentAccount ? '当前账号' : '确认选择'}
          </button>
        </div>
      </div>
    </div>
  );
};
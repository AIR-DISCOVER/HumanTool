import React, { useState, useEffect } from 'react';
import { X, Settings, RefreshCw, Check } from 'lucide-react';

interface Account {
  id: string;
  name: string;
  description?: string;
  experiment_group?: string;
}

interface WritingCategory {
  id: string;
  name: string;
  description: string;
}

interface AccountSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  currentAccount: string;
  currentWritingCategory?: string;
  onAccountChange: (accountId: string, writingCategory?: string) => void;
}

// 🎯 移除硬编码账号列表 - 完全从数据库获取
const DEFAULT_ACCOUNTS: Account[] = [];

// 创作类别配置
const WRITING_CATEGORIES: WritingCategory[] = [
  {
    id: 'supernatural',
    name: '超自然力量',
    description: '人类曾经拥有强大的魔法力量。但随着地球上超过70亿人，魔力已经分散得太薄，无法产生任何影响。当敌对的外星人将人类减少到微不足道的程度时，幸存者发现一种古老的力量开始再次觉醒。'
  },
  {
    id: 'sideeffects',
    name: '副作用',
    description: '当你28岁时，科学发现了一种药物，可以阻止所有衰老的影响，实现永生。你的政府决定将该药物提供给所有26岁以下的公民，但你和其余的「迷失的一代」被认为风险过高。当你85岁时，副作用终于被发现。'
  }
];

export const AccountSelector: React.FC<AccountSelectorProps> = ({
  isOpen,
  onClose,
  currentAccount,
  currentWritingCategory = 'supernatural',
  onAccountChange
}) => {
  const [selectedAccount, setSelectedAccount] = useState(currentAccount);
  const [selectedCategory, setSelectedCategory] = useState<string>(currentWritingCategory);
  const [accounts, setAccounts] = useState<Account[]>(DEFAULT_ACCOUNTS);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 🎯 从数据库加载用户列表
  const loadAccountsFromDatabase = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiBaseURL}/users/accounts`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📊 API返回的账号数据:', data);
        
        if (data.accounts && Array.isArray(data.accounts)) {
          if (data.accounts.length === 0) {
            // 数据库为空，使用默认用户
            const defaultAccount = [
              { id: 'user_main', name: '通用写作者' }
            ];
            setAccounts(defaultAccount);
            console.warn('📝 数据库中没有用户账号，使用默认通用用户');
            setError('数据库为空，显示默认用户（建议添加更多用户档案）');
          } else {
            setAccounts(data.accounts);
            console.log(`✅ 成功加载 ${data.accounts.length} 个账号`);
          }
        } else {
          console.warn('数据库返回格式异常，使用默认用户');
          setError('数据库返回格式异常，使用默认用户');
          const defaultAccount = [
            { id: 'user_main', name: '通用写作者' }
          ];
          setAccounts(defaultAccount);
        }
      } else {
        console.warn(`API请求失败: ${response.status}`, await response.text());
        setError(`服务器错误 (${response.status})，使用默认用户`);
        const defaultAccount = [
          { id: 'user_main', name: '通用写作者' }
        ];
        setAccounts(defaultAccount);
      }
    } catch (error) {
      console.warn('加载账号列表失败:', error);
      setError('无法连接到服务器，使用默认用户');
      const defaultAccount = [
        { id: 'user_main', name: '通用写作者' }
      ];
      setAccounts(defaultAccount);
    } finally {
      setIsLoading(false);
    }
  };

  // 🎯 向服务器发送账号选择
  const saveAccountSelection = async (accountId: string) => {
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiBaseURL}/users/select-account`, {
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

  // 同步外部传入的当前值
  useEffect(() => {
    setSelectedAccount(currentAccount);
    setSelectedCategory(currentWritingCategory);
  }, [currentAccount, currentWritingCategory]);

  const handleConfirm = async () => {
    if (selectedAccount !== currentAccount) {
      // 先保存到服务器
      await saveAccountSelection(selectedAccount);
      // 然后通知父组件，包含创作类别
      onAccountChange(selectedAccount, selectedCategory);
    } else {
      // 即使账号没变，也要传递类别信息
      onAccountChange(selectedAccount, selectedCategory);
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
            请选择您的账号和创作类别：
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
            <>
              {/* 用户账号选择 */}
              <div className="selection-section">
                <h4>🧪 选择用户档案</h4>
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
              </div>

              {/* 创作类别选择 */}
              <div className="selection-section">
                <h4>✍️ 选择创作类别</h4>
                <div className="categories-list">
                  {WRITING_CATEGORIES.map((category) => (
                    <div
                      key={category.id}
                      className={`category-card ${selectedCategory === category.id ? 'selected' : ''}`}
                      onClick={() => setSelectedCategory(category.id)}
                    >
                      <div className="category-info">
                        <div className="category-name">{category.name}</div>
                      </div>
                      <div className="category-selector-check">
                        {selectedCategory === category.id && <Check size={18} />}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
        
        <div className="modal-footer">
          <button onClick={onClose} className="cancel-button">
            取消
          </button>
          <button 
            onClick={handleConfirm} 
            className="confirm-button"
            disabled={isLoading}
          >
            确认选择
          </button>
        </div>
      </div>
    </div>
  );
};
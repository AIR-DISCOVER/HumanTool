import React, { useState, useEffect } from 'react';
import './ConfigModal.css';

interface UserProfile {
  id: string;
  name: string;
  description: string;
}

interface WritingTheme {
  id: string;
  label: string;
  query: string;
  description: string;
}

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: { user_profile: string; writing_query: string }) => void;
}

const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [userProfile, setUserProfile] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('');
  const [userProfiles, setUserProfiles] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  // 🎯 定义创意写作主题选项
  const writingThemes: WritingTheme[] = [
    {
      id: 'supernatural',
      label: '超自然力量',
      query: "基于以下背景设定写一个故事大纲：人类曾经拥有强大的魔法力量。但随着地球上超过70亿人，魔力已经分散得太薄，无法产生任何影响。当敌对的外星人将人类减少到微不足道的程度时，幸存者发现一种古老的力量开始再次觉醒。",
      description: '人类曾经拥有强大的魔法力量。但随着地球上超过70亿人，魔力已经分散得太薄，无法产生任何影响。当敌对的外星人将人类减少到微不足道的程度时，幸存者发现一种古老的力量开始再次觉醒。'
    },
    {
      id: 'sideeffects',
      label: '副作用',
      query: "基于以下背景设定写一个故事大纲：当你28岁时，科学发现了一种药物，可以阻止所有衰老的影响，实现永生。你的政府决定将该药物提供给所有26岁以下的公民，但你和其余的\"迷失的一代\"被认为风险过高。当你85岁时，副作用终于被发现。",
      description: '当你28岁时，科学发现了一种药物，可以阻止所有衰老的影响，实现永生。你的政府决定将该药物提供给所有26岁以下的公民，但你和其余的"迷失的一代"被认为风险过高。当你85岁时，副作用终于被发现。'
    }
  ];

  // 🎯 照搬AccountSelector逻辑：从数据库加载协作者列表
  useEffect(() => {
    if (isOpen) {
      loadCollaboratorsFromDatabase();
    }
  }, [isOpen]);

  const loadCollaboratorsFromDatabase = async () => {
    setLoading(true);
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiBaseURL}/users/accounts`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📊 API返回的协作者数据:', data);
        
        if (data.accounts && Array.isArray(data.accounts)) {
          setUserProfiles(data.accounts);
          if (data.accounts.length > 0) {
            setUserProfile(data.accounts[0].id);
          }
          console.log(`✅ 成功加载 ${data.accounts.length} 个协作者`);
        } else {
          console.warn('数据库返回格式异常，使用默认协作者列表');
          const defaultProfiles = [
            { id: 'user_main', name: '默认用户', description: '通用协作者档案' }
          ];
          setUserProfiles(defaultProfiles);
          setUserProfile('user_main');
        }
      } else {
        console.warn(`API请求失败: ${response.status}`, await response.text());
        const defaultProfiles = [
          { id: 'user_main', name: '默认用户', description: '通用协作者档案' }
        ];
        setUserProfiles(defaultProfiles);
        setUserProfile('user_main');
      }
    } catch (error) {
      console.warn('加载协作者列表失败，使用默认配置:', error);
      const defaultProfiles = [
        { id: 'user_main', name: '默认用户', description: '通用协作者档案' }
      ];
      setUserProfiles(defaultProfiles);
      setUserProfile('user_main');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (userProfile && selectedTheme && !submitting) {
      setSubmitting(true);
      setSubmitStatus('submitting');
      
      try {
        // 🎯 找到选中的写作主题，传递完整的query
        const selectedOption = writingThemes.find(option => option.id === selectedTheme);
        const writingQuery = selectedOption ? selectedOption.query : '';
        
        await onSubmit({
          user_profile: userProfile,
          writing_query: writingQuery  // 🎯 传递完整的query
        });
        
        setSubmitStatus('success');
        setTimeout(() => {
          setSubmitStatus('idle');
          setSubmitting(false);
        }, 500);
        
      } catch (error) {
        console.error('配置提交失败:', error);
        setSubmitStatus('error');
        setSubmitting(false);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="config-modal-overlay">
      <div className="config-modal">
        <h3>配置您的助手</h3>
        
        <div className="config-field">
          <label>选择用户档案：</label>
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <span>加载中...</span>
            </div>
          ) : (
            <select 
              value={userProfile} 
              onChange={(e) => setUserProfile(e.target.value)}
              disabled={submitting}
            >
              {userProfiles.map(profile => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
          )}
          {userProfile && (
            <div className="profile-description">
              {userProfiles.find(p => p.id === userProfile)?.description}
            </div>
          )}
        </div>

        {/* 🎯 创意写作主题选择 */}
        <div className="config-field">
          <label>选择创作主题：</label>
          <select 
            value={selectedTheme} 
            onChange={(e) => setSelectedTheme(e.target.value)}
            disabled={submitting}
          >
            <option value="">请选择一个创作主题...</option>
            {writingThemes.map(option => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="config-actions">
          <button 
            onClick={handleSubmit} 
            className={`btn-primary ${submitting ? 'submitting' : ''}`}
            disabled={!userProfile || !selectedTheme || loading || submitting}  // 🎯 添加selectedTheme验证
          >
            {submitting ? (
              <>
                <div className="button-spinner"></div>
                <span>
                  {submitStatus === 'submitting' ? '正在初始化...' : ''}
                  {submitStatus === 'success' ? '配置成功！' : ''}
                  {submitStatus === 'error' ? '配置失败，请重试' : ''}
                </span>
              </>
            ) : (
              '开始对话'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfigModal;
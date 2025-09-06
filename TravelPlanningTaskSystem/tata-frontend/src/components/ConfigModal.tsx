import React, { useState, useEffect } from 'react';
import './ConfigModal.css';

interface UserProfile {
  id: string;
  name: string;
  description?: string;
  experiment_group?: string;
  user_type?: string;
}

interface TravelOption {
  id: string;
  label: string;
  query: string;
  description: string;
}

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: { user_profile: string; travel_query: string }) => void;
}

const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [userProfile, setUserProfile] = useState('');
  const [selectedTravel, setSelectedTravel] = useState('');
  const [userProfiles, setUserProfiles] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  // 🎯 定义旅游选项 - 从三个查询中提取的关键信息
  const travelOptions: TravelOption[] = [
    // {
    //   id: 'philadelphia_virginia',
    //   label: '费城出发 → 弗吉尼亚州三城 (7天)',
    //   query: "Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800.",
    //   description: '预算$1,800，探索弗吉尼亚州多个城市的深度之旅'
    // },
    {
      id: 'vegas_santa_maria',
      label: '拉斯维加斯 → 圣玛丽亚 (3天，4人)',
      query: "Could you help design a 3-day trip for a group of 4 from Las Vegas to Santa Maria from March 10th to March 12th, 2022? We have a budget of $3,700. We have a preference for American and Mediterranean cuisines.",
      description: '预算$3,700，美式和地中海美食体验之旅'
    },
    {
      id: 'ithaca_newark',
      label: '伊萨卡 → 纽瓦克 (3天，2人)',
      query: "Can you design a 3-day travel itinerary for 2 people, departing from Ithaca and heading to Newark from March 18th to March 20th, 2022? Our budget is set at $1,200, and we require our accommodations to be entire rooms and visitor-friendly. Please note that we prefer not to drive ourselves during this trip.",
      description: '预算$1,200，整间房住宿，公共交通出行'
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
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseURL}/api/users/accounts`, {
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

  // 🎯 照搬AccountSelector逻辑：保存协作者选择到服务器
  const saveCollaboratorSelection = async (accountId: string) => {
    try {
      const apiBaseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseURL}/api/users/select-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          timestamp: Date.now(),
          session_context: {
            selection_source: 'config_modal',
            selection_time: new Date().toISOString()
          }
        })
      });

      if (response.ok) {
        console.log('✅ 协作者选择已保存到服务器');
      } else {
        console.error('保存协作者选择失败:', response.status);
      }
    } catch (error) {
      console.error('保存协作者选择时出错:', error);
    }
  };

  const handleSubmit = async () => {
    if (userProfile && selectedTravel && !submitting) {
      setSubmitting(true);
      setSubmitStatus('submitting');
      
      try {
        // 🎯 关键修复：先保存协作者选择到后端
        await saveCollaboratorSelection(userProfile);
        
        // 🎯 找到选中的旅游选项，传递完整的query
        const selectedOption = travelOptions.find(option => option.id === selectedTravel);
        const travelQuery = selectedOption ? selectedOption.query : '';
        
        await onSubmit({
          user_profile: userProfile,
          travel_query: travelQuery
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
          <label>选择协作者：</label>
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
              {/* {userProfiles.find(p => p.id === userProfile)?.description}
              {userProfiles.find(p => p.id === userProfile)?.experiment_group && (
                <span className="experiment-group"> (组别: {userProfiles.find(p => p.id === userProfile)?.experiment_group})</span>
              )} */}
            </div>
          )}
        </div>

        {/* 🎯 新增：旅游选项选择 */}
        <div className="config-field">
          <label>选择旅游场景：</label>
          <select 
            value={selectedTravel} 
            onChange={(e) => setSelectedTravel(e.target.value)}
            disabled={submitting}
          >
            <option value="">请选择一个旅游场景...</option>
            {travelOptions.map(option => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          {selectedTravel && (
            <div className="profile-description">
              {travelOptions.find(opt => opt.id === selectedTravel)?.description}
            </div>
          )}
        </div>

        <div className="config-actions">
          <button 
            onClick={handleSubmit} 
            className={`btn-primary ${submitting ? 'submitting' : ''}`}
            disabled={!userProfile || !selectedTravel || loading || submitting}  // 🎯 添加selectedTravel验证
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
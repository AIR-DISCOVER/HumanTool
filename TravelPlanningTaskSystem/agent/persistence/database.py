import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, Column, String, Text, JSON, Boolean, DateTime, Enum, ForeignKey, Integer, DECIMAL, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.mysql import TIMESTAMP, LONGTEXT

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    preferences = Column(JSON)
    
    # 用户统计字段
    total_sessions_count = Column(Integer, default=0)
    total_words_generated = Column(Integer, default=0)
    avg_session_duration_minutes = Column(DECIMAL(10,2), default=0)
    last_active_at = Column(TIMESTAMP)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 🎯 新增字段：人类工具档案相关
    user_type = Column(String(50), default='general')  # 用户类型
    display_name = Column(String(100))  # 显示名称
    experiment_group = Column(String(20))  # 实验组别
    description = Column(Text)  # 用户描述
    capabilities = Column(JSON)  # 能力列表
    user_preferences = Column(JSON)  # 用户偏好
    accessible = Column(Boolean, default=True)  # 是否可访问
    input_schema = Column(JSON)  # 输入模式定义
    
    # 🎯 关键字段：整合后的用户档案（来自profile_manager）
    overall_profile = Column(Text)  # 整合的用户档案描述
    last_updated = Column(DateTime)  # 档案最后更新时间
    
    # 关系
    sessions = relationship("Session", back_populates="user")

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.id'))
    title = Column(String(200))
    status = Column(Enum('active', 'paused', 'completed'), default='active')
    
    # 议程和内容
    agenda_doc = Column(LONGTEXT)
    core_goal = Column(Text)
    session_summary = Column(Text)
    
    # 统计信息
    message_count = Column(Integer, default=0)
    draft_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    tool_usage_count = Column(Integer, default=0)
    tools_used = Column(JSON)
    
    # 时间维度
    session_started_at = Column(TIMESTAMP, default=datetime.utcnow)
    first_ai_response_at = Column(TIMESTAMP)
    last_activity_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    duration_minutes = Column(DECIMAL(10,2), default=0)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    drafts = relationship("Draft", back_populates="session")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('sessions.id'))
    
    # 角色分类 (更标准)
    message_role = Column(Enum('user', 'assistant', 'system', 'tool'), default='user')
    type = Column(Enum('user', 'ai', 'ai_pause', 'system', 'tool'), default='user')  # 保持兼容性
    content = Column(LONGTEXT)
    
    # 消息属性
    word_count = Column(Integer, default=0)
    tool_name = Column(String(50))
    parent_message_id = Column(String(50), ForeignKey('messages.id'))
    
    # 元数据
    message_metadata = Column(JSON)
    
    # 🎯 新增：LLM完整响应内容
    llm_response_content = Column(LONGTEXT, comment='LLM完整响应内容(JSON格式)')
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id])

class Draft(Base):
    __tablename__ = 'drafts'
    
    id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey('sessions.id'))
    draft_id = Column(String(100))
    content = Column(LONGTEXT)
    
    # 草稿分类和版本
    draft_type = Column(Enum('story', 'character', 'plot', 'dialogue', 'outline', 'setting', 'other'), default='other')
    version = Column(Integer, default=1)
    is_final = Column(Boolean, default=False)
    
    # 统计信息
    word_count = Column(Integer, default=0)
    
    created_by = Column(Enum('user', 'ai'), default='ai')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("Session", back_populates="drafts")

class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 从环境变量构建数据库URL
            import os
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "3307")
            db_user = os.getenv("DB_USER", "root")
            db_password = os.getenv("DB_PASSWORD", "123456")
            db_name = os.getenv("DB_NAME", "tata")
            database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        print(f"✅ DatabaseManager 初始化完成，连接: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    def test_connection(self):
        """测试数据库连接 - 修复版本"""
        try:
            db = self.get_session()
            # 使用text()函数包装SQL语句
            db.execute(text("SELECT 1"))
            db.close()
            return True
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
            return False
    
    def get_session(self):
        return self.SessionLocal()
    
    def create_user(self, user_id: str, name: str = None, email: str = None, preferences: Dict = None) -> bool:
        """创建用户"""
        db = self.get_session()
        try:
            existing_user = db.query(User).filter_by(id=user_id).first()
            if existing_user:
                return False
            
            user = User(
                id=user_id,
                name=name or user_id,
                email=email,
                preferences=preferences or {}
            )
            db.add(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ 创建用户失败: {e}")
            return False
        finally:
            db.close()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        db = self.get_session()
        try:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                return {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'preferences': user.preferences or {},
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            return None
        finally:
            db.close()
    
    def create_session(self, session_id: str, user_id: str, title: str = None) -> bool:
        """创建会话 - 修复重复创建问题"""
        db = self.get_session()
        try:
            # 首先检查会话是否已存在
            existing_session = db.query(Session).filter_by(id=session_id).first()
            if existing_session:
                print(f"✅ 会话已存在，跳过创建: {session_id}")
                return True  # 返回True表示会话可用
            
            # 确保用户存在
            user = db.query(User).filter_by(id=user_id).first()
            if not user:
                print(f"🔄 用户不存在，自动创建: {user_id}")
                self.create_user(user_id)
            
            # 创建新会话
            session = Session(
                id=session_id,
                user_id=user_id,
                title=title or "新对话",
                status='active',
                session_started_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
            print(f"✅ 新会话创建成功: {session_id}")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ 创建会话失败: {e}")
            return False
        finally:
            db.close()
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """保存会话状态 - 修复重复创建问题"""
        db = self.get_session()
        try:
            session = db.query(Session).filter_by(id=session_id).first()
            if not session:
                # 如果会话不存在，记录警告但不创建
                print(f"⚠️ 会话不存在，无法保存状态: {session_id}")
                print("💡 请确保在保存状态前先调用 create_session()")
                return
            
            # 更新现有会话
            if state.get('agenda_doc'):
                session.agenda_doc = state.get('agenda_doc')
            if state.get('is_interactive_pause'):
                session.status = 'paused'
            elif state.get('action_needed') == 'finish':
                session.status = 'completed'
                session.completed_at = datetime.utcnow()
            
            session.last_activity_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"❌ 保存会话状态失败: {e}")
        finally:
            db.close()
    
    def load_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话状态"""
        db = self.get_session()
        try:
            session = db.query(Session).filter_by(id=session_id).first()
            if session:
                return self._deserialize_state(session)
            return None
        finally:
            db.close()
    
    def save_message(self, session_id: str, message_type: str, content: str, metadata: Dict = None, llm_response_content: str = None):
        """保存消息 - 适配新结构，支持LLM响应内容"""
        db = self.get_session()
        try:
            # 计算字数
            word_count = len(str(content).split())
            
            # 映射消息角色
            role_mapping = {
                'user': 'user',
                'ai': 'assistant',
                'ai_pause': 'assistant',
                'system': 'system',
                'tool': 'tool'
            }
            message_role = role_mapping.get(message_type, 'user')
            
            # 提取工具名称
            tool_name = None
            if metadata and 'last_tool' in metadata:
                tool_name = metadata['last_tool'].get('name')
            elif message_type == 'tool' and metadata:
                tool_name = metadata.get('tool_name')
            
            message = Message(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                session_id=session_id,
                message_role=message_role,
                type=message_type,  # 保持兼容性
                content=content,
                word_count=word_count,
                tool_name=tool_name,
                message_metadata=metadata or {},
                llm_response_content=llm_response_content,  # 🎯 新增：保存LLM完整响应内容
                created_at=datetime.utcnow()
            )
            db.add(message)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ 保存消息失败: {e}")
        finally:
            db.close()
    
    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """获取消息历史"""
        db = self.get_session()
        try:
            messages = db.query(Message).filter_by(session_id=session_id)\
                        .order_by(Message.created_at.desc()).limit(limit).all()
            return [self._message_to_dict(msg) for msg in reversed(messages)]
        finally:
            db.close()
    
    def save_drafts(self, session_id: str, drafts: Dict[str, str], created_by: str = 'ai'):
        """保存草稿 - 适配新结构"""
        db = self.get_session()
        try:
            for draft_id, content in drafts.items():
                # 自动识别草稿类型
                draft_type = self._detect_draft_type(draft_id, content)
                word_count = len(str(content).split())
                
                # 检查是否已存在
                existing_draft = db.query(Draft).filter_by(
                    session_id=session_id, 
                    draft_id=draft_id
                ).order_by(Draft.version.desc()).first()
                
                if existing_draft and existing_draft.content == content:
                    continue  # 内容相同，跳过
                
                # 创建新版本
                version = (existing_draft.version + 1) if existing_draft else 1
                
                draft = Draft(
                    id=f"draft_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    draft_id=draft_id,
                    content=content,
                    draft_type=draft_type,
                    version=version,
                    word_count=word_count,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                db.add(draft)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"❌ 保存草稿失败: {e}")
        finally:
            db.close()
    
    def get_drafts(self, session_id: str) -> Dict[str, Dict]:
        """获取会话草稿"""
        db = self.get_session()
        try:
            drafts = db.query(Draft).filter_by(session_id=session_id).all()
            result = {}
            for draft in drafts:
                result[draft.draft_id] = {
                    'content': draft.content,
                    'created_by': draft.created_by,
                    'created_at': draft.created_at.isoformat() if draft.created_at else None,
                    'updated_at': draft.updated_at.isoformat() if draft.updated_at else None
                }
            return result
        finally:
            db.close()
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """获取用户的会话列表"""
        db = self.get_session()
        try:
            sessions = db.query(Session).filter_by(user_id=user_id)\
                        .order_by(Session.updated_at.desc()).all()
            result = []
            for session in sessions:
                # 获取最后一条消息
                last_message = db.query(Message).filter_by(session_id=session.id)\
                                .order_by(Message.created_at.desc()).first()
                
                result.append({
                    'id': session.id,
                    'title': session.title,
                    'status': session.status,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                    'last_message': last_message.content if last_message else None,
                    'message_count': db.query(Message).filter_by(session_id=session.id).count()
                })
            return result
        finally:
            db.close()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户完整档案信息 - 支持新的overall_profile结构"""
        db = self.get_session()
        try:
            # 🎯 修复：使用SQLAlchemy ORM查询，获取所有用户档案字段
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                # 🎯 关键修复：优先使用overall_profile字段（来自profile_manager）
                profile_description = None
                if hasattr(user, 'overall_profile') and user.overall_profile:
                    profile_description = user.overall_profile
                elif hasattr(user, 'description') and user.description:
                    profile_description = user.description
                else:
                    # 如果没有档案描述，返回基本信息
                    profile_description = f"用户类型：{user.user_type or 'general'}"
                
                return {
                    'id': user.id,
                    'name': user.name or user.id,
                    'display_name': user.display_name or user.name or user.id,
                    'user_type': user.user_type or 'general',
                    'experiment_group': user.experiment_group or 'A',
                    'overall_profile': profile_description,
                    'description': user.description if hasattr(user, 'description') else None,
                    'last_updated': user.last_updated if hasattr(user, 'last_updated') else user.updated_at,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at,
                    'accessible': user.accessible if hasattr(user, 'accessible') else True,
                    'preferences': user.preferences if hasattr(user, 'preferences') else {},
                    # 🎯 保持向后兼容性
                    'information_capabilities': user.capabilities.get('information_capabilities', []) if user.capabilities and isinstance(user.capabilities, dict) else [],
                    'reasoning_capabilities': user.capabilities.get('reasoning_capabilities', []) if user.capabilities and isinstance(user.capabilities, dict) else []
                }
            return None
                
        except Exception as e:
            print(f"获取用户档案失败: {e}")
            return None
        finally:
            db.close()
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户"""
        try:
            db = self.get_session()
            try:
                # 检查表结构
                result = db.execute(text("SHOW COLUMNS FROM users"))
                columns = [row[0] for row in result.fetchall()]
                
                # 构建查询
                if 'description' in columns:
                    sql = "SELECT id, name, description FROM users ORDER BY id"
                else:
                    sql = "SELECT id, name FROM users ORDER BY id"
                
                result = db.execute(text(sql))
                rows = result.fetchall()
                
                users = []
                for row in rows:
                    user = {
                        'id': row[0],
                        'name': row[1] if len(row) > 1 else row[0],
                        'description': row[2] if len(row) > 2 else '用户档案'
                    }
                    users.append(user)
                
                return users
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"获取所有用户失败: {e}")  # 🎯 修复：使用 print 而不是 self.logger
            return []
    
    def _detect_draft_type(self, draft_id: str, content: str) -> str:
        """自动检测草稿类型"""
        draft_id_lower = draft_id.lower()
        
        if any(keyword in draft_id_lower for keyword in ['character', 'role', '角色', '人物']):
            return 'character'
        elif any(keyword in draft_id_lower for keyword in ['plot', 'story', '情节', '故事']):
            return 'story'
        elif any(keyword in draft_id_lower for keyword in ['dialogue', 'conversation', '对话']):
            return 'dialogue'
        elif any(keyword in draft_id_lower for keyword in ['outline', 'summary', '大纲', '摘要']):
            return 'outline'
        elif any(keyword in draft_id_lower for keyword in ['setting', 'scene', '场景', '设定']):
            return 'setting'
        else:
            return 'other'
    
    def _deserialize_state(self, session: Session) -> Dict[str, Any]:
        """反序列化状态，恢复LangChain消息对象"""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
        
        # 🎯 关键修复：从数据库加载草稿数据到draft_outputs
        draft_outputs = {}
        try:
            # 获取当前会话的所有草稿
            drafts = self.get_drafts(session.id)
            for draft_id, draft_data in drafts.items():
                draft_outputs[draft_id] = draft_data['content']
            print(f"✅ 从数据库加载了 {len(draft_outputs)} 个草稿到draft_outputs")
        except Exception as e:
            print(f"⚠️ 加载草稿数据失败: {e}")
            draft_outputs = {}
        
        state = {
            'agenda_doc': session.agenda_doc or '',
            'last_response': None,
            'action_needed': None,
            'tool_name': None,
            'tool_params': {},
            'human_question': None,
            'is_interactive_pause': False,
            'draft_outputs': draft_outputs,  # 🎯 使用从数据库加载的草稿数据
        }
        
        # 从消息表加载消息历史并恢复为LangChain对象
        messages = self.get_messages(session.id)
        langchain_messages = []
        
        message_classes = {
            'user': HumanMessage,
            'assistant': AIMessage,
            'system': SystemMessage,
            'tool': ToolMessage
        }
        
        for msg in messages:
            msg_role = msg.get('message_role', msg.get('type', 'user'))
            msg_class = message_classes.get(msg_role, HumanMessage)
            
            if msg_role == 'tool':
                langchain_messages.append(msg_class(
                    content=msg['content'],
                    tool_call_id=msg.get('message_metadata', {}).get('tool_call_id', '')
                ))
            elif msg_role == 'assistant' and msg.get('message_metadata', {}).get('tool_calls'):
                # AI消息包含工具调用
                langchain_messages.append(AIMessage(
                    content=msg['content'],
                    tool_calls=msg['message_metadata']['tool_calls']
                ))
            else:
                langchain_messages.append(msg_class(content=msg['content']))
        
        state['messages'] = langchain_messages
        return state
    
    def _message_to_dict(self, message: Message) -> Dict:
        """转换消息对象为字典"""
        return {
            'id': message.id,
            'type': message.type,
            'message_role': message.message_role,
            'content': message.content,
            'message_metadata': message.message_metadata or {},
            'llm_response_content': message.llm_response_content,  # 🎯 新增：包含LLM响应内容
            'created_at': message.created_at.isoformat() if message.created_at else None
        }

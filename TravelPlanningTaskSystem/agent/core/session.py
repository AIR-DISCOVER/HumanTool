import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage
from agent.utils.logger import Logger

class SessionManager:
    """会话管理类"""
    
    def __init__(self, database_manager, user_name: str, logger: Logger):
        self.database_manager = database_manager
        self.user_name = user_name
        self.logger = logger
        # 🎯 新增：缓存最近的LLM响应内容
        self._cached_llm_response = None
    
    def initialize_session(self, initial_query: str, session_id: str) -> tuple[str, Dict[str, Any], bool]:
        """初始化会话
        
        Returns:
            tuple: (session_id, initial_state, is_existing_session)
        """
        # 生成会话ID（如果未提供）
        if not session_id:
            session_id = f"session_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
            is_new_session = True
        else:
            is_new_session = False
        
        # 尝试从数据库恢复状态
        restored_state, existing_session = self._restore_session_state(session_id)
        
        # 数据库操作：创建会话和保存用户查询
        self._handle_database_operations(session_id, initial_query, existing_session, is_new_session, restored_state)
        
        # 设置初始状态
        if restored_state and existing_session:
            current_state_dict = self._setup_restored_session(restored_state, initial_query)
            self.logger.info(f"🔄 继续现有会话，消息历史: {len(current_state_dict.get('messages', []))} 条")
        else:
            current_state_dict = self._init_new_session_state(initial_query)
            self.logger.info(f"🆕 初始化新会话状态")
        
        # 确保会话ID在状态中
        current_state_dict['session_id'] = session_id
        current_state_dict['user_id'] = self.user_name
        
        # 调试：打印当前消息历史
        self._debug_message_history(current_state_dict)
        
        return session_id, current_state_dict, existing_session
    
    def _restore_session_state(self, session_id: str) -> tuple[Optional[Dict[str, Any]], bool]:
        """从数据库恢复会话状态"""
        restored_state = None
        existing_session = False
        
        if self.database_manager and session_id:
            try:
                restored_state = self.database_manager.load_session_state(session_id)
                if restored_state:
                    existing_session = True
                    self.logger.info(f"📂 找到现有会话，恢复状态: {session_id}")
                    self.logger.info(f"📋 恢复的消息数量: {len(restored_state.get('messages', []))}")
                    
                    # 验证恢复的消息
                    messages = restored_state.get('messages', [])
                    for i, msg in enumerate(messages):
                        msg_preview = str(msg.content)[:50] if hasattr(msg, 'content') else str(msg)[:50]
                        msg_type = type(msg).__name__ if hasattr(msg, '__class__') else 'Unknown'
                        self.logger.info(f"  消息 {i+1}: {msg_type} - {msg_preview}...")
                else:
                    self.logger.info(f"🆕 未找到现有会话状态: {session_id}")
            except Exception as e:
                self.logger.warning(f"⚠️ 状态恢复失败: {e}")
                import traceback
                traceback.print_exc()
        
        return restored_state, existing_session
    
    def _handle_database_operations(self, session_id: str, initial_query: str, 
                                  existing_session: bool, is_new_session: bool, 
                                  restored_state: Optional[Dict[str, Any]]):
        """处理数据库操作"""
        if not self.database_manager:
            return
            
        try:
            # 确保用户存在
            if not self.database_manager.get_user(self.user_name):
                success = self.database_manager.create_user(self.user_name, name=self.user_name)
                if success:
                    self.logger.info(f"✅ 用户创建成功: {self.user_name}")
                else:
                    self.logger.warning(f"⚠️ 用户创建失败: {self.user_name}")
            
            # 创建会话（如果不存在）
            success = self.database_manager.create_session(session_id, self.user_name, title=initial_query[:50])
            if success:
                self.logger.info(f"✅ 会话准备就绪: {session_id}")
            
            # 保存用户查询
            self._save_user_message_if_needed(session_id, initial_query, existing_session, 
                                            is_new_session, restored_state)
                
        except Exception as e:
            self.logger.warning(f"⚠️ 数据库操作失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_user_message_if_needed(self, session_id: str, initial_query: str, 
                                   existing_session: bool, is_new_session: bool,
                                   restored_state: Optional[Dict[str, Any]]):
        """根据需要保存用户消息"""
        # 只在新会话或新消息时保存用户查询
        if not existing_session or is_new_session:
            self.database_manager.save_message(session_id, 'user', initial_query)
            self.logger.info(f"✅ 用户查询已保存（新消息）")
        else:
            # 检查是否为新的不同用户输入
            messages = restored_state.get('messages', []) if restored_state else []
            last_user_message = None
            
            # 从后往前找最后一条用户消息
            for msg in reversed(messages):
                if hasattr(msg, 'content') and hasattr(msg, '__class__'):
                    if 'Human' in msg.__class__.__name__ or getattr(msg, 'type', '') == 'human':
                        last_user_message = msg.content
                        break
            
            # 如果新输入与最后一条用户消息不同，则保存
            if not last_user_message or last_user_message.strip() != initial_query.strip():
                self.database_manager.save_message(session_id, 'user', initial_query)
                self.logger.info(f"✅ 保存新的用户查询")
            else:
                self.logger.info(f"🔄 跳过重复的用户查询")
    
    def _setup_restored_session(self, restored_state: Dict[str, Any], initial_query: str) -> Dict[str, Any]:
        """设置恢复的会话状态"""
        current_state_dict = restored_state.copy()
        self.logger.info(f"🔄 使用恢复的会话状态")
        
        # 如果有新的用户输入，添加到消息历史
        messages = current_state_dict.get('messages', [])
        
        # 检查最后一条消息是否是这次的用户输入
        need_add_message = True
        if messages:
            last_msg = messages[-1]
            if (hasattr(last_msg, 'content') and 
                hasattr(last_msg, '__class__') and
                'Human' in last_msg.__class__.__name__ and 
                last_msg.content.strip() == initial_query.strip()):
                need_add_message = False
                self.logger.info(f"📝 用户消息已在历史中，不重复添加")
        
        if need_add_message:
            messages.append(HumanMessage(content=initial_query))
            current_state_dict['messages'] = messages
            self.logger.info(f"📝 添加新用户输入到消息历史")
        
        # 更新当前查询但保持其他状态
        current_state_dict['input_query'] = initial_query
        
        # 重置某些状态以允许继续处理
        current_state_dict['action_needed'] = None
        current_state_dict['is_interactive_pause'] = False
        current_state_dict['final_answer'] = None
        current_state_dict['human_question'] = None
        
        return current_state_dict
    
    def _init_new_session_state(self, initial_query: str) -> Dict[str, Any]:
        """初始化新会话状态"""
        return {
            "input_query": initial_query,
            "agenda_doc": "",
            "last_response": None,
            "messages": [],
            "action_needed": None,
            "tool_name": None,
            "tool_params": None,
            "human_question": None,
            "final_answer": None,
            "error_message": None,
            "tool_call_id_for_next_tool_message": None,
            "draft_outputs": {},
            "is_interactive_pause": False,
            "_json_parse_error_count": 0,
            "_router_error_count": 0,
            "session_memory": ""  # 🎯 新增：会话记忆字段
        }
    
    def _debug_message_history(self, state: Dict[str, Any]):
        """调试：打印当前消息历史"""
        messages = state.get('messages', [])
        self.logger.info(f"🔍 开始处理前的消息历史:")
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__ if hasattr(msg, '__class__') else 'Unknown'
            content_preview = str(msg.content)[:50] if hasattr(msg, 'content') else str(msg)[:50]
            self.logger.info(f"  {i+1}. {msg_type}: {content_preview}...")
    
    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """保存会话状态"""
        if self.database_manager:
            try:
                self.database_manager.save_session_state(session_id, state)
            except Exception as e:
                self.logger.warning(f"⚠️ 状态保存失败: {e}")
            
            # 保存草稿内容
            draft_outputs = state.get('draft_outputs', {})
            if draft_outputs:
                try:
                    self.database_manager.save_drafts(session_id, draft_outputs)
                except Exception as e:
                    self.logger.warning(f"⚠️ 草稿保存失败: {e}")
    
    def cache_llm_response(self, llm_response_content: str):
        """缓存LLM响应内容"""
        self._cached_llm_response = llm_response_content
        self.logger.info(f"🎯 缓存LLM响应内容: {len(llm_response_content)} 字符")
    
    def get_cached_llm_response(self) -> Optional[str]:
        """获取缓存的LLM响应内容"""
        return self._cached_llm_response
    
    def clear_cached_llm_response(self):
        """清除缓存的LLM响应内容"""
        self._cached_llm_response = None

    def save_ai_response(self, session_id: str, state: Dict[str, Any], initial_query: str):
        """保存AI响应"""
        if not self.database_manager or not state.get("final_answer"):
            return
            
        try:
            final_answer = state.get("final_answer")
            
            # 简单检查：如果final_answer不是用户问题，则保存
            if final_answer != initial_query:
                message_type = 'ai_pause' if state.get("is_interactive_pause") else 'ai'
                metadata = {}
                
                # 保存工具调用信息
                if state.get("tool_name"):
                    metadata['last_tool'] = {
                        'name': state["tool_name"],
                        'params': state.get("tool_params", {})
                    }
                
                # 🎯 关键修复：优先使用缓存的LLM响应内容
                llm_response_content = state.get("_llm_response_content") or self.get_cached_llm_response()
                
                if llm_response_content:
                    self.logger.info(f"🎯 使用{'状态中的' if state.get('_llm_response_content') else '缓存的'}LLM响应内容")
                else:
                    self.logger.warning(f"⚠️ 未找到LLM响应内容（状态和缓存都为空）")
                
                self.database_manager.save_message(
                    session_id,
                    message_type,
                    final_answer,
                    metadata,
                    llm_response_content  # 🎯 新增：传递LLM响应内容
                )
                self.logger.info(f"✅ AI响应已保存{'（包含LLM响应内容）' if llm_response_content else ''}")
                
                # 🎯 保存后清除缓存
                self.clear_cached_llm_response()
            else:
                self.logger.info(f"🔄 跳过保存（final_answer与用户输入相同）")
        except Exception as e:
            self.logger.warning(f"⚠️ AI响应保存失败: {e}")

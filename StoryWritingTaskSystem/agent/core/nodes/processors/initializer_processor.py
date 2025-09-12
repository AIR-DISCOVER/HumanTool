"""
初始化处理器
"""
from typing import cast
from langchain_core.messages import SystemMessage, HumanMessage
from ...state import SimplerAgendaState

class InitializerProcessor:
    """初始化处理器 - 处理会话初始化"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def process(self, state: SimplerAgendaState, system_prompt: str) -> SimplerAgendaState:
        """处理初始化逻辑"""
        self.logger.info("--- Initializer Node ---")
        
        # 更强健的判断逻辑
        messages = state.get("messages", [])
        has_system_prompt = any(
            hasattr(msg, '__class__') and 'System' in msg.__class__.__name__ 
            for msg in messages
        )
        
        # 如果没有消息，或者没有系统提示词，才需要初始化
        is_first_invocation = len(messages) == 0 or not has_system_prompt
        
        self.logger.info(f"消息历史长度: {len(messages)}")
        self.logger.info(f"包含系统提示词: {has_system_prompt}")
        self.logger.info(f"是否首次调用: {is_first_invocation}")
        
        if is_first_invocation:
            self.logger.info("首次调用，进行初始化")
            return self._initialize_first_session(state, system_prompt)
        else:
            self.logger.info("非首次调用，直接传递状态")
            return state
    
    def _initialize_first_session(self, state: SimplerAgendaState, system_prompt: str) -> SimplerAgendaState:
        """初始化首次会话"""
        initial_query = state["input_query"]
        initial_agenda = f"- [ ] {initial_query} @overall_goal"
        
        # 检查是否已有消息历史需要保留
        existing_messages = state.get("messages", [])
        
        if existing_messages:
            # 如果已有消息，只在开头添加系统提示词（如果缺失）
            has_system = any(
                hasattr(msg, '__class__') and 'System' in msg.__class__.__name__ 
                for msg in existing_messages
            )
            
            if not has_system:
                # 在现有消息前插入系统提示词
                new_messages = [SystemMessage(content=system_prompt)] + existing_messages
                self.logger.info(f"在现有 {len(existing_messages)} 条消息前添加系统提示词")
            else:
                new_messages = existing_messages
                self.logger.info(f"保留现有 {len(existing_messages)} 条消息")
        else:
            # 全新会话
            new_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"我的任务是: {initial_query}")
            ]
            self.logger.info("创建全新会话消息")
        
        return cast(SimplerAgendaState, {
            "input_query": initial_query,
            "agenda_doc": state.get("agenda_doc", initial_agenda),  # 保留现有议程
            "messages": new_messages,
            "last_response": state.get("last_response"),
            "action_needed": state.get("action_needed"),
            "tool_name": state.get("tool_name"),
            "tool_params": state.get("tool_params"),
            "human_question": state.get("human_question"),
            "final_answer": state.get("final_answer"),
            "error_message": state.get("error_message"),
            "tool_call_id_for_next_tool_message": None,
            "draft_outputs": state.get("draft_outputs", {}),  # 保留现有草稿
        })
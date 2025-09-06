from typing import TypedDict, List, Optional, Dict, Any

class BaseMessage:
    pass  # Assuming BaseMessage is defined elsewhere

class SimplerAgendaState(TypedDict, total=False):
    """简化的智能体状态 - 确保包含完整的历史记录字段"""
    messages: List[BaseMessage]  # 🎯 确保消息历史存在
    current_step: str
    step_count: int
    action_needed: str
    human_question: Optional[str]
    
    # 工具相关
    tool_name: Optional[str] 
    tool_params: Optional[Dict[str, Any]]
    tool_call_id_for_next_tool_message: Optional[str]
    
    # 历史和上下文
    chat_history: Optional[List[str]]  # 🎯 格式化的聊天历史
    tool_execution_history: Optional[List[str]]  # 🎯 工具执行历史
    
    # 其他状态
    error_message: Optional[str]
    is_interactive_pause: Optional[bool]
    loop_break_reason: Optional[str]
    draft_outputs: Optional[Dict[str, str]]
    last_auto_saved_draft: Optional[str]
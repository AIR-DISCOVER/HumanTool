from typing import TypedDict, List, Dict, Any, Optional, Literal
from langchain_core.messages import BaseMessage

class SimplerAgendaState(TypedDict, total=False):
    # 输入和查询
    input_query: str
    
    # 核心状态
    agenda_doc: str
    last_response: Optional[str]
    messages: List[BaseMessage]
    
    # 动作控制
    action_needed: Optional[str]  # "call_tool", "ask_human", "self_update", "finish"
    
    # 工具相关
    tool_name: Optional[str]
    tool_params: Optional[Dict[str, Any]]
    tool_call_id_for_next_tool_message: Optional[str]
    
    # 人类交互
    human_question: Optional[str]
    is_interactive_pause: bool  # 新增：标记是否需要交互暂停
    
    # 输出
    final_answer: Optional[str]
    draft_outputs: Dict[str, Any]
    
    # 错误处理
    error_message: Optional[str]
    _json_parse_error_count: Optional[int]  # 新增: 用于planner节点JSON解析的重试计数
    _router_error_count: Optional[int]      # 新增: 用于路由器未知action的重试计数

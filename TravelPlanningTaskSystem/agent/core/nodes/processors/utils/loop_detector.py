"""
循环检测器
"""
import re
from typing import List
from langchain_core.messages import AIMessage, ToolMessage
from ....state import SimplerAgendaState

class LoopDetector:
    """循环检测器 - 检测和防止各种类型的循环"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def is_recent_duplicate_tool_call(self, state: SimplerAgendaState, tool_name: str, tool_params: dict) -> bool:
        """检查是否是最近重复的工具调用"""
        messages = state.get("messages", [])
        if len(messages) < 2:
            return False
        
        # 检查最近的消息，包括 ToolMessage
        recent_messages = messages[-10:]  # 增加检查范围
        recent_tool_calls = []
        
        for msg in recent_messages:
            # 检查 AIMessage 中的 tool_calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if isinstance(tool_call, dict) and tool_call.get("name") == tool_name:
                        recent_tool_calls.append(tool_call)
            
            # 检查 ToolMessage（工具执行结果）
            elif hasattr(msg, 'content') and isinstance(msg, ToolMessage):
                # 检查是否是相同工具的结果
                if any(f"{tool_name}" in str(msg.content) for tool_name in [tool_name]):
                    recent_tool_calls.append({"name": tool_name, "source": "tool_message"})
        
        # 如果最近有相同工具的调用，认为是重复
        duplicate_count = len(recent_tool_calls)
        
        self.logger.info(f"重复检测 {tool_name}: 发现 {duplicate_count} 次最近调用")
        
        # 如果有任何最近的相同工具调用，都认为是重复
        return duplicate_count > 0
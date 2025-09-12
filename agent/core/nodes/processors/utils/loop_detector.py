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
        
        # 检查是否真正重复（考虑CSP子步骤）
        duplicate_count = len(recent_tool_calls)
        
        self.logger.info(f"重复检测 {tool_name}: 发现 {duplicate_count} 次最近执行，判定为不重复")
        
        # 🎯 修复：允许CSP流程的正常子步骤推进
        if tool_name == "creative_guide":
            # creative_guide工具允许多次调用以完成不同子步骤
            return self._is_creative_guide_duplicate(state, tool_params, recent_tool_calls)
        
        # 其他工具保持原有逻辑，但允许适度重复
        return duplicate_count >= 3  # 允许最多2次重复，第3次才算重复
    
    def _is_creative_guide_duplicate(self, state: SimplerAgendaState, current_params: dict, recent_calls: list) -> bool:
        """专门检查creative_guide是否真正重复"""
        if not recent_calls:
            return False
        
        # 提取当前调用的子步骤
        current_substep = current_params.get("current_substep", "1-1")
        
        # 检查最近的消息中是否有相同子步骤的调用
        messages = state.get("messages", [])
        recent_messages = messages[-5:]  # 检查最近5条消息
        
        for msg in recent_messages:
            if hasattr(msg, 'content'):
                msg_content = str(msg.content)
                # 检查是否已经执行过相同的子步骤
                if f"current_substep\": \"{current_substep}\"" in msg_content:
                    self.logger.info(f"检测到相似的creative_guide调用: '执行csp阶段{current_substep}: 情感内核挖掘...' vs '执行csp阶段{current_substep}: 情感内核挖掘...'")
                    return True
        
        # 如果是不同的子步骤，不算重复
        self.logger.info(f"creative_guide子步骤{current_substep}为新步骤，允许执行")
        return False
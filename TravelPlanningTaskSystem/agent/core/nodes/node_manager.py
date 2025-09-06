"""
节点管理器 - 主要入口，委托给专门的处理器
"""
import uuid
import time
from typing import Dict, Any, List, cast
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from ..state import SimplerAgendaState
from ...utils.logger import Logger
from ...utils.json_parser import JSONParser

# 导入专门的处理器
from .processors.router_processor import RouterProcessor
from .processors.initializer_processor import InitializerProcessor
from .processors.planner_processor import PlannerProcessor
from .processors.tool_processor import ToolProcessor

class NodeManager:
    """节点管理器 - 统一入口，委托给专门的处理器"""
    
    def __init__(self, llm, tools, logger, json_parser):
        self.llm = llm
        self.tools = tools
        self.logger = logger
        self.json_parser = json_parser
        self.stream_callback = None
        self.prompt_manager = None
        
        # 初始化各个处理器
        self.router_processor = RouterProcessor(logger)
        self.initializer_processor = InitializerProcessor(logger)
        self.planner_processor = PlannerProcessor(llm, logger, json_parser)
        self.tool_processor = ToolProcessor(tools, logger)
    
    def set_stream_callback(self, callback):
        """设置流式回调"""
        self.stream_callback = callback
        # 🎯 只设置工具处理器的回调，不设置规划处理器
        if hasattr(self.tool_processor, 'set_stream_callback'):
            self.tool_processor.set_stream_callback(callback)
            self.logger.info("✅ 工具处理器流式回调已设置")
        else:
            self.logger.warning("⚠️ 工具处理器没有 set_stream_callback 方法")
        
    def set_prompt_manager(self, prompt_manager):
        """设置 prompt_manager"""
        self.prompt_manager = prompt_manager
        self.planner_processor.set_prompt_manager(prompt_manager)
    
    def router_node(self, state) -> dict:
        """路由节点 - 委托给RouterProcessor"""
        return self.router_processor.process(state)
    
    def initializer_node(self, state: SimplerAgendaState, system_prompt: str = None) -> SimplerAgendaState:
        """初始化节点 - 委托给InitializerProcessor，增强日志"""
        self.logger.info("=== NodeManager.initializer_node 调用 ===")
        self.logger.info(f"输入状态消息数量: {len(state.get('messages', []))}")
        
        # 如果没有提供系统提示词，尝试从 prompt_manager 获取
        if not system_prompt and self.prompt_manager:
            try:
                system_prompt = self.prompt_manager.get_system_prompt()
                self.logger.info("从 PromptManager 获取系统提示词")
            except Exception as e:
                self.logger.warning(f"获取系统提示词失败: {e}")
                system_prompt = "You are TATA, a helpful story writing assistant."
        elif not system_prompt:
            system_prompt = "You are TATA, a helpful story writing assistant."
            self.logger.info("使用默认系统提示词")
        
        result = self.initializer_processor.process(state, system_prompt)
        
        self.logger.info(f"输出状态消息数量: {len(result.get('messages', []))}")
        self.logger.info("=== NodeManager.initializer_node 完成 ===")
        
        return result
    
    def planner_node(self, state):
        """规划节点 - 委托给PlannerProcessor"""
        self.logger.info("=== NodeManager.planner_node 调用 ===")
        
        # 调试：打印当前状态
        messages = state.get('messages', [])
        self.logger.info(f"输入消息数量: {len(messages)}")
        
        # 打印最后几条消息的概览
        for i, msg in enumerate(messages[-3:], len(messages)-2):
            if i > 0:
                msg_type = type(msg).__name__ if hasattr(msg, '__class__') else 'Unknown'
                content_preview = str(msg.content)[:50] if hasattr(msg, 'content') else str(msg)[:50]
                self.logger.info(f"  消息 {i}: {msg_type} - {content_preview}...")
        
        result = self.planner_processor.process(state)
        
        # 调试：打印输出状态
        result_messages = result.get('messages', [])
        self.logger.info(f"输出消息数量: {len(result_messages)}")
        self.logger.info(f"action_needed: {result.get('action_needed')}")
        
        self.logger.info("=== NodeManager.planner_node 完成 ===")
        return result
    
    def tool_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """工具节点 - 委托给ToolProcessor"""
        return self.tool_processor.process(state)

    # 保留一些兼容性方法
    def _assess_tool_result_quality(self, tool_name: str, result: str, params: Dict) -> str:
        """评估工具结果质量 - 委托给ToolProcessor"""
        return self.tool_processor.assess_result_quality(tool_name, result, params)

    def _auto_save_tool_result(self, state: SimplerAgendaState, tool_name: str, params: Dict, result: str):
        """自动保存工具结果 - 委托给ToolProcessor"""
        return self.tool_processor.auto_save_result(state, tool_name, params, result)

    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具显示名称 - 委托给ToolProcessor"""
        return self.tool_processor.get_display_name(tool_name)

    def _is_recent_duplicate_tool_call(self, state: SimplerAgendaState, tool_name: str, tool_params: dict) -> bool:
        """检查是否是最近重复的工具调用 - 委托给PlannerProcessor"""
        return self.planner_processor.is_recent_duplicate_tool_call(state, tool_name, tool_params)

    def _build_enhanced_tool_context_with_history(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建增强工具上下文 - 委托给PlannerProcessor"""
        return self.planner_processor.build_enhanced_tool_context_with_history(state, original_params)

    def _extract_tool_execution_history(self, state: SimplerAgendaState) -> List[str]:
        """提取工具执行历史 - 委托给PlannerProcessor"""
        return self.planner_processor.extract_tool_execution_history(state)

    def _build_enhanced_tool_context(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建增强工具上下文 - 委托给PlannerProcessor"""
        return self.planner_processor.build_enhanced_tool_context(state, original_params)

    def _emit_tool_call(self, tool_name: str, params: Dict, metadata: Dict):
        """发送工具调用事件 - 委托给ToolProcessor"""
        self.tool_processor.emit_tool_call(tool_name, params, metadata)

    def _emit_tool_result(self, tool_name: str, result: str, metadata: Dict):
        """发送工具结果事件 - 委托给ToolProcessor"""
        self.tool_processor.emit_tool_result(tool_name, result, metadata)
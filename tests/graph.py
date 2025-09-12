import json
import uuid
import os
import re
import sys 
import time
from datetime import datetime
from typing import Literal, cast, TypedDict, List, Dict, Any, Optional, Tuple, Union

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.errors import GraphInterrupt
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import traceback
from langchain_core.language_models.chat_models import BaseChatModel

_current_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_script_dir)

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from agent.tool.human import HumanTool, HUMAN_TOOLS_REGISTRY, get_human_tool_description_for_llm 
from agent.tool.llm import KnowledgeAnalyzerTool
from agent.tool.writing import (
    StoryBrainstormTool, PlotDeveloperTool, LongFormWriterTool,
    DialogueWriterTool, LogicCheckerTool, StyleEnhancerTool
)

# 新的模块化导入
from agent.core.state import SimplerAgendaState
from agent.core.prompts import PromptManager
from agent.core.nodes import NodeManager
from agent.utils.logger import Logger
from agent.utils.json_parser import JSONParser

load_dotenv()

# 保留计算器工具定义（为了兼容性）
class CalculatorTool:
    def execute(self, operation: str, num1: float, num2: float) -> str:
        if operation == "add":
            return str(num1 + num2)
        elif operation == "subtract":
            return str(num1 - num2)
        return "未知的操作"

class AgendaAgent:
    def __init__(self, verbose=True, user_name: str = "user_main", log_level="INFO", 
                 database_manager=None): 
        self.user_name = user_name
        self.database_manager = database_manager
        
        # 初始化工具组件
        self.logger = Logger(verbose, log_level)
        self.json_parser = JSONParser(self.logger)
        
        # 添加流式回调支持
        self.stream_callback = None
        
        # 设置人类工具
        self.human_tools: Dict[str, HumanTool] = {
            name: ht for name, ht in HUMAN_TOOLS_REGISTRY.items() if ht["user_name"] == self.user_name
        }
        if not self.human_tools:
            self.logger.warning(f"未找到用户 '{self.user_name}' 的特定人类能力档案。LLM将基于通用规则与用户交互。")
        else:
            self.logger.info(f"已为用户 '{self.user_name}' 加载以下人类能力档案: {list(self.human_tools.keys())}")

        # 初始化LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

        # 注册工具 - 包含通用工具和专业写作工具
        self.tools = {
            "calculator": CalculatorTool(),
            "knowledge_analyzer": KnowledgeAnalyzerTool(llm=self.llm, verbose=verbose),
            "story_brainstorm": StoryBrainstormTool(llm=self.llm, verbose=verbose),
            "plot_developer": PlotDeveloperTool(llm=self.llm, verbose=verbose),
            "longform_writer": LongFormWriterTool(llm=self.llm, verbose=verbose),  
            "dialogue_writer": DialogueWriterTool(llm=self.llm, verbose=verbose),
            "logic_checker": LogicCheckerTool(llm=self.llm, verbose=verbose),
            "style_enhancer": StyleEnhancerTool(llm=self.llm, verbose=verbose),
        }
        
        # 初始化组件
        self.prompt_manager = PromptManager(user_name, self.human_tools)
        self.node_manager = NodeManager(self.llm, self.tools, self.logger, self.json_parser)
        
        # 构建工作流图
        self.workflow = StateGraph(SimplerAgendaState)
        self._setup_graph()
        self.graph: Any = self.workflow.compile()

    def set_stream_callback(self, callback):
        """设置流式回调函数"""
        self.stream_callback = callback
        # 也设置给 node_manager
        if hasattr(self.node_manager, 'set_stream_callback'):
            self.node_manager.set_stream_callback(callback)
        self.logger.info("流式回调已设置")

    def _send_stream_event(self, event_type: str, content: str, metadata: dict = None):
        """发送流式事件的辅助方法"""
        if self.stream_callback:
            try:
                return self.stream_callback(event_type, content, metadata or {})
            except Exception as e:
                self.logger.error(f"流式回调错误: {e}")
                return None
        return None

    def _setup_graph(self):
        """构建工作流图 - 使用包装器方法"""
        # 添加节点 - 使用包装器方法来支持流式
        self.workflow.add_node("initializer", self._initializer_node_wrapper)
        self.workflow.add_node("planner", self._planner_node_wrapper) 
        self.workflow.add_node("router", self._router_node_wrapper)
        self.workflow.add_node("tool", self._tool_node_wrapper)
        
        # 设置入口点和边
        self.workflow.set_entry_point("initializer")
        self.workflow.add_edge("initializer", "planner")
        self.workflow.add_edge("planner", "router")
        
        # 路由逻辑
        self.workflow.add_conditional_edges(
            "router",
            self._should_call_tool,
            {
                "call_tool": "tool",
                "ask_human": END,
                "continue_planning": "planner",
                "finish": END
            }
        )
        self.workflow.add_edge("tool", "planner")

    def _initializer_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """初始化节点包装器"""
        self._send_stream_event('thinking', '正在初始化任务...', {'step_name': '任务初始化'})
        self.logger.info("[***后端系统] 正在初始化任务状态...")
        return self.node_manager.initializer_node(state)

    def _planner_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """规划节点包装器 - 增强流式支持"""
        self._send_stream_event('thinking', '正在规划下一步...', {'step_name': '策略规划'})
        
        # 调用原始规划节点
        result = self.node_manager.planner_node(state)
        
        # 检查是否有新的草稿内容
        if result.get('draft_outputs'):
            for draft_id, content in result.get('draft_outputs', {}).items():
                # 发送完整的草稿内容
                full_content = str(content)
                self.logger.info(f"发送草稿更新: {draft_id} ({len(full_content)} 字符)")
                self._send_stream_event('draft_update', f'生成草稿: {draft_id}', {
                    'draft_id': draft_id,
                    'content': full_content,  # 完整内容
                    'updated_by': 'ai'
                })
        
        return result

    def _router_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """路由节点包装器"""
        self._send_stream_event('thinking', '正在决定下一步行动...', {'step_name': '决策路由'})
        return self.node_manager.router_node(state)

    def _tool_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """工具节点包装器 - 增强流式支持"""
        tool_name = state.get("tool_name")
        tool_params = state.get("tool_params", {})
        tool_call_id = state.get("tool_call_id_for_next_tool_message")
        
        if tool_name and self.stream_callback:
            # 发送工具调用开始事件
            self._send_stream_event('tool_call', f'正在调用工具: {tool_name}', {
                'call_id': tool_call_id or f'tool_{int(time.time())}',
                'tool_name': tool_name,
                'tool_display_name': self._get_tool_display_name(tool_name),
                'params': tool_params
            })
        
        # 调用原始工具节点
        result = self.node_manager.tool_node(state)
        
        # 发送工具调用完成事件
        if tool_name and self.stream_callback:
            # 从结果中获取工具执行结果
            messages = result.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    tool_result = str(last_message.content)
                    self._send_stream_event('tool_result', tool_result[:500], {
                        'call_id': tool_call_id or f'tool_{int(time.time())}',
                        'tool_name': tool_name,
                        'result': tool_result
                    })
        
        return result

    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具显示名称"""
        display_names = {
            "calculator": "计算器",
            "knowledge_analyzer": "知识分析器", 
            "story_brainstorm": "故事头脑风暴",
            "plot_developer": "情节开发器",
            "longform_writer": "长篇写作器",
            "dialogue_writer": "对话写作器",
            "logic_checker": "逻辑检查器",
            "style_enhancer": "风格增强器"
        }
        return display_names.get(tool_name, tool_name)

    # ...existing code...

    def set_stream_callback(self, callback):
        """设置流式回调函数"""
        self.stream_callback = callback
        # 也设置给 node_manager
        if hasattr(self.node_manager, 'set_stream_callback'):
            self.node_manager.set_stream_callback(callback)
        self.logger.info("流式回调已设置")
    
    def _send_stream_event(self, event_type, content, metadata=None):
        """发送流式事件"""
        if self.stream_callback:
            try:
                return self.stream_callback(event_type, content, metadata)
            except Exception as e:
                self.logger.error(f"流式回调错误: {e}")
        return ""
    
    def run_interactive_streaming(self, initial_query: str, max_iterations: int = 15):
        """流式版本的交互式运行"""
        self.logger.info(f"开始流式交互运行: {initial_query}")
        


        # 发送初始分析事件
        yield self._send_stream_event('thinking', '开始分析任务...', {'step_name': '任务分析'})
        
        # 调用普通的 run_interactive
        result = self.run_interactive(initial_query, max_iterations)
        
        # 缓存结果供后续获取
        self.final_result_cache = result
        
        # 发送完成事件
        if result.get('is_interactive_pause'):
            yield self._send_stream_event('interactive_pause', '等待用户输入...', {'step_name': '交互暂停'})
        else:
            yield self._send_stream_event('final', '处理完成', {'step_name': '完成'})

        def get_final_result(self):
            """获取最终结果 - 详细调试版"""
            print(f"🔍 [WRAPPER] get_final_result 被调用")
            print(f"🔍 [WRAPPER] self 对象存在: {bool(self)}")
            print(f"🔍 [WRAPPER] hasattr final_result_cache: {hasattr(self, 'final_result_cache')}")
            
            if hasattr(self, 'final_result_cache'):
                print(f"🔍 [WRAPPER] final_result_cache 类型: {type(self.final_result_cache)}")
                print(f"🔍 [WRAPPER] final_result_cache 布尔值: {bool(self.final_result_cache)}")
                
                if self.final_result_cache:
                    result = self.final_result_cache
                    print(f"🔍 [WRAPPER] 返回缓存结果:")
                    print(f"  - 类型: {type(result)}")
                    print(f"  - Keys: {list(result.keys())}")
                    print(f"  - is_interactive_pause: {result.get('is_interactive_pause')}")
                    print(f"  - final_answer length: {len(str(result.get('final_answer', '')))}")
                    print(f"  - draft_contents keys: {list(result.get('draft_contents', {}).keys())}")
                    return result
                else:
                    print(f"⚠️ [WRAPPER] final_result_cache 为空")
                    return None
            else:
                print(f"⚠️ [WRAPPER] final_result_cache 属性不存在")
                return None



    def _initializer_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """初始化节点包装器"""
        system_prompt = self.prompt_manager.get_system_prompt()
        return self.node_manager.initializer_node(state, system_prompt)

    def _planner_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """规划节点包装器 - 增强流式支持"""
        if self.stream_callback:
            self._send_stream_event('thinking', '正在规划下一步...', {'step_name': '策略规划'})
        
        # 调用原始规划节点
        result = self.node_manager.planner_node(state)
        
        # 检查是否有新的草稿内容
        if result.get('draft_outputs'):
            for draft_id, content in result.get('draft_outputs', {}).items():
                if self.stream_callback:
                    # 发送完整的草稿内容
                    full_content = str(content)
                    self._send_stream_event('draft_update', f'生成草稿: {draft_id}', {
                        'draft_id': draft_id,
                        'content': full_content,  # 完整内容
                        'updated_by': 'ai'
                    })
        
        return result

    def _tool_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """工具节点包装器 - 增强流式支持"""
        # 设置流式回调给 node_manager
        if hasattr(self.node_manager, 'set_stream_callback'):
            self.node_manager.set_stream_callback(self.stream_callback)
        
        # 调用原始工具节点
        result = self.node_manager.tool_node(state)
        
        return result
    

    def _decide_next_step(self, state: SimplerAgendaState) -> str:
        """路由决策 - 最终版本"""
        self.logger.info("--- Router ---")
        action = state.get("action_needed")
        self.logger.info(f"Router: Action decided by LLM is '{action}'")

        if action == "ask_human":
            if state.get("human_question"):
                self.logger.info("Router: 设置交互暂停状态并直接结束")
                
                # 强制设置所有相关状态
                state["is_interactive_pause"] = True
                state["final_answer"] = state.get("human_question")
                state["action_needed"] = "finish"
                
                # 确保状态不会被覆盖
                state["_force_end"] = True  # 新增强制结束标志
                
                self.logger.info(f"Router: 状态设置完成 - is_interactive_pause=True, action_needed=finish")
                self.logger.info(f"Router: final_answer='{state['final_answer'][:50]}...'")
                
                # 验证设置
                self.logger.info(f"Router: 即将返回END，状态验证:")
                self.logger.info(f"  - is_interactive_pause: {state.get('is_interactive_pause')}")
                self.logger.info(f"  - action_needed: {state.get('action_needed')}")
                self.logger.info(f"  - human_question存在: {bool(state.get('human_question'))}")
                self.logger.info(f"  - _force_end: {state.get('_force_end')}")
                
                return END
            else:
                self.logger.warning("Router: LLM请求询问人类但未提供问题。")
                state["_router_error_count"] = state.get("_router_error_count", 0) + 1
                if state["_router_error_count"] > 2:
                    self.logger.error("Router: 多次错误，强制结束。")
                    state["error_message"] = "系统在决策时遇到问题。"
                    state["final_answer"] = "抱歉，系统处理时出现问题。"
                    state["action_needed"] = "finish"
                    state["is_interactive_pause"] = False
                    return END
                return "replan_due_to_router_issue"

        elif action == "call_tool":
            if state.get("tool_name") and state.get("tool_call_id_for_next_tool_message"):
                return "execute_tool"
            else:
                self.logger.warning("Router: 工具调用信息不完整。")
                state["_router_error_count"] = state.get("_router_error_count", 0) + 1
                if state["_router_error_count"] > 2:
                    self.logger.error("Router: 多次工具调用错误，强制结束。")
                    state["error_message"] = "工具调用遇到问题。"
                    state["final_answer"] = "抱歉，工具处理时出现问题。"
                    return END
                return "replan_due_to_router_issue"
                
        elif action == "self_update":
            return "continue_planning"
            
        elif action == "finish":
            self.logger.info(f"Router: 正常结束。Final answer: {state.get('final_answer', 'N/A')[:50]}...")
            return END
            
        else:
            self.logger.warning(f"Router: 未知action '{action}'。")
            state["_router_error_count"] = state.get("_router_error_count", 0) + 1
            if state["_router_error_count"] > 2:
                self.logger.error("Router: 多次未知action，强制结束。")
                state["error_message"] = "系统决策遇到问题。"
                state["final_answer"] = "抱歉，系统处理时卡住了。"
                state["action_needed"] = "finish"
                return END
            return "replan_due_to_router_issue"

    def _force_replan_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """强制重新规划节点"""
        self.logger.info("--- Force Replan Node ---")
        
        # 复制所有状态，包括错误计数器
        new_state = {key: value for key, value in state.items()}
        
        # 构建更明确的重新规划提示
        replan_message = """系统提示: 上一步的规划存在问题或不完整。请严格按照以下JSON格式重新规划你的完整响应：
```json
{
  "updated_agenda_doc": "详细的任务列表...",
  "thought": "你的思考过程...",
  "next_action": "call_tool|ask_human|self_update|finish",
  "tool_name": "...",
  "tool_params": {},
  "human_question": "...",
  "final_answer": "...",
  "save_to_draft": {"task_id": "...", "content": "..."},
  "use_draft_contents": ["..."]
}
```
请务必返回一个单一、完整且有效的JSON对象。"""

        new_state["last_response"] = replan_message
        
        if not isinstance(new_state.get("messages"), list):
            new_state["messages"] = []
        new_state["messages"].append(HumanMessage(content=replan_message))

        # 重置可能导致问题的规划字段，但不重置错误计数器
        new_state["action_needed"] = None 
        new_state["tool_name"] = None
        new_state["tool_params"] = None
        new_state["human_question"] = None
        # new_state["error_message"] = None # 保留之前的error_message，如果有的话

        return cast(SimplerAgendaState, new_state)

    def run_interactive(self, initial_query: str, session_id: str = None, max_iterations: int = 15):
        """运行交互式对话 - 修复历史记录恢复"""
        
        # 生成会话ID（如果未提供）
        if not session_id:
            session_id = f"session_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
            is_new_session = True
        else:
            is_new_session = False
        
        # 首先尝试从数据库恢复状态（在创建会话之前）
        restored_state = None
        existing_session = False
        
        if self.database_manager and session_id:
            try:
                restored_state = self.database_manager.load_session_state(session_id)
                if restored_state:
                    existing_session = True
                    print(f"📂 [AGENT] 找到现有会话，恢复状态: {session_id}")
                    print(f"📋 [AGENT] 恢复的消息数量: {len(restored_state.get('messages', []))}")
                    
                    # 验证恢复的消息
                    messages = restored_state.get('messages', [])
                    for i, msg in enumerate(messages):
                        msg_preview = str(msg.content)[:50] if hasattr(msg, 'content') else str(msg)[:50]
                        msg_type = type(msg).__name__ if hasattr(msg, '__class__') else 'Unknown'
                        print(f"  消息 {i+1}: {msg_type} - {msg_preview}...")
                else:
                    print(f"🆕 [AGENT] 未找到现有会话状态: {session_id}")
            except Exception as e:
                print(f"⚠️ [AGENT] 状态恢复失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 数据库操作：创建会话和保存用户查询
        if self.database_manager:
            try:
                # 确保用户存在
                if not self.database_manager.get_user(self.user_name):
                    success = self.database_manager.create_user(self.user_name, name=self.user_name)
                    if success:
                        print(f"✅ [AGENT] 用户创建成功: {self.user_name}")
                    else:
                        print(f"⚠️ [AGENT] 用户创建失败: {self.user_name}")
                
                # 创建会话（如果不存在）
                success = self.database_manager.create_session(session_id, self.user_name, title=initial_query[:50])
                if success:
                    print(f"✅ [AGENT] 会话准备就绪: {session_id}")
                
                # 只在新会话或新消息时保存用户查询
                if not existing_session or is_new_session:
                    self.database_manager.save_message(session_id, 'user', initial_query)
                    print(f"✅ [AGENT] 用户查询已保存（新消息）")
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
                        print(f"✅ [AGENT] 保存新的用户查询")
                    else:
                        print(f"🔄 [AGENT] 跳过重复的用户查询")
                    
            except Exception as e:
                print(f"⚠️ [AGENT] 数据库操作失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 设置初始状态
        if restored_state and existing_session:
            # 使用恢复的状态作为基础
            current_state_dict = restored_state.copy()
            print(f"🔄 [AGENT] 使用恢复的会话状态")
            
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
                    print(f"📝 [AGENT] 用户消息已在历史中，不重复添加")
            
            if need_add_message:
                from langchain_core.messages import HumanMessage
                messages.append(HumanMessage(content=initial_query))
                current_state_dict['messages'] = messages
                print(f"📝 [AGENT] 添加新用户输入到消息历史")
            
            # 更新当前查询但保持其他状态
            current_state_dict['input_query'] = initial_query
            
            # 重置某些状态以允许继续处理
            current_state_dict['action_needed'] = None
            current_state_dict['is_interactive_pause'] = False
            current_state_dict['final_answer'] = None
            current_state_dict['human_question'] = None
            
            print(f"🔄 [AGENT] 继续现有会话，消息历史: {len(messages)} 条")
            
        else:
            # 新会话，初始化状态
            current_state_dict = self._init_new_session_state(initial_query)
            print(f"🆕 [AGENT] 初始化新会话状态")
        
        # 确保会话ID在状态中
        current_state_dict['session_id'] = session_id
        current_state_dict['user_id'] = self.user_name
        
        # 调试：打印当前消息历史
        messages = current_state_dict.get('messages', [])
        print(f"🔍 [AGENT] 开始处理前的消息历史:")
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__ if hasattr(msg, '__class__') else 'Unknown'
            content_preview = str(msg.content)[:50] if hasattr(msg, 'content') else str(msg)[:50]
            print(f"  {i+1}. {msg_type}: {content_preview}...")
        
        # 其余处理逻辑保持不变...
        config: RunnableConfig = {"recursion_limit": max_iterations * 3}
        
        for i in range(max_iterations):
            self.logger.info(f"\n--- Iteration {i + 1}/{max_iterations} (Session: {session_id}) ---")
            
            # 在每次迭代开始时，打印当前消息历史数量
            messages = current_state_dict.get('messages', [])
            self.logger.info(f"📋 当前消息历史: {len(messages)} 条")
            
            # 检查交互暂停状态
            if current_state_dict.get("is_interactive_pause"):
                self.logger.info("检测到交互暂停状态，结束处理")
                break
            
            try:
                output_state_dict = self.graph.invoke(current_state_dict, config=config)
                current_state_dict.update(output_state_dict)
                
                # 保存状态到数据库
                if self.database_manager:
                    try:
                        self.database_manager.save_session_state(session_id, current_state_dict)
                    except Exception as e:
                        print(f"⚠️ [AGENT] 状态保存失败: {e}")
                    
                    # 保存草稿内容
                    draft_outputs = current_state_dict.get('draft_outputs', {})
                    if draft_outputs:
                        try:
                            self.database_manager.save_drafts(session_id, draft_outputs)
                        except Exception as e:
                            print(f"⚠️ [AGENT] 草稿保存失败: {e}")
                
                # 检查结束条件
                if self._should_end_iteration(current_state_dict, i):
                    break
                    
            except GraphInterrupt as gi:
                self.logger.info(f"✅ GraphInterrupt捕获，正常结束: {gi}")
                current_state_dict["is_interactive_pause"] = True
                if not current_state_dict.get("final_answer") and current_state_dict.get("human_question"):
                    current_state_dict["final_answer"] = current_state_dict.get("human_question")
                break
                
            except Exception as e:
                self.logger.error(f"执行错误: {e}")
                current_state_dict["error_message"] = f"执行错误: {str(e)}"
                current_state_dict["final_answer"] = "处理时发生错误。"
                break
        
        # 保存AI响应（只在有新回复时）
        if self.database_manager and current_state_dict.get("final_answer"):
            try:
                # 检查是否是新的AI回复
                final_answer = current_state_dict.get("final_answer")
                
                # 简单检查：如果final_answer不是用户问题，则保存
                if final_answer != initial_query:
                    message_type = 'ai_pause' if current_state_dict.get("is_interactive_pause") else 'ai'
                    metadata = {}
                    
                    # 保存工具调用信息
                    if current_state_dict.get("tool_name"):
                        metadata['last_tool'] = {
                            'name': current_state_dict["tool_name"],
                            'params': current_state_dict.get("tool_params", {})
                        }
                    
                    self.database_manager.save_message(
                        session_id, 
                        message_type, 
                        final_answer,
                        metadata
                    )
                    print(f"✅ [AGENT] AI响应已保存")
                else:
                    print(f"🔄 [AGENT] 跳过保存（final_answer与用户输入相同）")
            except Exception as e:
                print(f"⚠️ [AGENT] AI响应保存失败: {e}")
        
        result = self._format_final_response(cast(SimplerAgendaState, current_state_dict))
        result['session_id'] = session_id
        return result
    
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
        }
    
    def _should_end_iteration(self, state: Dict[str, Any], iteration: int) -> bool:
        """判断是否应该结束迭代"""
        if state.get("_force_end"):
            self.logger.info(f"✅ 第 {iteration+1} 次迭代后检测到强制结束标志")
            if not state.get("is_interactive_pause"):
                state["is_interactive_pause"] = True
            return True
            
        if state.get("is_interactive_pause"):
            self.logger.info(f"✅ 第 {iteration+1} 次迭代后检测到交互暂停")
            return True
            
        if state.get("action_needed") == "finish":
            self.logger.info(f"✅ 第 {iteration+1} 次迭代后检测到finish动作")
            return True
            
        if state.get("final_answer") and not state.get("action_needed"):
            self.logger.info(f"✅ 第 {iteration+1} 次迭代后检测到final_answer且无action")
            return True
            
        # 强制检查 - 如果有human_question但没有设置暂停
        if (state.get("human_question") and 
            not state.get("is_interactive_pause") and 
            iteration >= 0):
            self.logger.warning(f"⚠️ 第 {iteration+1} 次迭代：发现human_question但未设置暂停，强制设置")
            state["is_interactive_pause"] = True
            state["final_answer"] = state.get("human_question")
            state["action_needed"] = "finish"
            return True
            
        return False


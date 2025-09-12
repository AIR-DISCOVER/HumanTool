from cmath import log
import time
from typing import cast, Dict, Any
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.errors import GraphInterrupt
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from agent.core.state import SimplerAgendaState
from agent.core.agent import AgentCore
from agent.core.router import RouterLogic
from agent.core.session import SessionManager
from agent.utils.formatters import ResponseFormatter

load_dotenv()

class AgendaAgent:
    """TATA故事大纲生成助手的主要入口类"""
    
    def __init__(self, verbose=True, user_name: str = "user_main", log_level="INFO", 
                 database_manager=None):
        self.user_name = user_name
        self.database_manager = database_manager
        
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2,max_retries=3,request_timeout=40)
        
        # 🎯 传递数据库管理器给 AgentCore
        self.agent_core = AgentCore(
            user_name=user_name,
            verbose=verbose,
            log_level=log_level,
            database_manager=database_manager  # 🎯 新增传递
        )
        
        # 初始化核心组件
        self.router_logic = RouterLogic(self.agent_core.logger)
        self.session_manager = SessionManager(database_manager, user_name, self.agent_core.logger)
        self.formatter = ResponseFormatter()
        
        # 快速访问属性
        self.user_name = user_name
        self.database_manager = database_manager
        self.logger = self.agent_core.logger
        self.stream_callback = None
        
        # 构建工作流图
        self.workflow = StateGraph(SimplerAgendaState)
        self._setup_graph()
        self.graph = self.workflow.compile()

    def set_stream_callback(self, callback):
        """设置流式回调函数"""
        self.stream_callback = callback
        self.agent_core.set_stream_callback(callback)

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
        """构建工作流图"""
        # 添加节点 - 使用包装器方法来支持流式
        self.workflow.add_node("initializer", self._initializer_node_wrapper)
        self.workflow.add_node("planner", self._planner_node_wrapper) 
        self.workflow.add_node("router", self._router_node_wrapper)
        self.workflow.add_node("tool", self._tool_node_wrapper)
        
        # 设置入口点和边
        self.workflow.set_entry_point("initializer")
        self.workflow.add_edge("initializer", "planner")
        self.workflow.add_edge("planner", "router")
        
        # 路由逻辑 - 使用包装器确保状态正确传递
        self.workflow.add_conditional_edges(
            "router",
            self._router_condition_wrapper,
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
        return self.agent_core.node_manager.initializer_node(state)

    def _planner_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """规划节点包装器 - 增强流式支持"""
        self._send_stream_event('thinking', '正在规划下一步...', {'step_name': '策略规划'})
        
        # 调用原始规划节点
        result = self.agent_core.node_manager.planner_node(state)
        
        # 🎯 关键修复：如果planner_node生成了LLM响应内容，缓存到SessionManager
        llm_response_content = result.get("_llm_response_content")
        if llm_response_content:
            self.session_manager.cache_llm_response(llm_response_content)
            self.logger.info(f"🎯 已将LLM响应内容缓存到SessionManager")
        
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
        return state  # 路由逻辑现在在条件边中处理

    def _router_condition_wrapper(self, state: SimplerAgendaState) -> str:
        """路由条件包装器 - 确保状态修改能够正确传递"""
        # 🎯 关键修复：在条件边中保留LLM响应内容
        llm_response_content = state.get("_llm_response_content")
        
        # 调用原始路由逻辑
        decision = self.router_logic.should_call_tool(state)
        
        # 🎯 关键修复：确保LLM响应内容在路由决策后仍然存在
        if llm_response_content and not state.get("_llm_response_content"):
            state["_llm_response_content"] = llm_response_content
            self.logger.info(f"🔧 在路由条件中恢复LLM响应内容 ({len(llm_response_content)} 字符)")
        
        # 🎯 调试：记录路由决策后的状态
        final_llm_content = state.get("_llm_response_content")
        self.logger.info(f"🔍 路由条件执行后:")
        self.logger.info(f"  - 决策结果: {decision}")
        self.logger.info(f"  - LLM响应内容存在: {bool(final_llm_content)}")
        if final_llm_content:
            self.logger.info(f"  - LLM响应内容长度: {len(final_llm_content)} 字符")
        
        return decision

    def _tool_node_wrapper(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """工具节点包装器 - 增强流式支持"""
        tool_name = state.get("tool_name")
        tool_params = state.get("tool_params", {})
        tool_call_id = state.get("tool_call_id_for_next_tool_message")
        
        if tool_name and self.stream_callback:
            # 🎯 获取工具显示名称，包括新的旅游工具
            tool_display_name = self.agent_core.get_tool_display_name(tool_name)
            
            # 发送工具调用开始事件
            self._send_stream_event('tool_call', f'正在调用工具: {tool_display_name}', {
                'call_id': tool_call_id or f'tool_{int(time.time())}',
                'tool_name': tool_name,
                'tool_display_name': tool_display_name,
                'params': tool_params
            })
        
        # 调用原始工具节点
        result = self.agent_core.node_manager.tool_node(state)
        
        # 🎯 特殊处理旅游工具的结果
        if tool_name and tool_name.startswith('travel_') and self.stream_callback:
            # 发送旅游规划特定事件
            messages = result.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    tool_result = str(last_message.content)
                    
                    # 🎯 对旅游工具结果进行特殊处理
                    if tool_name == 'travel_info_extractor':
                        self._send_stream_event('travel_analysis', '数据分析完成', {
                            'call_id': tool_call_id or f'tool_{int(time.time())}',
                            'analysis_result': tool_result[:500],
                            'full_result': tool_result
                        })
                    elif tool_name in ['travel_planner', 'itinerary_planner']:
                        self._send_stream_event('travel_plan', '行程规划完成', {
                            'call_id': tool_call_id or f'tool_{int(time.time())}',
                            'plan_preview': tool_result[:500],
                            'full_plan': tool_result
                        })
                    else:
                        self._send_stream_event('tool_result', tool_result[:500], {
                            'call_id': tool_call_id or f'tool_{int(time.time())}',
                            'tool_name': tool_name,
                            'result': tool_result
                        })
        elif tool_name and self.stream_callback:
            # 普通工具的结果处理
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

    def run_interactive_streaming(self, initial_query: str, session_id: str = None, max_iterations: int = 15):
        """流式版本的交互式运行"""
        self.logger.info(f"开始流式交互运行: {initial_query}")
        
        # 发送初始分析事件
        yield self._send_stream_event('thinking', '开始分析任务...', {'step_name': '任务分析'})
        
        # 🎯 修复：传递 session_id 参数
        result = self.run_interactive(initial_query, session_id, max_iterations)
        
        # 缓存结果供后续获取
        self.final_result_cache = result
        
        # 只在真正完成时发送final事件
        if not result.get('is_interactive_pause'):
            yield self._send_stream_event('final', '处理完成', {'step_name': '完成'})

    def get_final_result(self) -> Dict[str, Any]:
        """获取最终结果 - 确保包含议程信息"""
        if not hasattr(self, 'current_state') or not self.current_state:
            self.logger.warning("📋 [修复] current_state 不存在或为空")
            return {}
        
        # 🎯 关键修复：使用与 run_interactive 相同的格式化器
        result = self.formatter.format_final_response(cast(SimplerAgendaState, self.current_state))
        
        self.logger.info(f"📋 [修复] 最终结果 {result}")
        self.logger.info(f"📋 [修复] 最终回答: {result}")
        agenda_found = result.get('final_agenda') or result.get('agenda_doc') or result.get('updated_agenda_doc')
        self.logger.info(f"📋 [修复] 议程信息存在: {bool(agenda_found)}")
        
        return result
    
    def run_interactive(self, initial_query: str, session_id: str, max_iterations: int = 15):
        """运行交互式对话"""
        
        # 使用 SessionManager 初始化会话
        session_id, current_state_dict, existing_session = self.session_manager.initialize_session(
            initial_query, session_id
        )
        
        # 🎯 新增：检查是否为配置初始化请求
        if self._is_config_initialization(initial_query):
            result = self._handle_config_initialization(initial_query, session_id, current_state_dict)
            return result
        
        # 执行主循环
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
                # 🎯 关键修复：正确处理 invoke 的返回值
                # 当图正常结束时（如 action: finish），invoke的返回是最后一个节点的状态
                # 我们需要将这个最终状态与当前状态合并，以确保所有信息都保留
                output_state_dict = self.graph.invoke(current_state_dict, config=config)

                # 如果 invoke 返回了有效的状态，则更新
                if output_state_dict:
                    # 🎯 关键修复：保留LLM响应内容，防止在状态合并时丢失
                    llm_response_content = current_state_dict.get("_llm_response_content")
                    
                    # 🎯 调试：记录状态合并前的信息
                    current_drafts = current_state_dict.get("draft_outputs", {})
                    output_drafts = output_state_dict.get("draft_outputs", {})
                    self.logger.info(f"🔍 状态合并前:")
                    self.logger.info(f"  - current_state草稿数量: {len(current_drafts)}")
                    self.logger.info(f"  - output_state草稿数量: {len(output_drafts)}")
                    self.logger.info(f"  - current_state有LLM响应内容: {bool(llm_response_content)}")
                    self.logger.info(f"  - output_state有LLM响应内容: {bool(output_state_dict.get('_llm_response_content'))}")
                    
                    # 合并返回的状态，确保 action_needed, final_answer 等最终字段被更新
                    current_state_dict.update(output_state_dict)
                    
                    # 🎯 关键修复：如果原状态有LLM响应内容但新状态没有，则恢复
                    if llm_response_content and not current_state_dict.get("_llm_response_content"):
                        current_state_dict["_llm_response_content"] = llm_response_content
                        self.logger.info(f"🔧 恢复LLM响应内容到最终状态 ({len(llm_response_content)} 字符)")
                    
                    # 🎯 调试：记录状态合并后的信息
                    final_llm_content = current_state_dict.get("_llm_response_content")
                    self.logger.info(f"🔍 状态合并后:")
                    self.logger.info(f"  - 最终状态有LLM响应内容: {bool(final_llm_content)}")
                    if final_llm_content:
                        self.logger.info(f"  - LLM响应内容长度: {len(final_llm_content)} 字符")
                else:
                    # 理论上不应发生，但作为防护
                    self.logger.warning("Graph execution returned None, which is unexpected.")

                # 保存状态到数据库
                self.session_manager.save_session_state(session_id, current_state_dict)
                
                # 🎯 关键修复：保存工具消息到数据库
                self.session_manager.save_tool_messages(session_id, current_state_dict)
                
                # 检查结束条件
                if self.formatter.should_end_iteration(current_state_dict, i, self.logger):
                    self.logger.info("✅ 检测到结束条件，跳出循环")
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
        
        # 保存AI响应
        self.session_manager.save_ai_response(session_id, current_state_dict, initial_query)
        
        # 🎯 关键修复：保存当前状态供 get_final_result 使用
        self.current_state = current_state_dict

        result = self.formatter.format_final_response(cast(SimplerAgendaState, current_state_dict))
        result['session_id'] = session_id
        return result
    
    def _build_session_metadata(self, state: SimplerAgendaState) -> Dict[str, Any]:
        """构建会话元数据 - 防止None错误"""
        try:
            messages = state.get("messages", [])
            return {
                "message_count": len(messages),
                "tool_calls_made": len(state.get("recent_tool_calls", [])),
                "json_parse_errors": 0,
                "router_errors": 0
            }
        except Exception as e:
            self.logger.error(f"构建会话元数据失败: {e}")
            return {
                "message_count": 0,
                "tool_calls_made": 0,
                "json_parse_errors": 0,
                "router_errors": 0
            }
    
    def _is_config_initialization(self, query: str) -> bool:
        """检查是否为配置初始化请求"""
        try:
            import json
            data = json.loads(query)
            return isinstance(data, dict) and 'user_profile' in data
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _handle_config_initialization(self, query: str, session_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理配置初始化请求 - 修复根任务设置和JSON存储"""
        try:
            import json
            config_data = json.loads(query)
            
            user_profile = config_data.get('user_profile')
            writing_request = config_data.get('writing_request', '')  # 🎯 改为 writing_request
            writing_category = config_data.get('writing_category', 'reality')  # 🎯 新增写作类别
            
            self.logger.info(f"🎯 配置初始化数据: user_profile={user_profile}, writing_request={writing_request[:50]}..., category={writing_category}")
            
            # 🎯 生成开场白（现在返回文本，但内部缓存了JSON）
            opening_message = self._generate_opening_message(user_profile, writing_request)
            
            # 🎯 关键新增：获取缓存的JSON响应并保存到状态
            if hasattr(self, '_cached_opening_response') and self._cached_opening_response:
                cached_response = self._cached_opening_response
                if cached_response['json_response']:
                    # 保存完整的JSON响应到状态，供数据库存储使用
                    state["_llm_response_content"] = json.dumps(
                        cached_response['json_response'],
                        ensure_ascii=False,
                        indent=2
                    )
                    self.logger.info(f"✅ 开场白JSON响应已保存到状态")
                else:
                    # 如果JSON解析失败，保存原始响应
                    state["_llm_response_content"] = cached_response['raw_response']
                    self.logger.info(f"✅ 开场白原始响应已保存到状态")
            
            # 🎯 关键修复：设置正确的根任务和五阶段议程
            root_task = writing_request  # 使用完整的写作请求作为根任务
            initial_agenda = """# 故事大纲生成流程 @overall_goal：

- [ ] **阶段1: 核心概念与人物驱动** [待开始]
- [ ] **阶段2: 世界设定与激励事件** [待定]
- [ ] **阶段3: 结构发展与冲突升级** [待定]
- [ ] **阶段4: 危机、高潮与核心思想确认** [待定]
- [ ] **阶段5: 大纲生成与完善** [待定]"""
            
            # 更新状态
            state.update({
                'input_query': root_task,  # 🎯 关键：设置正确的根任务
                'user_profile': user_profile,
                'writing_request': writing_request,
                'writing_category': writing_category,
                'final_answer': opening_message,
                'is_interactive_pause': True,  # 🎯 关键：设置为暂停状态，触发ai_pause类型
                'action_needed': 'ask_human',  # 🎯 设置为询问用户
                'human_question': opening_message,  # 🎯 设置human_question
                'agenda_doc': f"{initial_agenda}"
            })
            
            # 保存状态
            self.session_manager.save_session_state(session_id, state)
            
            # 🎯 关键修复：手动调用save_ai_response来存储开场白
            self.session_manager.save_ai_response(session_id, state, query)
            self.logger.info(f"🎯 开场白已作为ai_pause类型存储到数据库")
            
            # 格式化响应
            result = self.formatter.format_final_response(cast(SimplerAgendaState, state))
            result['session_id'] = session_id
            
            self.logger.info(f"🎯 配置初始化完成，开场白将作为ai_pause类型存储")
            
            return result
            
        except Exception as e:
            self.logger.error(f"配置初始化失败: {e}")
            return {
                'final_answer': '配置初始化失败，请重试',
                'is_interactive_pause': False,
                'error_message': str(e),
                'session_id': session_id
            }
    
    def _generate_opening_message(self, user_profile: str, writing_request: str) -> str:
        """使用LLM生成个性化开场白 - 支持JSON格式和数据库存储"""
        try:
            # 🎯 修复：确保正确导入LLM
            from langchain_core.messages import SystemMessage, HumanMessage
            from langchain_openai import ChatOpenAI
            import os
            import json
            
            # 🎯 关键修复：从数据库获取真实的用户档案信息
            user_capabilities = {'description': '通用用户', 'display_name': '默认用户'}
            try:
                if self.database_manager:
                    # 直接从数据库获取用户档案
                    profile_data = self.database_manager.get_user_profile(user_profile)
                    if profile_data:
                        user_capabilities = {
                            'description': profile_data.get('overall_profile', '通用用户档案'),
                            'display_name': profile_data.get('display_name', profile_data.get('name', '用户')),
                            'experiment_group': profile_data.get('experiment_group', ''),
                            'user_type': profile_data.get('user_type', 'general')
                        }
                        self.logger.info(f"🎯 成功获取用户档案: {user_capabilities['display_name']}")
                    else:
                        self.logger.warning(f"数据库中未找到用户档案: {user_profile}")
                else:
                    self.logger.warning("数据库管理器不可用")
            except Exception as e:
                self.logger.warning(f"无法获取用户档案信息: {e}")
                # 🎯 保持原有的创意写作回退逻辑作为最后的备选
                if user_profile == 'user_student':
                    user_capabilities = {'description': '大学生，喜欢写日记和短文', 'display_name': '学生用户'}
                elif user_profile == 'user_office':
                    user_capabilities = {'description': '职场人士，业余时间喜欢写作', 'display_name': '职场用户'}
                elif user_profile == 'user_parent':
                    user_capabilities = {'description': '家长，喜欢写家庭故事', 'display_name': '家长用户'}
                elif user_profile == 'user_retiree':
                    user_capabilities = {'description': '退休教师，有丰富人生阅历', 'display_name': '退休用户'}
                else:
                    user_capabilities = {'description': '普通用户，对故事创作感兴趣', 'display_name': '通用用户'}
            
            # 🎯 修改：构建要求JSON输出的系统提示
            system_prompt = """你叫TATA，|一个人机协作完成任务的专业的AI协作者（此部分无需告知人类）|。请生成一个个性化的、易读的开场白。

⭐ **重要要求：请保持内容简洁明了，字数不要太长，语调温和亲切，让用户感到轻松愉快。避免过于正式或冗长的表达。**

请按照以下结构生成开场白，必须使用清晰的分段和列表格式：

**第一段：自我介绍** 
- 告知用户你的名字是TATA
- 说明接下来会一起完成故事大纲创作任务，直到完成实验问卷

**第二段：大纲写作创意拆解流程简介**
- 简要介绍你将通过五个阶段来协助完成故事大纲：核心概念与人物驱动，世界设定与激励事件，结构发展与冲突升级，危机高潮与核心思想确认，大纲生成与完善

**第三段：交互规则**
- 作为AI，你会主导创作进行，掌握故事理论、情节构思、角色设计能力
- 但需要人类帮助完成关键任务，请求配合
- **重要提示**：如果在任何环节想不出来或遇到困难，随时可以说"我不知道"、"帮我想想"、"给我提供一些素材"，我会主动协助你

**第四段：故事背景设定**
- 明确告知具体的故事背景设定（完整描述）
- 说明将基于这个背景共同创作故事大纲

**第五段：用户参与环节**
列出关键参与点：
• **创意决策参与**：深度创意挖掘、大纲生成确认、大纲优化反馈
• **质量保障参与**：因为AI可能犯错，需要帮助确认逻辑性、世界观一致性、创作潜力利用、主题表达、个人偏好匹配

**第六段：开始邀请**
- 引导用户"如果准备好了，请告诉我，我们就可以开始了~☺️"

**格式要求：使用换行符\\n、emoji、加粗标记**，确保结构清晰易读。

**重要：你必须严格按照以下JSON格式输出：**
{
    "human_question": "你的完整开场白内容，必须使用换行符\\n和列表格式，结构清晰易读。例如：\\n\\n🎯 **我是TATA**\\n你好！我是TATA，与你一起完成故事大纲创作任务的AI协作者。\\n\\n🧠 **五阶段创作流程**\\n我将通过五个阶段来协助你：核心概念与人物驱动→世界设定与激励事件→结构发展与冲突升级→危机高潮与核心思想确认→大纲生成与完善\\n\\n📚 **交互规则**\\n- 作为AI，我将主导创作过程，运用故事理论、情节构思和角色设计能力\\n- 但我需要你的帮助来完成关键任务，请你多多配合\\n\\n📖 **故事背景设定：**\\n[具体背景设定]\\n\\n✨ **你需要参与的环节：**\\n• **创意决策参与**：核心概念确定、冲突升级设计、大纲生成确认、大纲优化反馈\\n• **质量保障参与**：帮助确认逻辑性、世界观一致性、创作潜力利用、主题表达、个人偏好匹配\\n\\n🤝 **开始创作**\\n如果准备好了，请告诉我，我们就可以开始了~☺️",
    "why_need_human": "Cognitive judgment|Creativity|External world interaction|Domain expertise knowledge|Private domain information|Preference constraints|Responsibility scope|User-authorizable content（多选，需多样性大）",
    "when_need_human": "Decision-making needs|Innovation needs|Execution needs|Professional knowledge needs|Private information needs|Personal preference needs|Responsibility assumption needs|User authorization needs（多选，需多样性大）",
    "interaction_behavior": "Prime|Configure|Probe|Cue|Elicit|Augment|Guide|Explain|Correct|Reflect|Approve（多选，需多样性大）",
    "communication_principle": "Echoing responses|Casual language|Feedback|Using emoji|Emphatic messages|Humor|Present capabilities|Acknowledge limitations|Repetitive messages|Exaggeration（多选，需多样性大）"
}"""

            # 构建用户提示 - 使用个性化档案信息（不显示用户姓名）
            user_prompt = f"""用户档案描述：{user_capabilities.get('description')}
接下来，你们会一起完成的故事大纲创作任务的具体背景设定是：{writing_request}

请在开场白中：
1. 明确告知用户这个具体的故事背景设定
2. 解释你们将基于这个背景来共同创作故事大纲
3. 让用户了解这个背景设定的创作可能性和挑战

请根据用户的具体档案特征和故事背景设定生成一个个性化的开场白，严格按照JSON格式输出。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 调用LLM
            self.logger.info(f"prompt: {user_prompt}")
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
            llm = ChatOpenAI(model=model_name, temperature=0.7,max_retries=3,request_timeout=40)
            response = llm.invoke(messages)
            
            # 🎯 新增：解析JSON响应并缓存
            try:
                response_content = response.content.strip()
                
                # 处理可能的```json包装
                if '```json' in response_content:
                    start = response_content.find('```json') + 7
                    end = response_content.find('```', start)
                    if end > start:
                        json_content = response_content[start:end].strip()
                    else:
                        json_content = response_content
                else:
                    json_content = response_content
                
                parsed_response = json.loads(json_content)
                
                # 🎯 关键：缓存完整的JSON响应供后续使用
                self._cached_opening_response = {
                    'json_response': parsed_response,
                    'raw_response': response_content
                }
                
                # 返回human_question作为开场白文本
                opening_text = parsed_response.get('human_question', response_content)
                self.logger.info(f"✅ AI开场白JSON解析成功")
                return opening_text
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"⚠️ JSON解析失败，使用原始响应: {e}")
                # 回退处理
                self._cached_opening_response = {
                    'json_response': None,
                    'raw_response': response.content
                }
                return response.content
            
        except Exception as e:
            self.logger.error(f"生成开场白失败: {e}")
            # 🎯 提供结构化的默认回退
            default_response = {
                "human_question": f"您好！我是TATA，您的故事大纲助手。我注意到您对 **{writing_request}** 很感兴趣。请告诉我您的具体需求，我会为您提供专业的建议和支持。",
                "why_need_human": "Cognitive judgment|Creativity|Domain expertise knowledge|Preference constraints",
                "when_need_human": "Decision-making needs|Innovation needs|Professional knowledge needs|Personal preference needs",
                "interaction_behavior": "Prime|Configure|Probe|Guide|Explain",
                "communication_principle": "Casual language|Feedback|Using emoji|Present capabilities|Acknowledge limitations"
            }
            self._cached_opening_response = {
                'json_response': default_response,
                'raw_response': json.dumps(default_response, ensure_ascii=False)
            }
            return default_response['human_question']


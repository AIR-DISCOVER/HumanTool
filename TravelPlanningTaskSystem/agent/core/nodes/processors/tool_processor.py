"""
工具处理器
"""
import time
from typing import Dict, Any, cast
from langchain_core.messages import ToolMessage
from ...state import SimplerAgendaState
from .utils.context_builder import ContextBuilder
from ....utils.city_validator import validate_and_correct_tool_params

class ToolProcessor:
    """工具处理器 - 处理工具执行"""
    
    def __init__(self, tools: Dict, logger, stream_callback=None):
        self.tools = tools
        self.logger = logger
        self.stream_callback = stream_callback
        self.sent_tool_events = set()
        self.recent_tool_calls = []
        # 🎯 新增：上下文构建器初始化
        self.context_builder = ContextBuilder(logger)

    def set_stream_callback(self, callback):
        """设置流式回调"""
        self.stream_callback = callback
    
    def process(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """处理工具执行 - 增强循环检测和中断机制"""
        tool_name = state.get("tool_name")
        tool_params = state.get("tool_params", {})
        
        if not tool_name:
            return self._handle_no_tool_error(state)
        
        if tool_name not in self.tools:
            return self._handle_unknown_tool_error(state, tool_name)
        
        # 🎯 增强的循环检测 - 检查连续失败
        if self._is_in_failure_loop(tool_name, tool_params):
            self.logger.warning(f"检测到 {tool_name} 工具陷入失败循环，强制转为用户交互")
            return self._handle_failure_loop(state, tool_name)
        
        # 原有的重复检测
        if self._is_meaningless_duplicate(tool_name, tool_params):
            return self._handle_duplicate_tool_execution(state, tool_name)
        
        # 记录工具调用
        self._record_tool_call(tool_name, tool_params)
        
        # 执行工具
        tool_call_id = state.get("tool_call_id_for_next_tool_message") or f"call_{tool_name}_{int(time.time())}"
        return self._execute_tool(state, tool_name, tool_params, tool_call_id)

    def _is_in_failure_loop(self, tool_name: str, tool_params: dict) -> bool:
        """检测是否陷入失败循环"""
        # 检查最近3次相同工具的调用结果
        recent_failures = 0
        current_task = tool_params.get("task_description", "").strip().lower()
        
        for call in self.recent_tool_calls[-3:]:
            if (call['tool_name'] == tool_name and 
                self._tasks_are_similar(current_task, call['params'].get("task_description", "").strip().lower()) and
                call.get('result_quality') == 'low'):
                recent_failures += 1
        
        # 如果最近3次相同任务都是低质量结果，认为是失败循环
        is_loop = recent_failures >= 2
        if is_loop:
            self.logger.warning(f"检测到失败循环: {tool_name} 连续 {recent_failures} 次低质量结果")
        
        return is_loop

    def _handle_failure_loop(self, state: SimplerAgendaState, tool_name: str) -> SimplerAgendaState:
        """处理失败循环 - 强制转为用户交互"""
        tool_display_name = self.get_display_name(tool_name)
        
        # 分析失败原因并给出具体建议
        failure_reason = "信息不足"
        if tool_name == "llm_general":
            recent_results = [call.get('result', '') for call in self.recent_tool_calls[-3:] 
                             if call['tool_name'] == tool_name]
            if any("请提供" in result for result in recent_results):
                failure_reason = "缺少关键信息"
        
        new_state = {**state}
        new_state.update({
            "action_needed": "ask_human",
            "human_question": f"我尝试使用{tool_display_name}来完成任务，但遇到了{failure_reason}的问题。为了更好地帮助您，请提供一些具体信息：\n\n1. 您希望我重点关注哪些方面？\n2. 有什么特殊要求或偏好？\n3. 是否需要调整任务的方向或范围？",
            "tool_name": None,
            "tool_params": None,
            "tool_call_id_for_next_tool_message": None,
            "loop_break_reason": f"检测到{tool_name}工具失败循环，转为用户交互"
        })
        
        return cast(SimplerAgendaState, new_state)

    def _is_meaningless_duplicate(self, tool_name: str, tool_params: dict) -> bool:
        """检查是否是无意义的重复调用"""
        # 只检查最近的3次调用
        recent_calls = [call for call in self.recent_tool_calls[-3:] if call['tool_name'] == tool_name]
        
        if not recent_calls:
            return False  # 没有最近的相同工具调用
        
        current_task = tool_params.get("task_description", "").strip().lower()
        
        for recent_call in recent_calls:
            recent_task = recent_call['params'].get("task_description", "").strip().lower()
            
            # 🎯 检查任务描述是否有显著差异
            if self._tasks_are_similar(current_task, recent_task):
                # 对于图片生成工具，额外检查风格和尺寸参数
                if tool_name == "image_generator":
                    if not self._image_params_different(tool_params, recent_call['params']):
                        self.logger.info(f"检测到相似的{tool_name}调用: '{current_task[:50]}...' vs '{recent_task[:50]}...'")
                        return True
                # 对于其他工具，主要看任务描述
                else:
                    self.logger.info(f"检测到相似的{tool_name}调用: '{current_task[:50]}...' vs '{recent_task[:50]}...'")
                    return True
        
        return False

    def _tasks_are_similar(self, task1: str, task2: str) -> bool:
        """判断两个任务描述是否相似"""
        if not task1 or not task2:
            return False
        
        # 如果任务描述完全相同
        if task1 == task2:
            return True
        
        # 如果任务描述长度都很短且高度相似
        if len(task1) < 50 and len(task2) < 50:
            # 计算简单的相似度
            common_words = set(task1.split()) & set(task2.split())
            if len(common_words) > len(task1.split()) * 0.7:  # 70%以上的词汇重叠
                return True
        
        # 检查是否是明显的重复表述
        similarity_indicators = [
            "制定", "规划", "生成", "创作", "分析", "写", "画", "设计"
        ]
        
        task1_indicators = [ind for ind in similarity_indicators if ind in task1]
        task2_indicators = [ind for ind in similarity_indicators if ind in task2]
        
        # 如果动作词相同且核心内容相似
        if task1_indicators and task1_indicators == task2_indicators:
            # 进一步检查核心关键词
            task1_words = set(task1.replace("，", " ").replace("。", " ").split())
            task2_words = set(task2.replace("，", " ").replace("。", " ").split())
            common_ratio = len(task1_words & task2_words) / max(len(task1_words), len(task2_words), 1)
            
            if common_ratio > 0.6:  # 60%以上的关键词重叠
                return True
        
        return False

    def _image_params_different(self, params1: dict, params2: dict) -> bool:
        """检查图片生成参数是否有显著差异"""
        # 检查风格是否不同
        style1 = params1.get("image_style", "realistic")
        style2 = params2.get("image_style", "realistic")
        
        # 检查尺寸是否不同
        size1 = params1.get("image_size", "1024x1024")
        size2 = params2.get("image_size", "1024x1024")
        
        # 如果风格或尺寸不同，认为是有差异的调用
        return style1 != style2 or size1 != size2

    def _record_tool_call(self, tool_name: str, tool_params: dict):
        """记录工具调用 - 增加结果质量跟踪"""
        call_record = {
            'tool_name': tool_name,
            'params': tool_params.copy(),
            'timestamp': time.time(),
            'result': None,  # 执行后填充
            'result_quality': None  # 执行后填充
        }
        
        self.recent_tool_calls.append(call_record)
        
        # 保持最近10次调用记录
        if len(self.recent_tool_calls) > 10:
            self.recent_tool_calls.pop(0)

    def _execute_tool(self, state: SimplerAgendaState, tool_name: str, 
                     tool_params: Dict, tool_call_id: str) -> SimplerAgendaState:
        """执行工具 - 增加历史记录传递"""
        tool_execution_id = f"{tool_name}_{hash(str(tool_params))}_{tool_call_id}"
        
        if tool_execution_id in self.sent_tool_events:
            self.logger.warning(f"跳过重复的工具执行: {tool_name}")
            return state
        
        self.sent_tool_events.add(tool_execution_id)

        self.logger.info(f"执行工具: {tool_name}")
        self.logger.info(f"工具参数: {tool_params}")

        # 🎯 修复：移除此处的事件发送，统一在 graph.py 的包装器中处理
        # if self.stream_callback:
        #     self.emit_tool_call(tool_name, tool_params, {
        #         "call_id": tool_call_id,
        #         "execution_id": tool_execution_id
        #     })

        # 🎯 关键修改：为LLM工具增强上下文
        enhanced_params = self._enhance_tool_params_with_history(state, tool_name, tool_params)
        self.logger.info(f"**=> 增强后的工具参数: {enhanced_params}")

        # 🎯 新增：验证和修正城市名称参数
        validated_params = validate_and_correct_tool_params(enhanced_params)
        if validated_params != enhanced_params:
            self.logger.info(f"**=> 城市名称已修正，最终工具参数: {validated_params}")
        else:
            validated_params = enhanced_params

        # 执行工具
        result = self.tools[tool_name].execute(**validated_params)
        result_quality = self.assess_result_quality(tool_name, result, tool_params)
        
        # 更新最近调用记录的结果质量
        if self.recent_tool_calls:
            self.recent_tool_calls[-1]['result'] = result
            self.recent_tool_calls[-1]['result_quality'] = result_quality
        
        if result_quality == "low":
            self.logger.warning(f"工具 {tool_name} 返回了低质量结果")
        
        self.logger.info(f"工具执行完成，结果长度: {len(result)}")

        # 发送工具结果事件
        if self.stream_callback:
            self.emit_tool_result(tool_name, result, {
                "call_id": tool_call_id,
                "execution_id": tool_execution_id
            })

        # 自动保存结果
        auto_saved_id = self.auto_save_result(state, tool_name, tool_params, result)

        # 更新状态
        return self._update_state_after_tool_execution(
            state, result, tool_call_id, tool_name, auto_saved_id
        )
    
    def _update_state_after_tool_execution(self, state: SimplerAgendaState, result: str,
                                         tool_call_id: str, tool_name: str,
                                         auto_saved_id: str = None) -> SimplerAgendaState:
        """工具执行后更新状态"""
        new_state = {**state}
        
        self.logger.info(f"[DEBUG] _update_state_after_tool_execution: auto_saved_id={auto_saved_id}")
        self.logger.info(f"[DEBUG] 当前state中的draft_outputs: {state.get('draft_outputs', {})}")
        
        # 添加工具消息到历史
        if not isinstance(new_state.get("messages"), list):
            new_state["messages"] = []
        
        new_state["messages"].append(ToolMessage(
            content=result,
            tool_call_id=tool_call_id or f"call_{tool_name}_{int(time.time())}"
        ))

        # 清除工具调用状态，准备下一步规划
        new_state.update({
            "action_needed": "self_update",
            "tool_name": None,
            "tool_params": None,
            "tool_call_id_for_next_tool_message": None
        })

        # 🎯 确保draft_outputs被正确传递
        if "draft_outputs" in state:
            new_state["draft_outputs"] = state["draft_outputs"]
            self.logger.info(f"[DEBUG] 传递draft_outputs到新状态: {list(new_state['draft_outputs'].keys())}")

        # 添加自动保存信息
        if auto_saved_id:
            new_state["last_auto_saved_draft"] = auto_saved_id

        return cast(SimplerAgendaState, new_state)
    
    def assess_result_quality(self, tool_name: str, result: str, params: Dict) -> str:
        """评估工具结果质量 - 增强检测"""
        result_lower = result.lower()
        
        # 检查是否是无效结果
        low_quality_indicators = [
            "请提供", "需要更多信息", "无法", "抱歉", 
            "please provide", "需要您", "缺少", "不够清楚",
            "为了", "我们需要了解"  # 🎯 新增
        ]
        
        if any(indicator in result_lower for indicator in low_quality_indicators):
            return "low"
        
        # 检查结果长度 - 调整阈值
        if len(result) < 100:  # 从50提高到100
            return "low"
        
        # 🎯 新增：检查是否是循环性的请求信息
        if (result_lower.count("提供") > 2 or 
            result_lower.count("需要") > 2 or
            "请" in result_lower and len(result) < 200):
            return "low"
        
        return "high"
    
    def auto_save_result(self, state, tool_name: str, params: Dict, result: str) -> str:
        """自动保存工具结果"""
        self.logger.info(f"[DEBUG] auto_save_result 被调用: tool_name={tool_name}, result_length={len(result)}")
        
        # 检查是否是值得保存的内容
        has_error_phrases = any(phrase in result.lower() for phrase in [
            "请提供", "需要更多信息", "无法", "错误", "抱歉"
        ])
        
        self.logger.info(f"[DEBUG] 结果长度: {len(result)}, 包含错误短语: {has_error_phrases}")
        
        if len(result) > 100 and not has_error_phrases:
            # 生成基于工具名称和时间的任务ID
            timestamp = int(time.time()) % 10000
            task_id = f"{tool_name}_{timestamp}"
            
            # 保存到草稿
            if "draft_outputs" not in state:
                state["draft_outputs"] = {}
                self.logger.info(f"[DEBUG] 初始化 draft_outputs")
            
            state["draft_outputs"][task_id] = result
            self.logger.info(f"[DEBUG] 自动保存工具结果到草稿: {task_id} ({len(result)} 字符)")
            self.logger.info(f"[DEBUG] 当前 draft_outputs 包含: {list(state['draft_outputs'].keys())}")
            
            return task_id
        else:
            self.logger.info(f"[DEBUG] 工具结果不符合保存条件，跳过保存")
            return None
    
    def get_display_name(self, tool_name: str) -> str:
        """获取工具显示名称"""
        display_names = {
            "knowledge_analyzer": "知识分析器",
            "story_brainstorm": "故事头脑风暴",
            "plot_developer": "情节开发器",
            "longform_writer": "长篇写作器",
            # "dialogue_writer": "对话写作器",
            # "logic_checker": "逻辑检查器",
            # "style_enhancer": "风格增强器",
            # "image_generator": "AI画师 🎨",
            "travel_planner": "专业旅游规划器 🗺️",
            "travel_info_extractor": "旅游信息提取器 📊",
            "itinerary_planner": "高级旅游规划器 ✨",
            "accommodation_planner": "住宿规划器 🏨",
            "attraction_planner": "景点规划器 🎯",
            "restaurant_planner": "餐饮规划器 🍽️"
        }
        return display_names.get(tool_name, tool_name)
    
    def emit_tool_call(self, tool_name: str, params: Dict, metadata: Dict):
        """发送工具调用事件 - 避免重复"""
        execution_id = metadata.get("execution_id")
        if execution_id and f"call_{execution_id}" in getattr(self, '_sent_call_events', set()):
            return  # 跳过重复的调用事件
        
        if not hasattr(self, '_sent_call_events'):
            self._sent_call_events = set()
        
        if execution_id:
            self._sent_call_events.add(f"call_{execution_id}")
        
        if self.stream_callback:
            try:
                call_message = f"正在调用工具: {tool_name}"
                self.stream_callback("tool_call", call_message, {
                    "tool_name": tool_name,
                    "params": params,
                    "call_id": metadata.get("call_id"),
                    "tool_display_name": self.get_display_name(tool_name),
                    "status": "calling"
                })
            except Exception as e:
                self.logger.error(f"发送工具调用事件失败: {e}")

    def emit_tool_result(self, tool_name: str, result: str, metadata: Dict):
        """发送工具结果事件 - 避免重复"""
        execution_id = metadata.get("execution_id")
        if execution_id and f"result_{execution_id}" in getattr(self, '_sent_result_events', set()):
            return  # 跳过重复的结果事件
        
        if not hasattr(self, '_sent_result_events'):
            self._sent_result_events = set()
        
        if execution_id:
            self._sent_result_events.add(f"result_{execution_id}")
        
        if self.stream_callback:
            try:
                self.stream_callback("tool_result", result, {
                    "tool_name": tool_name,
                    "result": result,
                    "call_id": metadata.get("call_id"),
                    "tool_display_name": self.get_display_name(tool_name),
                    "status": "completed"
                })
            except Exception as e:
                self.logger.error(f"发送工具结果事件失败: {e}")
    
    def _handle_no_tool_error(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """处理无工具错误"""
        self.logger.warning("工具节点：没有指定工具名称")
        return cast(SimplerAgendaState, {
            **state,
            "error_message": "没有指定要调用的工具",
            "action_needed": "self_update"
        })
    
    def _handle_unknown_tool_error(self, state: SimplerAgendaState, tool_name: str) -> SimplerAgendaState:
        """处理未知工具错误"""
        self.logger.error(f"工具节点：未知工具 '{tool_name}'")
        return cast(SimplerAgendaState, {
            **state,
            "error_message": f"未知工具: {tool_name}",
            "action_needed": "self_update"
        })
    
    def _handle_execution_error(self, state: SimplerAgendaState, error: Exception) -> SimplerAgendaState:
        """处理执行错误"""
        self.logger.error(f"工具执行失败: {error}")
        return cast(SimplerAgendaState, {
            **state,
            "error_message": f"工具执行失败: {str(error)}",
            "action_needed": "self_update",
            "tool_name": None,
            "tool_params": None,
            "tool_call_id_for_next_tool_message": None
        })
    
    def _create_execution_signature(self, tool_name: str, tool_params: dict, state: SimplerAgendaState) -> str:
        """创建工具执行签名 - 用于检测重复"""
        import hashlib
        import json
        
        # 获取最近几条消息的内容作为上下文
        messages = state.get("messages", [])
        recent_context = ""
        if len(messages) >= 2:
            recent_messages = messages[-2:]
            # 🎯 修复：增加上下文长度限制
            recent_context = "".join([str(getattr(msg, 'content', ''))[:300] for msg in recent_messages])  # 从100增加到300
        
        # 创建签名内容
        signature_data = {
            "tool_name": tool_name,
            # 🎯 修复：增加任务描述的保留长度
            "task_description": tool_params.get("task_description", "")[:500],  # 从200增加到500
            "context_hash": hashlib.md5(recent_context.encode()).hexdigest()[:8]
        }
        
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def _handle_duplicate_tool_execution(self, state: SimplerAgendaState, tool_name: str) -> SimplerAgendaState:
        """处理重复工具执行 - 提供更友好的提示"""
        self.logger.info(f"无意义重复工具执行 {tool_name} 被阻止，转为用户交互")
        
        # 获取工具显示名称
        tool_display_name = self.get_display_name(tool_name)
        
        new_state = {**state}
        new_state.update({
            "action_needed": "ask_human",
            "human_question": f"我刚刚已经使用了{tool_display_name}。您是希望调整之前的结果，还是有新的不同需求？请具体说明您的想法。",
            "tool_name": None,
            "tool_params": None,
            "tool_call_id_for_next_tool_message": None,
            "is_interactive_pause": True  # 强制暂停
        })
        
        return cast(SimplerAgendaState, new_state)

    def _enhance_tool_params_with_history(self, state: SimplerAgendaState, 
                                        tool_name: str, tool_params: Dict) -> Dict:
        """为工具参数增加历史上下文"""
        # 🎯 只为LLM类型工具添加历史记录，并且扩展支持的工具类型
        llm_tools = ['llm_general', 'knowledge_analyzer', 'llm_thinking',
                    'travel_info_extractor', 'travel_planner', 'itinerary_planner',
                    'accommodation_planner', 'attraction_planner', 'restaurant_planner']  # 🎯 添加专门旅游工具
        
        self.logger.info(f"[DEBUG] 工具名称: {tool_name}, 是否为LLM工具: {tool_name in llm_tools}")
        
        if tool_name in llm_tools:
            return self.context_builder.build_enhanced_tool_context_with_history(state, tool_params)
        else:
            # 其他工具保持原有参数，不进行任何截断
            return tool_params
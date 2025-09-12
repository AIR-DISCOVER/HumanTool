import uuid
import re
import json 
import time
from typing import Dict, Any, List, cast
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from .state import SimplerAgendaState
from ..utils.logger import Logger
from ..utils.json_parser import JSONParser

class NodeManager:
    def __init__(self, llm, tools, logger, json_parser):
        self.llm = llm
        self.tools = tools
        self.logger = logger
        self.json_parser = json_parser
        self.stream_callback = None
        self.prompt_manager = None  # 需要在外部设置
    
    def set_stream_callback(self, callback):
        """设置流式回调"""
        self.stream_callback = callback
        
    def set_prompt_manager(self, prompt_manager):
        """设置 prompt_manager"""
        self.prompt_manager = prompt_manager
    
    def router_node(self, state) -> dict:
        """路由节点 - 新增方法"""
        self.logger.info("--- Router Node ---")
        
        try:
            action = state.get("action_needed")
            self.logger.info(f"Router: 检测到action = {action}")
            
            # 根据action决定下一步
            if action == "call_tool":
                tool_name = state.get("tool_name")
                if tool_name:
                    self.logger.info(f"Router: 准备调用工具 {tool_name}")
                    return state
                else:
                    self.logger.warning("Router: call_tool但未指定工具")
                    new_state = dict(state)
                    new_state["action_needed"] = "finish"
                    new_state["final_answer"] = "工具调用配置有误"
                    return new_state
                    
            elif action == "ask_human":
                human_question = state.get("human_question")
                if human_question:
                    self.logger.info(f"Router: 准备询问用户")
                    new_state = dict(state)
                    new_state["is_interactive_pause"] = True
                    new_state["final_answer"] = human_question
                    return new_state
                else:
                    self.logger.warning("Router: ask_human但未提供问题")
                    new_state = dict(state)
                    new_state["action_needed"] = "finish"
                    new_state["final_answer"] = "系统准备询问但未配置问题"
                    return new_state
                    
            elif action == "finish":
                self.logger.info("Router: 任务完成")
                final_answer = state.get("final_answer", "任务已完成")
                new_state = dict(state)
                new_state["final_answer"] = final_answer
                return new_state
                
            else:
                self.logger.warning(f"Router: 未知action {action}")
                new_state = dict(state)
                new_state["action_needed"] = "finish"
                new_state["final_answer"] = "处理完成"
                return new_state
                
        except Exception as e:
            self.logger.error(f"Router节点错误: {e}")
            new_state = dict(state)
            new_state["action_needed"] = "finish"
            new_state["final_answer"] = f"路由处理出错: {str(e)}"
            return new_state
    
    def initializer_node(self, state: SimplerAgendaState, system_prompt: str) -> SimplerAgendaState:
        """初始化节点"""
        self.logger.info("--- Initializer Node ---")
        
        is_first_invocation = not state.get("messages")
        
        if is_first_invocation:
            self.logger.info("首次调用，进行初始化")
            initial_query = state["input_query"]
            initial_agenda = f"- [ ] {initial_query} @overall_goal"
            
            return cast(SimplerAgendaState, {
                "input_query": initial_query,
                "agenda_doc": initial_agenda,
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=f"我的任务是: {initial_query}")
                ],
                "last_response": state.get("last_response"),
                "action_needed": state.get("action_needed"),
                "tool_name": state.get("tool_name"),
                "tool_params": state.get("tool_params"),
                "human_question": state.get("human_question"),
                "final_answer": state.get("final_answer"),
                "error_message": state.get("error_message"),
                "tool_call_id_for_next_tool_message": None,
                "draft_outputs": {},
            })
        else:
            self.logger.info("非首次调用，直接传递状态")
            return state
    
    def planner_node(self, state):
        """规划节点 - 增强重复检测"""
        self.logger.info("--- Planner Node ---")
        
        try:
            # 检查 prompt_manager
            if not self.prompt_manager:
                self.logger.error("规划节点错误: prompt_manager 未设置")
                new_state = dict(state)
                new_state["error_message"] = "规划节点配置错误"
                new_state["action_needed"] = "finish"
                new_state["final_answer"] = "系统配置有误，请重试"
                return new_state
            
            # 检查是否已有足够的工具执行结果
            messages = state.get("messages", [])
            tool_result_count = sum(1 for msg in messages if hasattr(msg, 'tool_call_id'))
            
            if tool_result_count >= 2:  # 如果已经有2个或更多工具结果
                self.logger.info(f"检测到{tool_result_count}个工具结果，强制转向用户交互")
                new_state = dict(state)
                new_state["action_needed"] = "ask_human"
                new_state["human_question"] = "我已经为您生成了一些创作内容。您觉得怎么样？希望我在哪个方面进一步完善吗？"
                new_state["tool_name"] = None
                new_state["tool_params"] = None
                return new_state
            
            # 构建提示
            prompt = self.prompt_manager.get_planner_prompt(state) 
            
            # 获取LLM响应
            response = self.llm.invoke(prompt)
            self.logger.info(f"Planner response type: {type(response)}")
            
            # 解析响应
            new_state = dict(state)
            
            # 处理消息历史
            if not isinstance(new_state.get("messages"), list):
                new_state["messages"] = []
            new_state["messages"].append(response)
            
            # 尝试解析JSON响应
            content = response.content if hasattr(response, 'content') else str(response)
            
            try:
                # 提取JSON部分
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 尝试直接解析整个内容
                    json_str = content
                
                parsed = json.loads(json_str)
                
                # 强制检查是否试图重复调用工具
                planned_action = parsed.get("next_action")
                planned_tool = parsed.get("tool_name")
                
                if planned_action == "call_tool" and planned_tool:
                    # 强制重复检测
                    if self._is_recent_duplicate_tool_call(state, planned_tool, {}):
                        self.logger.warning(f"强制阻止重复工具调用: {planned_tool}")
                        parsed["next_action"] = "ask_human"
                        parsed["tool_name"] = None
                        parsed["tool_params"] = {}
                        parsed["human_question"] = f"我刚刚已经使用了{planned_tool}工具生成了内容。您对结果满意吗？希望我在哪方面进一步完善？"
                
                # 更新状态
                new_state["agenda_doc"] = parsed.get("updated_agenda_doc", state.get("agenda_doc", ""))
                new_state["action_needed"] = parsed.get("next_action", "ask_human")
                new_state["tool_name"] = parsed.get("tool_name")
                new_state["tool_params"] = parsed.get("tool_params", {})
                new_state["human_question"] = parsed.get("human_question")
                new_state["final_answer"] = parsed.get("final_answer")
                
                # 如果需要工具调用，生成工具调用ID
                if new_state["action_needed"] == "call_tool" and new_state["tool_name"]:
                    import uuid
                    new_state["tool_call_id_for_next_tool_message"] = str(uuid.uuid4())
                
                self.logger.info(f"规划完成: action={new_state['action_needed']}, tool={new_state.get('tool_name')}")
                
            except (json.JSONDecodeError, AttributeError) as e:
                self.logger.warning(f"JSON解析失败: {e}")
                # 如果已有工具结果，转向用户交互
                if tool_result_count > 0:
                    new_state["action_needed"] = "ask_human"
                    new_state["human_question"] = "我已经为您准备了一些内容。您希望我如何继续？"
                else:
                    new_state["action_needed"] = "finish"
                    new_state["final_answer"] = content[:500] + "..." if len(content) > 500 else content
            
            return new_state
            
        except Exception as e:
            self.logger.error(f"规划节点错误: {e}")
            import traceback
            traceback.print_exc()
            
            new_state = dict(state)
            new_state["error_message"] = f"规划节点错误: {str(e)}"
            new_state["action_needed"] = "finish"
            new_state["final_answer"] = "规划过程出现问题，请重试"
            return new_state
    
    def tool_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """工具执行节点 - 增强结果处理"""
        tool_name = state.get("tool_name")
        tool_params = state.get("tool_params", {})
        tool_call_id = state.get("tool_call_id_for_next_tool_message")

        if not tool_name:
            self.logger.warning("工具节点：没有指定工具名称")
            return cast(SimplerAgendaState, {
                **state,
                "error_message": "没有指定要调用的工具",
                "action_needed": "self_update"
            })

        if tool_name not in self.tools:
            self.logger.error(f"工具节点：未知工具 '{tool_name}'")
            return cast(SimplerAgendaState, {
                **state,
                "error_message": f"未知工具: {tool_name}",
                "action_needed": "self_update"
            })

        try:
            self.logger.info(f"执行工具: {tool_name}")
            self.logger.info(f"工具参数: {tool_params}")

            # 执行工具 - 修复参数传递
            if self.stream_callback:
                self._emit_tool_call(tool_name, tool_params, {"call_id": tool_call_id})

            result = self.tools[tool_name].execute(**tool_params)
            
            # 检查工具结果质量
            result_quality = self._assess_tool_result_quality(tool_name, result, tool_params)
            
            if result_quality == "low":
                self.logger.warning(f"工具 {tool_name} 返回了低质量结果，可能需要调整参数")
            
            self.logger.info(f"工具执行完成，结果长度: {len(result)}")

            # 发送工具结果 - 修复参数传递
            if self.stream_callback:
                self._emit_tool_result(tool_name, result, {"call_id": tool_call_id})

            # 自动保存有价值的工具结果
            auto_saved_id = self._auto_save_tool_result(state, tool_name, tool_params, result)

            # 更新状态
            new_state = {**state}
            
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

            # 如果自动保存了结果，添加到状态中
            if auto_saved_id:
                new_state["last_auto_saved_draft"] = auto_saved_id

            return cast(SimplerAgendaState, new_state)

        except Exception as e:
            self.logger.error(f"工具执行失败: {e}")
            return cast(SimplerAgendaState, {
                **state,
                "error_message": f"工具执行失败: {str(e)}",
                "action_needed": "self_update",
                "tool_name": None,
                "tool_params": None,
                "tool_call_id_for_next_tool_message": None
            })

    def _assess_tool_result_quality(self, tool_name: str, result: str, params: Dict) -> str:
        """评估工具结果质量"""
        result_lower = result.lower()
        
        # 检查是否是无效结果
        low_quality_indicators = [
            "请提供", "需要更多信息", "无法", "抱歉", 
            "please provide", "需要您", "缺少", "不够清楚"
        ]
        
        if any(indicator in result_lower for indicator in low_quality_indicators):
            return "low"
        
        # 检查结果长度
        if len(result) < 50:
            return "low"
        
        # 针对特定工具的检查
        if tool_name == "style_enhancer" and "请提供" in result:
            return "low"
        
        if tool_name == "dialogue_writer" and len(result) < 200:
            return "low"
        
        return "high"

    def _build_planner_prompt(self, state: SimplerAgendaState) -> str:
        """构建规划节点的输入提示"""
        parts = []
        parts.append(f"当前的议程是:\n---\n{state['agenda_doc']}\n请参考议程，已经获取的信息*不要删除*。---")
        
        # 添加草稿内容
        draft_outputs = state.get("draft_outputs", {})
        if draft_outputs:
            draft_list = []
            for task_id, content in draft_outputs.items():
                if "故事" in task_id.lower() or "分析" in task_id.lower():
                    content_preview = content
                else:
                    content_preview = content[:200] + "..." if len(content) > 200 else content
                draft_list.append(f"### {task_id}\n{content_preview}\n")
            
            draft_summary = "\n".join(draft_list)
            parts.append(f"## 以下是已存储的草稿内容:\n{draft_summary}\n\n**重要提示：这些草稿内容是之前生成的有价值内容，请优先考虑使用它们，避免重复创建相似内容。如果你要在最终答案中使用这些内容，请使用 `use_draft_contents` 字段指定内容ID。**")
        
        # 处理用户反馈
        if state.get("last_response"):
            last_response = state["last_response"]
            if "用户回答了问题" in last_response:
                user_response = last_response.split("': ", 1)[-1] if "': " in last_response else last_response
                parts.append(f"这是【用户的具体建议和要求】:\n---\n{user_response}\n---")
                parts.append("**重要提示：你必须严格按照用户的建议进行修改，不得偏离用户明确提出的核心设定、情节要素或创意方向。如果需要使用工具来实现用户的建议，请在tool_params中完整包含用户的原始要求。**")
            else:
                parts.append(f"这是【本轮需要处理的新信息/反馈】 (可能来自工具或用户):\n---\n{last_response}\n---")
        
        parts.append("请严格基于【上一轮的议程文档】，并结合【本轮需要处理的新信息/反馈】，生成一份【更新后的议程文档】。确保不要丢失任何未完成的任务和已有信息。")
        parts.append("重要：当你决定询问用户问题前，必须先向用户清晰地沟通所有已收集的关键信息。不要把获得的信息只记录在议程中而不向用户展示。当你有任何发现或结论时，应该先向用户说明，再提出问题。")
        parts.append("如果有工具生成的内容适合保存为草稿供后续使用，请使用 `save_to_draft` 字段。如果你想在最终答案中使用已保存的草稿内容，请使用 `use_draft_contents` 字段列出要使用的内容ID。")
        
        return "\n".join(parts)
    
    def _process_planner_response(self, state: SimplerAgendaState, parsed_output, ai_response) -> SimplerAgendaState:
        """处理规划节点的LLM响应 - 参考graph523逻辑"""
        # 获取基本状态信息
        new_state_values = {**state}
        
        # 更新议程
        new_state_values["agenda_doc"] = parsed_output.get("updated_agenda_doc", state.get("agenda_doc", ""))
        
        # 获取下一步行动
        action_needed = parsed_output.get("next_action")
        
        # 根据action_needed设置状态
        if action_needed == "call_tool":
            tool_name = parsed_output.get("tool_name")
            tool_params = parsed_output.get("tool_params", {})
            
            if not tool_name:
                self.logger.warning("规划器选择call_tool但未指定tool_name")
                action_needed = "ask_human"
                new_state_values["human_question"] = "抱歉，我在选择工具时出现了问题。请告诉我您希望我做什么？"
            else:
                # 检查是否重复调用相同工具
                if self._is_recent_duplicate_tool_call(state, tool_name, tool_params):
                    self.logger.info(f"检测到重复工具调用 {tool_name}，转为询问用户")
                    action_needed = "ask_human"
                    new_state_values["human_question"] = f"我刚刚已经使用了{tool_name}工具。您对结果还满意吗？是否需要我做些调整，或者我们继续下一步？"
                    new_state_values["tool_name"] = None
                    new_state_values["tool_params"] = None
                else:
                    # 正常的工具调用
                    new_state_values["tool_name"] = tool_name
                    new_state_values["tool_params"] = tool_params
                    
                    # 增强工具参数
                    if tool_name in ["story_brainstorm", "plot_developer", "longform_writer", 
                                   "dialogue_writer", "logic_checker", "style_enhancer"]:
                        enhanced_context = self._build_enhanced_tool_context_with_history(state, tool_params)
                        new_state_values["tool_params"] = enhanced_context
                        self.logger.info(f"已为{tool_name}增强上下文信息，包含工具执行历史")
        
        elif action_needed == "ask_human":
            human_question = parsed_output.get("human_question")
            if not human_question:
                human_question = "我需要您的意见来继续。请告诉我您的想法？"
            new_state_values["human_question"] = human_question
            new_state_values["tool_name"] = None
            new_state_values["tool_params"] = None
        
        elif action_needed == "finish":
            final_answer = parsed_output.get("final_answer")
            use_draft_contents = parsed_output.get("use_draft_contents", [])
            
            # 处理草稿内容组合
            if use_draft_contents and isinstance(use_draft_contents, list):
                combined_content = []
                draft_outputs = new_state_values.get("draft_outputs", {}) or {}
                
                for task_id in use_draft_contents:
                    if task_id in draft_outputs:
                        combined_content.append(draft_outputs[task_id])
                
                if combined_content:
                    if final_answer:
                        combined_answer = final_answer + "\n\n" + "\n\n".join(combined_content)
                    else:
                        combined_answer = "\n\n".join(combined_content)
                    new_state_values["final_answer"] = combined_answer
                else:
                    new_state_values["final_answer"] = final_answer
            else:
                new_state_values["final_answer"] = final_answer
            
            new_state_values["tool_name"] = None
            new_state_values["tool_params"] = None
        
        else:
            # 默认情况或self_update
            action_needed = "ask_human"
            new_state_values["human_question"] = "我需要更多信息来继续。请告诉我您希望我如何协助您？"
            new_state_values["tool_name"] = None
            new_state_values["tool_params"] = None
        
        # 设置action_needed
        new_state_values["action_needed"] = action_needed
        
        # 处理save_to_draft
        save_to_draft = parsed_output.get("save_to_draft")
        if save_to_draft and isinstance(save_to_draft, dict):
            task_id = save_to_draft.get("task_id")
            content = save_to_draft.get("content")
            if task_id and content:
                if "draft_outputs" not in new_state_values or new_state_values["draft_outputs"] is None:
                    new_state_values["draft_outputs"] = {}
                new_state_values["draft_outputs"][task_id] = content
                self.logger.info(f"已保存内容到草稿: {task_id}")
        
        # 构建AI消息并添加到历史
        ai_message_content_str = str(ai_response.content)
        
        if action_needed == "call_tool" and new_state_values.get("tool_name"):
            tool_call_id = str(uuid.uuid4())
            new_state_values["tool_call_id_for_next_tool_message"] = tool_call_id
            current_ai_message = AIMessage(
                content=ai_message_content_str,
                tool_calls=[
                    {
                        "id": tool_call_id,
                        "name": new_state_values["tool_name"],
                        "args": new_state_values["tool_params"]
                    }
                ]
            )
        else:
            current_ai_message = AIMessage(content=ai_message_content_str)
        
        updated_messages_history = list(new_state_values.get("messages", []))
        updated_messages_history.append(current_ai_message)
        new_state_values["messages"] = updated_messages_history
        
        return cast(SimplerAgendaState, new_state_values)

    def _is_recent_duplicate_tool_call(self, state: SimplerAgendaState, tool_name: str, tool_params: dict) -> bool:
        """检查是否是最近重复的工具调用 - 修复版本"""
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

    def _build_enhanced_tool_context_with_history(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """为工具构建包含执行历史的增强上下文信息"""
        # 获取基础增强上下文
        enhanced_params = self._build_enhanced_tool_context(state, original_params)
        
        # 添加工具执行历史
        tool_history = self._extract_tool_execution_history(state)
        if tool_history:
            current_task = enhanced_params.get("task_description", "")
            history_context = f"""

【已执行的工具和结果】:
{chr(10).join(tool_history)}

【当前任务】: {current_task}

【重要提示】: 请基于上述已有的工具执行结果，避免重复生成相同类型的内容。如果之前的工具已经生成了相关内容，请在此基础上进行优化或扩展，而不是重新生成。
"""
            enhanced_params["task_description"] = history_context.strip()
        
        return enhanced_params

    def _extract_tool_execution_history(self, state: SimplerAgendaState) -> List[str]:
        """提取工具执行历史"""
        history = []
        messages = state.get("messages", [])
        
        current_tool = None
        for message in messages[-20:]:  # 只看最近20条消息，避免上下文过长
            if hasattr(message, 'content'):
                content = str(message.content)
                
                # 检测工具调用
                if "调用工具:" in content or "tool_name" in content:
                    # 尝试提取工具名称
                    import re
                    tool_match = re.search(r'"tool_name":\s*"([^"]+)"', content)
                    if tool_match:
                        current_tool = tool_match.group(1)
                
                # 检测工具结果
                elif isinstance(message, ToolMessage) and current_tool:
                    tool_display_name = self._get_tool_display_name(current_tool)
                    
                    # 截取结果预览
                    result_preview = content[:200] + "..." if len(content) > 200 else content
                    
                    history.append(f"- {tool_display_name}: {result_preview}")
                    current_tool = None  # 重置
        
        return history[-5:]  # 只保留最近5个工具执行结果

    def _auto_save_tool_result(self, state: SimplerAgendaState, tool_name: str, params: Dict, result: str):
        """自动保存工具结果 - 增强版"""
        # 检查是否是值得保存的内容
        if len(result) > 100 and not any(phrase in result.lower() for phrase in [
            "请提供", "需要更多信息", "无法", "错误", "抱歉"
        ]):
            # 生成基于工具名称和时间的任务ID
            timestamp = int(time.time()) % 10000
            task_id = f"{tool_name}_{timestamp}"
            
            # 保存到草稿
            if "draft_outputs" not in state:
                state["draft_outputs"] = {}
            
            state["draft_outputs"][task_id] = result
            self.logger.info(f"自动保存工具结果到草稿: {task_id} ({len(result)} 字符)")
            
            return task_id
        return None

    def _build_enhanced_tool_context(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """为工具构建增强的上下文信息"""
        agenda_doc = state.get("agenda_doc", "")
        overall_goal_match = re.search(r'- \[.\] (.+?) @overall_goal', agenda_doc)
        core_goal = overall_goal_match.group(1) if overall_goal_match else "未明确核心目标"
        
        incomplete_tasks = re.findall(r'- \[ \] (.+?)(?=\n|$)', agenda_doc, re.MULTILINE)
        task_requirements = []
        for task in incomplete_tasks:
            if "@overall_goal" not in task:
                task_requirements.append(f"- {task}")
        
        completed_tasks = re.findall(r'- \[x\] (.+?) \(结果: (.+?)\)', agenda_doc)
        task_history = []
        for task, result in completed_tasks:
            task_history.append(f"- {task}: {result}")
        
        last_response = state.get("last_response")
        user_feedback = ""
        if last_response and "用户回答了问题" in last_response:
            user_feedback = last_response.split("': ", 1)[-1] if "': " in last_response else last_response
        
        draft_outputs = state.get("draft_outputs") or {}
        draft_summary = []
        for task_id, content in draft_outputs.items():
            if content:
                preview = content[:150] + "..." if len(content) > 150 else content
                draft_summary.append(f"- {task_id}: {preview}")
        
        enhanced_task_description = f"""
【核心目标】: {core_goal}

【当前未完成的具体要求】:
{chr(10).join(task_requirements) if task_requirements else "- 无具体要求"}

【对话阶段】: 这是一个多轮交互的创作任务，当前处于第{len(completed_tasks) + 1}轮。

【之前完成的内容】:
{chr(10).join(task_history) if task_history else "- 尚未有已完成的任务"}

【用户最新反馈】:
{user_feedback if user_feedback else "无最新用户反馈"}

【已有草稿内容】:
{chr(10).join(draft_summary) if draft_summary else "- 暂无已保存的草稿内容"}

【当前具体任务】: {original_params.get('task_description', '未指定具体任务')}

【重要要求】:
1. 必须严格围绕核心目标进行创作
2. 必须严格遵循"当前未完成的具体要求"中的每一项要求，不得遗漏
3. 充分考虑用户的所有反馈和建议
4. 确保内容与对话的当前阶段相符
5. 特别注意：议程中的所有要求都是必须遵循的，包括细节要求
        """
        
        enhanced_params = {**original_params}
        enhanced_params["task_description"] = enhanced_task_description.strip()
        
        return enhanced_params

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

    def _emit_tool_call(self, tool_name: str, params: Dict, metadata: Dict):
        """发送工具调用事件 - 修复内容格式"""
        if self.stream_callback:
            try:
                # 修复：第二个参数应该是字符串内容，不是字典
                call_message = f"正在调用工具: {tool_name}"
                self.stream_callback("tool_call", call_message, {
                    "tool_name": tool_name,
                    "params": params,
                    "call_id": metadata.get("call_id"),
                    "tool_display_name": self._get_tool_display_name(tool_name),
                    "status": "calling"
                })
            except Exception as e:
                self.logger.error(f"发送工具调用事件失败: {e}")

    def _emit_tool_result(self, tool_name: str, result: str, metadata: Dict):
        """发送工具结果事件 - 确保完整内容传递"""
        if self.stream_callback:
            try:
                # 传递完整结果作为内容，元数据包含详细信息
                self.stream_callback("tool_result", result, {
                    "tool_name": tool_name,
                    "result": result,  # 完整结果
                    "call_id": metadata.get("call_id"),
                    "tool_display_name": self._get_tool_display_name(tool_name),
                    "status": "completed"
                })
            except Exception as e:
                self.logger.error(f"发送工具结果事件失败: {e}")
#planner_processor.py
"""
规划处理器
"""
import uuid
import time
from typing import Dict, Any, List, cast
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from ...state import SimplerAgendaState
from ....utils.logger import Logger
from ....utils.json_parser import JSONParser

class PlannerProcessor:
    """规划处理器 - 处理规划和决策逻辑"""
    
    def __init__(self, llm, logger: Logger, json_parser: JSONParser):
        self.llm = llm
        self.logger = logger
        self.json_parser = json_parser
        self.prompt_manager = None
    
    def set_prompt_manager(self, prompt_manager):
        """设置 prompt_manager"""
        self.prompt_manager = prompt_manager
    
    def process(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """处理规划逻辑"""
        self.logger.info("--- Planner Node ---")
        
        # 检查 prompt_manager 是否设置
        if not self.prompt_manager:
            self.logger.error("❌ prompt_manager 未设置，无法获取系统提示词")
            return self._handle_config_error(state)
        
        # 清理和验证消息历史
        current_messages = self._clean_message_history(state.get("messages", []))
        
        # 检查最后一条消息是否需要LLM响应
        if not self._needs_llm_response(current_messages):
            self.logger.info("检测到最后一条消息是AI响应，跳过LLM调用")
            return self._handle_existing_ai_response(state, current_messages)
        
        # 🎯 修复：使用 PromptManager 构建包含系统提示词的消息
        try:
            enhanced_messages = self._build_enhanced_context_with_prompt_manager(state, current_messages)
            self.logger.info(f"构建增强上下文成功，包含系统提示词")
        except Exception as e:
            self.logger.error(f"构建增强上下文失败: {e}")
            return self._handle_error(state, e)
        
        # 调用LLM - 使用包含系统提示词的消息
        try:
            self.logger.info(f"发送给LLM的消息数量: {len(enhanced_messages)}")
            self.logger.info(f"第一条消息类型: {type(enhanced_messages[0]).__name__ if enhanced_messages else 'None'}")
            
            self.logger.info(f"【planner】发送给LLM的消息: {enhanced_messages}")
            response = self.llm.invoke(enhanced_messages)  # 🎯 使用enhanced_messages而不是current_messages
            self.logger.info(f"Planner response type: {type(response)}")
            
            # 🎯 新增：首先保存原始LLM响应内容
            if hasattr(response, 'content'):
                original_content = response.content.strip()
                self.logger.info(f"LLM原始响应内容预览: {original_content[:200]}...")
                
                # 保存原始响应内容到状态（作为备份）
                state["_llm_raw_response"] = original_content
            
            # 检查响应内容
            if hasattr(response, 'content'):
                content = response.content.strip()
                self.logger.info(f"LLM响应内容预览: {content}")
                
                if not content:
                    self.logger.warning("LLM返回空响应")
                    return self._handle_empty_response(state, current_messages)
                
                # 尝试解析JSON响应
                parsed_json = self._parse_llm_response(content)
                if not parsed_json:
                    self.logger.warning("JSON解析失败，分析响应内容特征")
                    return self._handle_parse_failure_adaptive(state, current_messages, content)
                
                # 处理成功的JSON响应
                self.logger.info(f"JSON解析成功，action_needed: {parsed_json.get('action_needed')}")
                
                # 🎯 新增：处理会话记忆更新
                if "session_memory_update" in parsed_json and parsed_json["session_memory_update"]:
                    state["session_memory"] = parsed_json["session_memory_update"]
                    self.logger.info(f"✅ 会话记忆已更新: {parsed_json['session_memory_update'][:50]}...")
                
                return self._handle_successful_response(state, current_messages, response, parsed_json)
            else:
                self.logger.error("LLM响应没有content属性")
                return self._handle_empty_response(state, current_messages)
                
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return self._handle_llm_error(state, current_messages, str(e))
    
    def _clean_message_history(self, messages: List) -> List:
        """清理消息历史，移除无效和重复消息"""
        cleaned_messages = []
        last_content = None
        error_count = 0

        self.logger.info(f"开始清理消息历史，共 {len(messages)} 条消息")
        
        for msg in messages:
            try:
                if not hasattr(msg, 'content'):
                    continue
                    
                content = msg.content.strip()
                if not content:
                    continue
                
                # 🎯 新增：跳过重复的错误消息
                if content in ["处理时发生错误。", "规划过程出现问题，请重试", "请重新描述您的需求？", "系统遇到了一些问题，请重新描述您的需求？"]:
                    error_count += 1
                    # if error_count > 2:  # 取消错误消息数量限制
                    #     continue
                
                # 🎯 新增：跳过重复内容
                if content == last_content:
                    self.logger.warning(f"跳过重复消息: {content[:50]}...")
                    continue
                
                # 🎯 注释掉消息历史长度限制，保留完整对话历史
                # if len(cleaned_messages) >= 15:  # 只保留最近15条有效消息
                #     cleaned_messages = cleaned_messages[-10:]  # 保留最后10条
                #     self.logger.info("消息历史过长，截断到最近10条")
                
                # 取消单条消息内容长度限制
                # if len(content) > 10000:
                #     content = content[:10000] + "...[内容过长已截断]"
                #     if hasattr(msg, '__class__'):
                #         msg_class = msg.__class__
                #         new_msg = msg_class(content=content)
                #         cleaned_messages.append(new_msg)
                #     else:
                #         cleaned_messages.append(msg)
                # else:
                #     cleaned_messages.append(msg)
                
                # 直接添加消息，不进行长度限制
                cleaned_messages.append(msg)
                    
                last_content = content
                        
            except Exception as e:
                self.logger.warning(f"清理消息时出错: {e}，跳过该消息")
                continue
        
        self.logger.info(f"消息清理完成: {len(messages)} -> {len(cleaned_messages)} (跳过 {error_count} 个错误消息)")
        return cleaned_messages
    
    def _needs_llm_response(self, messages: List) -> bool:
        """检查是否需要LLM响应"""
        if not messages:
            return True
        
        last_msg = messages[-1]
        
        # 如果最后一条是用户消息，需要AI响应
        if hasattr(last_msg, '__class__') and 'Human' in last_msg.__class__.__name__:
            return True
        
        # 如果最后一条是AI消息，检查是否需要继续处理
        if hasattr(last_msg, '__class__') and 'AI' in last_msg.__class__.__name__:
            # 检查AI消息是否包含有效的JSON格式
            try:
                content = last_msg.content
                parsed = self.json_parser.parse(content)
                if parsed and parsed.get('action_needed'):
                    return False  # 已有有效的AI响应
            except:
                pass
            return True  # AI响应无效，需要重新生成
        
        return True
    
    def _build_enhanced_context(self, state: SimplerAgendaState, messages: List) -> List:
        """构建增强的上下文消息"""
        enhanced_messages = messages.copy()
        
        # 在最后添加当前任务上下文
        current_query = state.get("input_query", "")
        agenda_doc = state.get("agenda_doc", "")
        
        if current_query and agenda_doc:
            context_msg = HumanMessage(content=f"""
当前任务: {current_query}

当前议程状态:
{agenda_doc}

请基于以上上下文和对话历史，决定下一步行动。请严格按照JSON格式响应。
""")
            enhanced_messages.append(context_msg)
        
        return enhanced_messages
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试直接解析
            parsed = self.json_parser.parse(content)
            if parsed:
                return parsed
            
            # 尝试提取JSON块
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                if end > start:
                    json_content = content[start:end].strip()
                    parsed = self.json_parser.parse(json_content)
                    if parsed:
                        return parsed
            
            # 如果解析失败，返回None
            return None
            
        except Exception as e:
            self.logger.warning(f"JSON解析异常: {e}")
            return None
    
    def _handle_existing_ai_response(self, state: SimplerAgendaState, messages: List) -> SimplerAgendaState:
        """处理已存在的AI响应"""
        last_msg = messages[-1]
        
        try:
            parsed = self.json_parser.parse(last_msg.content)
            if parsed:
                return self._update_state_from_parsed_response(state, messages, parsed)
        except:
            pass
        
        # 如果解析失败，使用默认完成状态
        new_state = dict(state)
        new_state["messages"] = messages
        new_state["action_needed"] = "finish"
        new_state["final_answer"] = "根据对话历史，我已经提供了相关建议。还有什么其他需要帮助的吗？"
        return cast(SimplerAgendaState, new_state)
    
    def _handle_empty_response(self, state: SimplerAgendaState, messages: List) -> SimplerAgendaState:
        """处理空响应"""
        default_response = {
            "thought": "我需要更多信息来帮助您",
            "action_needed": "ask_human",
            "human_question": "请告诉我您具体需要什么帮助？",
            "final_answer": "请告诉我您具体需要什么帮助？"
        }
        
        # 🎯 新增：保存LLM响应内容
        import json
        try:
            llm_response_json = json.dumps(default_response, ensure_ascii=False, indent=2)
            state["_llm_response_content"] = llm_response_json
            self.logger.info(f"✅ 空响应处理：LLM响应内容已保存")
        except Exception as e:
            self.logger.warning(f"⚠️ 空响应处理：保存LLM响应内容失败: {e}")
        
        ai_message = AIMessage(content=self.json_parser.format_json(default_response))
        new_messages = messages + [ai_message]
        
        new_state = dict(state)
        new_state["messages"] = new_messages
        new_state.update(default_response)
        return cast(SimplerAgendaState, new_state)
    
    def _handle_parse_failure(self, state: SimplerAgendaState, messages: List, content: str) -> SimplerAgendaState:
        """处理JSON解析失败"""
        # 尝试从内容中提取有用信息
        default_response = {
            "thought": "【planner】解析JSON失败；我无法解析您的请求，请提供更清晰的指示",
            "action_needed": "ask_human",
            "human_question": "请重新描述您的需求？",
            "final_answer": content
        }
        
        # 🎯 新增：保存LLM响应内容
        import json
        try:
            llm_response_json = json.dumps(default_response, ensure_ascii=False, indent=2)
            state["_llm_response_content"] = llm_response_json
            self.logger.info(f"✅ 解析失败处理：LLM响应内容已保存")
        except Exception as e:
            self.logger.warning(f"⚠️ 解析失败处理：保存LLM响应内容失败: {e}")
        
        ai_message = AIMessage(content=self.json_parser.format_json(default_response))
        new_messages = messages + [ai_message]
        
        new_state = dict(state)
        new_state["messages"] = new_messages
        new_state.update(default_response)
        return cast(SimplerAgendaState, new_state)
    
    def _handle_successful_response(self, state: SimplerAgendaState, messages: List, 
                                  response: AIMessage, parsed_json: Dict[str, Any]) -> SimplerAgendaState:
        """处理成功的响应 - 增强重复检测"""
        
        action_needed = parsed_json.get("action_needed") or parsed_json.get("next_action")
        
        # 🎯 关键修复：在执行工具前强制检查重复
        if action_needed == "call_tool":
            tool_name = parsed_json.get("tool_name")
            if tool_name and self._is_tool_recently_executed_enhanced(messages, tool_name):
                self.logger.warning(f"🚫 检测到重复工具调用 {tool_name}，强制转换为询问用户")
                
                # 强制改为询问用户
                parsed_json["action_needed"] = "ask_human"
                parsed_json["human_question"] = f"我刚刚已经为您使用了{tool_name}工具。您对结果满意吗？需要我做哪些调整？"
                parsed_json["tool_name"] = None
                parsed_json["tool_params"] = None
        
        # 🎯 新增：保存LLM完整响应内容到状态中，供后续保存到数据库
        import json
        try:
            llm_response_json = json.dumps(parsed_json, ensure_ascii=False, indent=2)
            state["_llm_response_content"] = llm_response_json
            self.logger.info(f"✅ LLM响应内容已保存到状态: {len(llm_response_json)} 字符")
            # 🔍 新增调试：记录state对象信息
            self.logger.info(f"🔍 PlannerProcessor - 状态对象ID: {id(state)}")
            self.logger.info(f"🔍 PlannerProcessor - _llm_response_content存在: {bool(state.get('_llm_response_content'))}")
        except Exception as e:
            self.logger.warning(f"⚠️ 保存LLM响应内容失败: {e}")
        
        result = self._update_state_from_parsed_response(state, messages, parsed_json)
        
        # 🔍 新增调试：确认结果状态包含LLM响应内容
        self.logger.info(f"🔍 PlannerProcessor - 结果状态对象ID: {id(result)}")
        self.logger.info(f"🔍 PlannerProcessor - 结果状态_llm_response_content存在: {bool(result.get('_llm_response_content'))}")
        if result.get('_llm_response_content'):
            self.logger.info(f"🔍 PlannerProcessor - 结果状态LLM内容长度: {len(result['_llm_response_content'])} 字符")
        
        return result
    
    def _is_tool_recently_executed(self, messages: List, tool_name: str) -> bool:
        """检查工具是否在最近几条消息中执行过"""
        recent_messages = messages  # 检查所有消息
         
        for msg in recent_messages:
            if hasattr(msg, 'content') and msg.content:
                content = str(msg.content)
                # 检查是否包含工具执行完成的标记
                if f"工具执行完成: {tool_name}" in content or f"**{tool_name}**" in content:
                    self.logger.info(f"在最近消息中发现 {tool_name} 工具执行记录")
                    return True
        
        return False
    
    def _is_tool_recently_executed_enhanced(self, messages: List, tool_name: str) -> bool:
        """增强版工具重复检测"""
        if len(messages) < 2:
            return False
        
        # 检查所有消息
        recent_messages = messages
        tool_execution_count = 0
        
        for msg in recent_messages:
            # 检查 ToolMessage
            if hasattr(msg, '__class__') and 'Tool' in msg.__class__.__name__:
                content = str(getattr(msg, 'content', ''))
                # 检查内容中是否包含工具特征
                if self._is_tool_content_match(content, tool_name):
                    tool_execution_count += 1
            
            # 检查 AIMessage 中的 tool_calls
            elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if isinstance(tool_call, dict) and tool_call.get("name") == tool_name:
                        tool_execution_count += 1
        
        # 如果最近有相同工具执行，认为是重复
        is_duplicate = tool_execution_count > 0
        self.logger.info(f"重复检测 {tool_name}: 发现 {tool_execution_count} 次最近执行，判定为{'重复' if is_duplicate else '不重复'}")
        
        return is_duplicate
    
    def _is_tool_content_match(self, content: str, tool_name: str) -> bool:
        """检查内容是否匹配特定工具的输出特征"""
        tool_patterns = {
            'itinerary_planner': ['行程规划', '旅游计划', '逐日行程', '## 第', '天', '### 实用信息'],
            'brainstorm_tool': ['创意方向', '故事', '情节', '角色', '主题'],
            'plot_developer': ['情节发展', '冲突', '转折', '高潮'],
            'longform_writer': ['章节', '段落', '叙述', '描写'],
            'knowledge_analyzer': ['分析结果', '分析', '总结', '建议']
        }
        
        patterns = tool_patterns.get(tool_name, [])
        if not patterns:
            return False
        
        # 检查是否包含多个特征模式（增加准确性）
        matches = sum(1 for pattern in patterns if pattern in content)
        return matches >= 2  # 至少匹配2个特征才认为是同类工具输出
    
    def _handle_llm_error(self, state: SimplerAgendaState, messages: List, error_msg: str) -> SimplerAgendaState:
        """处理LLM调用错误"""
        default_response = {
            "thought": f"处理请求时遇到问题: {error_msg}",
            "action_needed": "ask_human",
            "human_question": "系统遇到了一些问题，请重新描述您的需求？",
            "final_answer": "抱歉，系统遇到了一些问题，请重新描述您的需求？"
        }
        
        # 🎯 新增：保存LLM响应内容
        import json
        try:
            llm_response_json = json.dumps(default_response, ensure_ascii=False, indent=2)
            state["_llm_response_content"] = llm_response_json
            self.logger.info(f"✅ LLM错误处理：LLM响应内容已保存")
        except Exception as e:
            self.logger.warning(f"⚠️ LLM错误处理：保存LLM响应内容失败: {e}")
        
        ai_message = AIMessage(content=self.json_parser.format_json(default_response))
        new_messages = messages + [ai_message]
        
        new_state = dict(state)
        new_state["messages"] = new_messages
        new_state.update(default_response)
        return cast(SimplerAgendaState, new_state)
    
    def _update_state_from_parsed_response(self, state: SimplerAgendaState, 
                                         messages: List, parsed_json: Dict[str, Any]) -> SimplerAgendaState:
        """从解析的响应更新状态 - 修复字段名映射"""
        new_state = dict(state)
        new_state["messages"] = messages
        
        # 🎯 修复：处理字段名不匹配问题
        action_needed = parsed_json.get("action_needed") or parsed_json.get("next_action")
        if action_needed:
            parsed_json["action_needed"] = action_needed
            
        # 确保删除可能的 next_action 字段
        if "next_action" in parsed_json:
            del parsed_json["next_action"]
            
        self.logger.info(f"更新状态时字段映射后 action_needed: {action_needed}")
        
        new_state.update(parsed_json)
        
        # 🎯 确保LLM响应内容被保留在状态中 - 增强版本
        llm_content = state.get("_llm_response_content")
        if llm_content:
            new_state["_llm_response_content"] = llm_content
            self.logger.info(f"✅ LLM响应内容已保留在新状态中: {len(llm_content)} 字符")
            # 🔍 调试：验证保存
            self.logger.info(f"🔍 _update_state_from_parsed_response - 原状态有LLM内容: {bool(llm_content)}")
            self.logger.info(f"🔍 _update_state_from_parsed_response - 新状态有LLM内容: {bool(new_state.get('_llm_response_content'))}")
        else:
            self.logger.warning(f"⚠️ 原状态中没有找到_llm_response_content字段")
        
        # 生成工具调用ID（如果需要）
        if action_needed == "call_tool" and parsed_json.get("tool_name"):
            tool_name = parsed_json.get("tool_name")
            timestamp = int(time.time())
            new_state["tool_call_id_for_next_tool_message"] = f"call_{tool_name}_{timestamp}"
        
        return cast(SimplerAgendaState, new_state)
    
    # 其他辅助方法
    def is_recent_duplicate_tool_call(self, state: SimplerAgendaState, tool_name: str, tool_params: dict) -> bool:
        """检查是否是最近重复的工具调用"""
        return self.loop_detector.is_recent_duplicate_tool_call(state, tool_name, tool_params)
    
    def build_enhanced_tool_context_with_history(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建增强工具上下文"""
        return self.context_builder.build_enhanced_tool_context_with_history(state, original_params)
    
    def extract_tool_execution_history(self, state: SimplerAgendaState) -> List[str]:
        """提取工具执行历史"""
        return self.context_builder.extract_tool_execution_history(state)
    
    def build_enhanced_tool_context(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建增强工具上下文"""
        return self.context_builder.build_enhanced_tool_context(state, original_params) 
    
    def _handle_config_error(self, state: SimplerAgendaState) -> SimplerAgendaState:
        """处理配置错误"""
        self.logger.error("规划节点错误: prompt_manager 未设置")
        new_state = dict(state)
        new_state["error_message"] = "规划节点配置错误"
        new_state["action_needed"] = "finish"
        new_state["final_answer"] = "系统配置有误，请重试"
        return new_state
    
    def _handle_parse_error(self, state: SimplerAgendaState, content: str) -> SimplerAgendaState:
        """处理解析错误"""
        messages = state.get("messages", [])
        tool_result_count = sum(1 for msg in messages if hasattr(msg, 'tool_call_id'))
        
        new_state = dict(state)
        if tool_result_count > 0:
            new_state["action_needed"] = "ask_human"
            new_state["human_question"] = "我已经为您准备了一些内容。您希望我如何继续？"
        else:
            new_state["action_needed"] = "finish"
            new_state["final_answer"] = content
        
        return new_state
    
    def _handle_error(self, state: SimplerAgendaState, error: Exception) -> SimplerAgendaState:
        """处理错误"""
        new_state = dict(state)
        new_state["error_message"] = f"规划节点错误: {str(error)}"
        new_state["action_needed"] = "finish"
        new_state["final_answer"] = "规划过程出现问题，请重试"
        return new_state
    
    def _build_enhanced_context_with_prompt_manager(self, state: SimplerAgendaState, messages: List) -> List:
        """使用 PromptManager 构建包含系统提示词的完整消息列表"""
        
        filtered_messages = []
        tool_call_history = []
        recent_tool_executions = []  # 🎯 新增：记录最近的工具执行
        
        for i, msg in enumerate(messages):  # 检查所有消息
            # 跳过旧的系统提示词
            if hasattr(msg, '__class__') and 'System' in msg.__class__.__name__:
                continue
            is_last_message = (i == len(messages) - 1) 
            # 🎯 修复：更明确地标识工具结果
            if hasattr(msg, '__class__') and 'Tool' in msg.__class__.__name__:
                tool_name = self._extract_tool_name_precisely(msg)
                if tool_name:
                    tool_call_history.append(tool_name)
                    recent_tool_executions.append({
                        'tool': tool_name,
                        'time': len(filtered_messages),  # 用消息顺序作为时间
                        'content_preview': str(msg.content)
                    })
                    if is_last_message:
                        converted_content = f"""✅ **工具执行完成: {tool_name}** 【此条为历史对话的最后一条消息，注意该轮输出json里"action_needed"必须为ask_human，请一定记住不允许再次call_tool；主动推进议程阶段，不允许和之前的AI message消息重复，禁止重复问询，禁止追问】"""
                    else:# 转换为明确的AI消息
                        converted_content = f"""✅ **工具执行完成: {tool_name}**"""

                    converted_msg = AIMessage(content=converted_content)
                    filtered_messages.append(converted_msg)
                    self.logger.info(f"转换ToolMessage为AIMessage: {tool_name}")
            elif hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                # 处理AI消息 
                if is_last_message:
                    # 为AI消息添加上下文标记
                    ai_content = f"{msg.content} 【此条为历史对话的最后一条消息，消息由AI发出】"
                    filtered_messages.append(AIMessage(content=ai_content))
                else:
                    filtered_messages.append(msg)
            elif hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__:
                # 处理Human消息
                if is_last_message:
                    # 为Human消息添加上下文标记
                    human_content = f"{msg.content} 【此条为历史对话的最后一条消息，消息由用户发出，请你完全理解用户的需求，结合上文思考用户真实需求，满足需求，不允许和之前的AI message消息重复，禁止重复问询，禁止追问，若用户提供内容不足，可以主动调用工具call_tool提供灵感，主动推进议程阶段】"
                    filtered_messages.append(HumanMessage(content=human_content))
                else:
                    filtered_messages.append(msg)
            else:
                # 处理其他类型消息
                filtered_messages.append(msg)
        
        # 获取系统提示词
        system_prompt = self.prompt_manager.get_system_prompt()
        
        system_prompt+=f"""
        下面是当前对话的所有上下文，AIMessage是你之前的输出，HumanMessage是用户的输出：
        '''
        """
        enhanced_messages = [SystemMessage(content=system_prompt)] + filtered_messages

        # 构建当前已经使用工具的最新完整内容
        latest_tool_content = ""
        if recent_tool_executions:
            # 按工具类型获取最新的完整内容
            tool_latest = {}
            for exec_info in recent_tool_executions:
                tool_name = exec_info['tool']
                if tool_name not in tool_latest or exec_info['time'] > tool_latest[tool_name]['time']:
                    tool_latest[tool_name] = exec_info  # 保存完整的exec_info对象而不是只保存content_preview
            
            # 显示所有工具种类的最新完整内容
            if tool_latest:
                tool_contents = []
                for tool_name, exec_info in tool_latest.items():
                    tool_contents.append(f"【{tool_name}最新结果】:\n{exec_info['content_preview']}")
                latest_tool_content = "\n\n".join(tool_contents)
        else:
            latest_tool_content = "暂无工具执行结果"
        
        planner_prompt=f"""
        '''
        下面是工具的最新结果：
        
        {latest_tool_content}
        """
        # 添加规划提示
        planner_prompt += self.prompt_manager.get_planner_prompt(state)
        
        # 🎯 如果有工具结果，修改规划提示强调不重复
        if recent_tool_executions:
            # 提取唯一的工具名称
            unique_recent_tools = list(set([exec_info['tool'] for exec_info in recent_tool_executions]))
            
            planner_prompt += f"""

🔍 **当前状态检查**:
- ✅ 最近完成: {", ".join(unique_recent_tools)} 工具执行
- 📋 有可用结果，用户可以查看和选择

🎯 **强制要求**:
- 当前必须使用 ask_human 询问用户对现有结果的意见
- 如果用户满意，使用 finish 结束任务"""
        
        enhanced_messages.append(SystemMessage(content=planner_prompt))
        
        
        return enhanced_messages

    def _extract_tool_name_precisely(self, tool_message) -> str:
        """精确提取工具名称"""
        try:
            # 方法1: 直接从tool_call_id中提取（最准确）
            if hasattr(tool_message, 'tool_call_id') and tool_message.tool_call_id:
                tool_call_id = str(tool_message.tool_call_id)
                # 从tool_call_id中提取实际工具名（格式为"call_工具名_timestamp"）
                if 'call_' in tool_call_id and tool_call_id.count('_') >= 2:
                    # 移除开头的"call_"和结尾的时间戳，中间的就是工具名
                    without_prefix = tool_call_id[5:]  # 去掉"call_"
                    last_underscore_idx = without_prefix.rfind('_')  # 找到最后一个下划线
                    if last_underscore_idx > 0:
                        return without_prefix[:last_underscore_idx]  # 返回工具名部分
            
            # 方法2: 从消息内容中推断当前实际使用的工具
            content = str(getattr(tool_message, 'content', ''))
            if content:
                # 基于当前实际工具的特征关键词
                tool_patterns = {
                    'creative_guide': ['创意方向', '主题分析', '情感内核'],
                    'material_collector': ['素材收集', '信息整理', '背景资料'],
                    'theme_focuser': ['主题聚焦', '核心问题', '焦点确定'],
                    'story_planner': ['故事大纲', '情节结构', '章节规划'],
                    'story_refiner': ['大纲优化', '结构调整', '内容完善'],
                    'brainstorm_tool': ['头脑风暴', '创意激发', '想法生成'],
                    'character_builder': ['角色设定', '人物构建', '角色发展'],
                    'plot_developer': ['情节开发', '冲突设计', '转折点']
                }
                
                for tool_name, keywords in tool_patterns.items():
                    if any(keyword in content for keyword in keywords):
                        return tool_name
            
            return 'unknown_tool'
            
        except Exception as e:
            self.logger.warning(f"提取工具名称时出错: {e}")
            return 'unknown_tool'

    def _handle_parse_failure_adaptive(self, state: SimplerAgendaState, messages: List, content: str) -> SimplerAgendaState:
        """智能处理JSON解析失败"""
        self.logger.warning(f"LLM输出了自然语言而非JSON: {content[:100]}...")
        
        # 检查内容特征
        content_lower = content.lower()
        user_input = state.get("input_query", "")
        
        # 根据内容特征智能响应
        if any(keyword in content_lower for keyword in ["故事", "创作", "科幻", "机器人", "情节", "小说"]):
            self.logger.info("检测到故事创作需求")
            default_response = {
                "thought": "用户想要创作科幻故事，我需要为他提供创意灵感",
                "action_needed": "call_tool",
                "tool_name": "brainstorm_tool",
                "tool_params": {
                    "task_description": f"用户想要创作科幻小说，涉及机器人主题。用户需求：{user_input}。请提供创意灵感和故事构思建议。",
                    "brainstorm_focus": "character_development",
                    "creative_constraints": "科幻背景，机器人相关主题"
                }
            }
        else:
            self.logger.info("使用通用询问响应")
            default_response = {
                "thought": "LLM返回了自然语言而非JSON，需要重新获取用户需求",
                "action_needed": "ask_human",
                "human_question": f"基于我的理解：{content}\n\n请告诉我您希望我接下来如何帮助您？",
                "final_answer": content
            }
        
        # 🎯 新增：保存LLM响应内容
        import json
        try:
            # 保存原始内容和处理后的响应
            llm_response_data = {
                "original_content": content,
                "processed_response": default_response,
                "parse_failure_reason": "LLM输出自然语言而非JSON格式"
            }
            llm_response_json = json.dumps(llm_response_data, ensure_ascii=False, indent=2)
            state["_llm_response_content"] = llm_response_json
            self.logger.info(f"✅ 自适应解析失败处理：LLM响应内容已保存")
        except Exception as e:
            self.logger.warning(f"⚠️ 自适应解析失败处理：保存LLM响应内容失败: {e}")
        
        # 创建AI消息
        ai_message = AIMessage(content=self.json_parser.format_json(default_response))
        new_messages = messages + [ai_message]
        
        new_state = dict(state)
        new_state["messages"] = new_messages
        new_state.update(default_response)
        return cast(SimplerAgendaState, new_state)
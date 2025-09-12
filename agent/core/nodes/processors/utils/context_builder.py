"""
上下文构建器
"""
import re
from typing import Dict, Any, List
from langchain_core.messages import ToolMessage
from ....state import SimplerAgendaState

class ContextBuilder:
    """上下文构建器 - 构建增强的工具上下文"""
    
    def __init__(self, logger):
        """初始化上下文构建器"""
        self.logger = logger

    def _strip_progress_tail(self, text: str) -> str:
        """去除消息末尾的“当前进度”提示段

        匹配形如：\n\n📍**当前进度**：阶段X - 阶段名称（或任意内容）
        无论是否有前置换行，统一剔除该段以及其后的所有文本。
        """
        if not text:
            return text
        try:
            # 去除从“📍**当前进度**：”所在行到文本结尾的内容
            return re.sub(r"(?:\r?\n){0,3}\s*📍\*\*当前进度\*\*：.*$", "", text, flags=re.M|re.S)
        except Exception:
            return text

    def build_enhanced_tool_context_with_history(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建包含执行历史的增强上下文信息"""
        self.logger.info(f"[DEBUG] build_enhanced_tool_context_with_history 被调用")
        self.logger.info(f"[DEBUG] 调用时state的所有keys: {list(state.keys())}")
        
        # 获取基础增强上下文
        enhanced_params = self.build_enhanced_tool_context(state, original_params)
        
        # 🎯 提取聊天历史记录
        chat_history = self.extract_chat_history(state)
        self.logger.info(f"[DEBUG] 聊天历史记录数量: {len(chat_history)}")
        
        # 添加工具执行历史
        tool_history = self.extract_tool_execution_history(state)
        self.logger.info(f"[DEBUG] 工具执行历史数量: {len(tool_history)}")
        
        if tool_history or chat_history:
            # 🎯 从聊天历史中提取用户最新的一条消息作为当前任务
            user_latest_message = "未指定具体任务"
            messages = state.get("messages", [])
            # 从后往前查找最新的用户消息
            for message in reversed(messages):
                if hasattr(message, '__class__') and message.__class__.__name__ == "HumanMessage":
                    if hasattr(message, 'content') and message.content:
                        user_latest_message = self._strip_progress_tail(str(message.content).strip())
                        break
            
            # 🎯 构建完整的历史上下文
            history_context = f"""
【聊天历史记录】:
{chr(10).join(chat_history) if chat_history else "- 暂无历史对话"}

【已执行的工具和最新结果】:
{chr(10).join(tool_history) if tool_history else "- 暂无工具执行历史"}

【用户的最后一条消息】: {user_latest_message}【用户的最后一条消息，请你联系上下文思考用户需求，以用户需求为准】

"""
            enhanced_params["task_description"] = history_context.strip()
        
        return enhanced_params

    def extract_chat_history(self, state: SimplerAgendaState) -> List[str]:
        """提取聊天历史记录 - 记录工具调用名称但不记录具体内容"""
        history = []
        messages = state.get("messages", [])

        for message in messages:
            if hasattr(message, 'content'):
                content = self._strip_progress_tail(str(message.content).strip())
                
                # 识别消息类型并格式化
                if hasattr(message, '__class__'):
                    msg_type = message.__class__.__name__
                    
                    if msg_type == "HumanMessage":
                        # 过滤掉user_profile中的具体姓名，替换为空字符串
                        if '"user_profile":"user_' in content:
                            import re
                            filtered_content = re.sub(r'"user_profile":"user_[^"]*"', '"user_profile":""', content)
                            history.append(f"用户: {filtered_content}")
                        else:
                            history.append(f"用户: {content}")
                        
                    elif msg_type == "AIMessage":
                        # 检查是否是工具执行完成消息
                        if "工具执行完成" in content:
                            # 内联提取工具名称
                            match = re.search(r'工具执行完成[:\s]*([a-zA-Z_]+)', content)
                            tool_name = match.group(1) if match else "unknown_tool"
                            history.append(f"助手: 已调用工具 [{tool_name}]")
                        else:
                            pattern = r'(?:\n\n|\r\n\r\n)📍\*\*当前进度\*\*：阶段\d+ - .*?(?:\n|$)'
                            cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
                            # 普通AI回复
                            history.append(f"助手: {cleaned}")
                            
                    elif msg_type == "ToolMessage":
                        # 从tool_call_id中提取工具名 (格式: call_tool_name_timestamp)
                        if hasattr(message, 'tool_call_id') and message.tool_call_id:
                            tool_call_id = str(message.tool_call_id)
                            if 'call_' in tool_call_id and tool_call_id.count('_') >= 2:
                                # 移除开头的"call_"和结尾的时间戳
                                without_prefix = tool_call_id[5:]  # 去掉"call_"
                                last_underscore_idx = without_prefix.rfind('_')  # 找到最后一个下划线
                                tool_name = without_prefix[:last_underscore_idx] if last_underscore_idx > 0 else "unknown_tool"
                            else:
                                tool_name = "unknown_tool"
                        else:
                            tool_name = "unknown_tool"
                        history.append(f"工具: 已执行 [{tool_name}]")
        
        return history

    def extract_tool_execution_history(self, state: SimplerAgendaState) -> List[str]:
        """提取工具执行历史 - 只显示每种工具的最新结果"""
        history = []
        
        # 🎯 从draft_outputs中获取所有工具的最新结果
        draft_outputs = state.get("draft_outputs") or {}
        has_draft_key = "draft_outputs" in state
        self.logger.info(f"[DEBUG] state中有draft_outputs key: {has_draft_key}, 草稿数量: {len(draft_outputs)}")
        
        # 🎯 按工具类型分组，只保留每种工具的最新结果
        tool_latest_results = {}
        
        # for task_id, content in draft_outputs.items():
        #     if content and content.strip():  # 只考虑非空的草稿内容
        #         # 从task_id中提取工具名 (格式: tool_name_timestamp)
        #         if '_' in task_id:
        #             # 找到最后一个下划线，前面的都是工具名
        #             last_underscore_idx = task_id.rfind('_')
        #             tool_name = task_id[:last_underscore_idx]
        #             timestamp_str = task_id.split('_')[-1] if len(task_id.split('_')) > 1 else '0'
                    
        #             try:
        #                 timestamp = int(timestamp_str)
        #             except:
        #                 timestamp = 0
                    
        #             # 只保留每种工具的最新结果
        #             if tool_name not in tool_latest_results or timestamp > tool_latest_results[tool_name]['timestamp']:
        #                 tool_latest_results[tool_name] = {
        #                     'content': content,
        #                     'timestamp': timestamp,
        #                     'task_id': task_id
        #                 }
        
        # # 🎯 构建历史记录，只包含每种工具的最新结果
        # for tool_name, data in tool_latest_results.items():
        #     tool_display_name = self._get_tool_display_name(tool_name)
        #     history.append(f"- {tool_display_name}: {data['content']}")
        #     self.logger.info(f"[DEBUG] 添加最新工具结果: {tool_display_name} (task_id: {data['task_id']})")
        
        # 🎯 如果draft_outputs中没有找到，再从消息历史中查找ToolMessage
        if not history:
            messages = state.get("messages", [])
            self.logger.info(f"[DEBUG] draft_outputs为空，从消息历史中查找，消息总数: {len(messages)}")
            
            current_tool = None
            for i, message in enumerate(messages):  # 只看最近20条消息
                msg_type = type(message).__name__
                self.logger.info(f"[DEBUG] 消息 {i}: 类型={msg_type}")
                
                if hasattr(message, 'content'):
                    content = str(message.content)
                    self.logger.info(f"[DEBUG] 消息 {i} 内容预览: {content[:100]}...")
                    
                    # 🎯 只识别真正的工具执行结果，排除系统提示词
                    is_tool_message = isinstance(message, ToolMessage)
                    has_tool_call_id = hasattr(message, 'tool_call_id') and message.tool_call_id
                    
                    # 排除系统提示词的特征
                    is_system_prompt = any(pattern in content for pattern in [
                        "你叫TATA", "扮演一个", "核心原则", "工作模式", "重要规则",
                        "工具调用策略", "禁止轻易调用工具"
                    ])
                    
                    self.logger.info(f"[DEBUG] 消息 {i} - 是ToolMessage: {is_tool_message}, 有tool_call_id: {has_tool_call_id}, 是系统提示词: {is_system_prompt}")
                    
                    # 只有真正的工具消息且不是系统提示词才处理
                    if (is_tool_message or has_tool_call_id) and not is_system_prompt:
                        # 从tool_call_id提取工具名和时间戳
                        tool_name = "unknown_tool"
                        timestamp = 0
                        
                        if has_tool_call_id and message.tool_call_id:
                            tool_call_id = str(message.tool_call_id)
                            # 格式: call_creative_guide_1756475018
                            if tool_call_id.startswith('call_'):
                                parts = tool_call_id[5:].split('_')  # 去掉"call_"前缀
                                if len(parts) >= 2:
                                    # 最后一部分是时间戳，前面的是工具名
                                    tool_name = '_'.join(parts[:-1])
                                    try:
                                        timestamp = int(parts[-1])
                                    except:
                                        timestamp = 0
                        
                        # 检查内容是否有效（非空且有意义）
                        if len(content.strip()) > 20:
                            # 只保留每种工具的最新结果
                            if tool_name not in tool_latest_results or timestamp > tool_latest_results[tool_name]['timestamp']:
                                tool_latest_results[tool_name] = {
                                    'content': content,  # 保持完整内容，不截取
                                    'timestamp': timestamp,
                                    'message_index': i
                                }
                                self.logger.info(f"[DEBUG] 从ToolMessage更新工具结果: {tool_name} (时间戳: {timestamp})")
        
        # 🎯 构建历史记录，只包含每种工具的最新结果
        for tool_name, data in tool_latest_results.items():
            tool_display_name = self._get_tool_display_name(tool_name)
            # 保持完整内容，不截取
            history.append(f"- {tool_display_name}: {data['content']}")
            self.logger.info(f"[DEBUG] 添加工具历史: {tool_display_name}")
        
        if not history:
            self.logger.info(f"[DEBUG] 没有找到有效的工具执行历史")
        
        self.logger.info(f"[DEBUG] 工具执行历史提取完成，共找到 {len(history)} 条记录")
        return history[-5:]  # 只保留最近5个工具执行结果

    def build_enhanced_tool_context(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建增强的工具上下文信息"""
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

【已有草稿内容】:
{chr(10).join(draft_summary) if draft_summary else "- 暂无已保存的草稿内容"}

【当前具体任务】: {original_params.get('task_description', '未指定具体任务')}


        """
        
        enhanced_params = {**original_params}
        enhanced_params["task_description"] = enhanced_task_description.strip()
        
        return enhanced_params
    
    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具显示名称"""
        display_names = {
            "creative_guide": "creative_guide",
            "material_collector": "material_collector",
            "theme_focuser": "theme_focuser",
            "story_planner": "story_planner"
        }
        return display_names.get(tool_name, tool_name)

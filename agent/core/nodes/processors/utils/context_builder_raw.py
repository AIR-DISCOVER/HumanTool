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

    def build_enhanced_tool_context_with_history(self, state: SimplerAgendaState, original_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建包含执行历史的增强上下文信息"""
        self.logger.info(f"[DEBUG] build_enhanced_tool_context_with_history 被调用")
        
        # 获取基础增强上下文
        enhanced_params = self.build_enhanced_tool_context(state, original_params)
        
        # 🎯 提取聊天历史记录
        chat_history = self.extract_chat_history(state)
        self.logger.info(f"[DEBUG] 聊天历史记录数量: {len(chat_history)}")
        
        # 添加工具执行历史
        tool_history = self.extract_tool_execution_history(state)
        self.logger.info(f"[DEBUG] 工具执行历史数量: {len(tool_history)}")
        
        if tool_history or chat_history:
            current_task = enhanced_params.get("task_description", "")
            
            # 🎯 构建完整的历史上下文
            history_context = f"""
【聊天历史记录】:
{chr(10).join(chat_history) if chat_history else "- 暂无历史对话"}

【已执行的工具和结果】:
{chr(10).join(tool_history) if tool_history else "- 暂无工具执行历史"}

【当前任务】: {current_task}

【重要提示】: 请基于上述聊天历史和工具执行结果，避免重复生成相同类型的内容。如果之前已经有相关内容，请在此基础上进行优化、补充或扩展。
"""
            enhanced_params["task_description"] = history_context.strip()
        
        return enhanced_params

    def extract_chat_history(self, state: SimplerAgendaState) -> List[str]:
        """提取聊天历史记录"""
        history = []
        messages = state.get("messages", [])

        # 只保留最近40条消息
        recent_messages = messages[-40:]
        
        for message in recent_messages:
            if hasattr(message, 'content'):
                content = str(message.content).strip()
                
                # 跳过工具执行相关的消息
                if any(skip_word in content.lower() for skip_word in [
                    "执行工具", "tool_call", "tool_result", "调用工具"
                ]):
                    continue
                
                # 识别消息类型并格式化
                if hasattr(message, '__class__'):
                    msg_type = message.__class__.__name__
                    if msg_type == "HumanMessage":
                        history.append(f"用户: {content}...")
                    elif msg_type == "AIMessage":
                        history.append(f"助手: {content}...")
        
        return history[-5:]  # 只保留最近5条对话记录

    def extract_tool_execution_history(self, state: SimplerAgendaState) -> List[str]:
        """提取工具执行历史"""
        history = []
        
        # 🎯 优先从draft_outputs中获取工具执行结果
        draft_outputs = state.get("draft_outputs") or {}
        self.logger.info(f"[DEBUG] 检查draft_outputs，共有 {len(draft_outputs)} 个草稿")
        
        for task_id, content in draft_outputs.items():
            if content and len(content) > 100:  # 只考虑有实质内容的草稿
                # 根据task_id推断工具类型
                if any(keyword in task_id.lower() for keyword in ['itinerary', 'travel', 'planner']):
                    tool_display_name = "旅行规划器"
                elif any(keyword in task_id.lower() for keyword in ['story', 'brainstorm']):
                    tool_display_name = "故事头脑风暴"
                elif any(keyword in task_id.lower() for keyword in ['image', 'generator']):
                    tool_display_name = "图片生成器"
                else:
                    tool_display_name = "工具执行结果"
                
                # 智能截取内容
                if len(content) > 1000:
                    sentences = content.split('。')
                    result_preview = ""
                    for sentence in sentences:
                        if len(result_preview + sentence + '。') <= 800:
                            result_preview += sentence + '。'
                        else:
                            break
                    if not result_preview:
                        result_preview = content[:800]
                    result_preview += "..."
                else:
                    result_preview = content
                
                history.append(f"- {tool_display_name}: {result_preview}")
                self.logger.info(f"[DEBUG] 从draft_outputs添加工具历史: {tool_display_name} (task_id: {task_id})")
        
        # 🎯 如果draft_outputs中没有找到，再从消息历史中查找ToolMessage
        if not history:
            messages = state.get("messages", [])
            self.logger.info(f"[DEBUG] draft_outputs为空，从消息历史中查找，消息总数: {len(messages)}")
            
            current_tool = None
            for i, message in enumerate(messages[-20:]):  # 只看最近20条消息
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
                        # 检查是否包含实际的工具执行结果特征
                        has_travel_content = any(pattern in content for pattern in [
                            "## 📅 逐日详细行程", "旅游规划结果", "第1天", "第2天", "第3天",
                            "住宿信息", "交通方式", "用餐建议", "景点", "预算"
                        ])
                        
                        if has_travel_content:
                            tool_display_name = "旅行规划器"
                            
                            if len(content) > 1000:
                                sentences = content.split('。')
                                result_preview = ""
                                for sentence in sentences:
                                    if len(result_preview + sentence + '。') <= 800:
                                        result_preview += sentence + '。'
                                    else:
                                        break
                                if not result_preview:
                                    result_preview = content[:800]
                                result_preview += "..."
                            else:
                                result_preview = content
                            
                            history.append(f"- {tool_display_name}: {result_preview}")
                            self.logger.info(f"[DEBUG] 从ToolMessage添加工具历史: {tool_display_name}")
        
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
            "calculator": "计算器",
            "knowledge_analyzer": "知识分析器",
            "story_brainstorm": "故事头脑风暴",
            "plot_developer": "情节开发器",
            "longform_writer": "长篇写作器",
            "itinerary_planner": "旅行规划器",  # 🎯 新增旅行规划工具
            "travel_planner": "旅行规划器",     # 🎯 新增旅行规划工具别名
            # "dialogue_writer": "对话写作器",
            # "logic_checker": "逻辑检查器",
            # "style_enhancer": "风格增强器"
        }
        return display_names.get(tool_name, tool_name)
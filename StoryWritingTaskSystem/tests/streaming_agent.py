import time
import re
from typing import Callable, Dict, Any, Optional, List
from agent.graph import AgendaAgent
from agent.core.state import SimplerAgendaState

class StreamChunk:
    def __init__(self, type: str, content: str, step_name: Optional[str] = None, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.type = type
        self.content = content
        self.step_name = step_name
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def to_dict(self):
        return {
            "type": self.type,
            "content": self.content,
            "step_name": self.step_name,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class AgendaParser:
    """议程解析器 - 解析和分析议程变化"""
    
    @staticmethod
    def parse_agenda(agenda_text: str) -> Dict[str, Any]:
        """解析议程文本，提取任务状态"""
        tasks = {
            "pending": [],      # [ ] 待办
            "completed": [],    # [x] 已完成  
            "in_progress": [],  # [-] 进行中/阻塞
            "goals": []         # @overall_goal 标记的目标
        }
        
        if not agenda_text:
            return tasks
            
        lines = agenda_text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是任务行
            if re.match(r'^- \[[ x-]\]', line):
                task_info = AgendaParser._parse_task_line(line, line_num)
                if task_info:
                    status = task_info["status"]
                    if status == "pending":
                        tasks["pending"].append(task_info)
                    elif status == "completed":
                        tasks["completed"].append(task_info)
                    elif status == "in_progress":
                        tasks["in_progress"].append(task_info)
                    
                    # 检查是否是目标任务
                    if "@overall_goal" in line:
                        tasks["goals"].append(task_info)
        
        return tasks
    
    @staticmethod
    def _parse_task_line(line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """解析单个任务行"""
        # 匹配任务状态
        if "- [x]" in line:
            status = "completed"
            # 提取结果信息
            result_match = re.search(r'\(结果: (.*?)\)', line)
            result = result_match.group(1) if result_match else None
        elif "- [-]" in line:
            status = "in_progress"
            # 提取原因信息
            reason_match = re.search(r'\(原因: (.*?)\)', line)
            result = reason_match.group(1) if reason_match else None
        elif "- [ ]" in line:
            status = "pending"
            result = None
        else:
            return None
        
        # 提取任务描述
        task_match = re.search(r'- \[[ x-]\] (.*?)(?:\s*\((?:结果|原因): .*?\))?(?:\s*@\w+)?$', line)
        description = task_match.group(1).strip() if task_match else line
        
        # 检查缩进级别（嵌套层级）
        indent_level = (len(line) - len(line.lstrip())) // 2
        
        # 检查是否是目标任务
        is_goal = "@overall_goal" in line
        
        return {
            "status": status,
            "description": description,
            "result": result,
            "line_number": line_num,
            "indent_level": indent_level,
            "is_goal": is_goal,
            "raw_line": line
        }
    
    @staticmethod
    def get_agenda_summary(agenda_text: str) -> Dict[str, Any]:
        """获取议程摘要统计"""
        tasks = AgendaParser.parse_agenda(agenda_text)
        
        return {
            "total_tasks": sum(len(task_list) for task_list in tasks.values() if isinstance(task_list, list)),
            "pending_count": len(tasks["pending"]),
            "completed_count": len(tasks["completed"]),
            "in_progress_count": len(tasks["in_progress"]),
            "goals_count": len(tasks["goals"]),
            "completion_rate": len(tasks["completed"]) / max(1, len(tasks["pending"]) + len(tasks["completed"]) + len(tasks["in_progress"])),
            "tasks_by_status": tasks
        }

class StreamingAgendaAgent(AgendaAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_callback: Optional[Callable[[StreamChunk], None]] = None
        self.current_drafts = {}
        self.last_agenda = ""
        self.tool_call_counter = 0
    
    def set_stream_callback(self, callback: Callable[[StreamChunk], None]):
        """设置流式回调函数"""
        self.stream_callback = callback
    
    def _emit_chunk(self, type: str, content: str, step_name: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None):
        """发送流式数据块"""
        if self.stream_callback:
            chunk = StreamChunk(type, content, step_name, metadata)
            self.stream_callback(chunk)
    
    def _emit_thinking(self, content: str):
        """发送思考过程"""
        self._emit_chunk("thinking", f"🤔 {content}", "思考")
    
    def _emit_agenda_update(self, new_agenda: str):
        """发送议程更新"""
        if new_agenda != self.last_agenda:
            # 解析议程变化
            agenda_summary = AgendaParser.get_agenda_summary(new_agenda)
            tasks_by_status = agenda_summary["tasks_by_status"]
            
            # 检测新完成的任务
            old_summary = AgendaParser.get_agenda_summary(self.last_agenda) if self.last_agenda else {"tasks_by_status": {"completed": []}}
            old_completed = {task["description"] for task in old_summary["tasks_by_status"]["completed"]}
            new_completed = {task["description"] for task in tasks_by_status["completed"]}
            newly_completed = new_completed - old_completed
            
            # 准备内容
            content_parts = []
            if newly_completed:
                content_parts.append(f"✅ 新完成任务: {', '.join(list(newly_completed)[:2])}")
            
            if agenda_summary["pending_count"] > 0:
                content_parts.append(f"📋 待办: {agenda_summary['pending_count']}项")
            
            if agenda_summary["in_progress_count"] > 0:
                content_parts.append(f"🔄 进行中: {agenda_summary['in_progress_count']}项")
            
            content = " | ".join(content_parts) if content_parts else "📋 议程已更新"
            
            self._emit_chunk("agenda_update", content, "议程更新", {
                "full_agenda": new_agenda,
                "agenda_summary": agenda_summary,
                "newly_completed_tasks": list(newly_completed)
            })
            
            self.last_agenda = new_agenda
    
    def _emit_tool_call(self, tool_name: str, params: Dict[str, Any]):
        """发送工具调用通知"""
        self.tool_call_counter += 1
        
        # 生成工具调用的友好描述
        tool_descriptions = {
            "knowledge_analyzer": "📚 知识分析器",
            "story_brainstorm": "💡 故事创意生成器", 
            "plot_developer": "📖 情节发展器",
            "longform_writer": "✍️ 长文写作器",
            "dialogue_writer": "💬 对话写作器",
            "logic_checker": "🔍 逻辑检查器",
            "style_enhancer": "✨ 文笔优化器",
            "calculator": "🧮 计算器"
        }
        
        tool_display_name = tool_descriptions.get(tool_name, f"🔧 {tool_name}")
        
        # 提取任务描述的简短版本
        task_desc = params.get("task_description", "")
        if len(task_desc) > 50:
            task_desc = task_desc[:47] + "..."
        
        content = f"{tool_display_name} | {task_desc}"
        
        self._emit_chunk("tool_call", content, "工具调用", {
            "tool_name": tool_name,
            "tool_display_name": tool_display_name,
            "params": params,
            "call_id": self.tool_call_counter,
            "call_timestamp": time.time()
        })
    
    def _emit_tool_result(self, tool_name: str, result: str, call_metadata: Optional[Dict] = None):
        """发送工具结果"""
        tool_descriptions = {
            "knowledge_analyzer": "📚 知识分析",
            "story_brainstorm": "💡 创意生成", 
            "plot_developer": "📖 情节发展",
            "longform_writer": "✍️ 文本创作",
            "dialogue_writer": "💬 对话创作",
            "logic_checker": "🔍 逻辑检查",
            "style_enhancer": "✨ 文笔优化",
            "calculator": "🧮 计算"
        }
        
        tool_display_name = tool_descriptions.get(tool_name, f"🔧 {tool_name}")
        
        # 生成结果预览
        if len(result) > 100:
            result_preview = result[:97] + "..."
        else:
            result_preview = result
        
        content = f"{tool_display_name}完成 | {result_preview}"
        
        # 检查是否有草稿内容生成
        draft_detected = "草稿" in result or "内容已保存" in result or len(result) > 200
        
        self._emit_chunk("tool_result", content, "工具结果", {
            "tool_name": tool_name,
            "tool_display_name": tool_display_name,
            "full_result": result,
            "result_length": len(result),
            "draft_detected": draft_detected,
            "call_metadata": call_metadata or {}
        })
    
    def _emit_draft_update(self, draft_id: str, content: str):
        """发送草稿更新"""
        self.current_drafts[draft_id] = content
        
        # 生成草稿摘要
        word_count = len(content)
        content_preview = content[:100] + "..." if len(content) > 100 else content
        
        self._emit_chunk("draft_update", f"📝 草稿更新: {draft_id} ({word_count}字)", "草稿更新", {
            "draft_id": draft_id,
            "content": content,
            "word_count": word_count,
            "content_preview": content_preview
        })
    
    def _emit_assistant_message(self, content: str, message_type: str = "general", metadata: Optional[Dict[str, Any]] = None):
        """发送助手消息"""
        self._emit_chunk("assistant_message", content, "助手回应", {
            "message_type": message_type,
            **(metadata or {})
        })
    
    # 重写核心方法以添加流式输出
    def _planner_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        self._emit_thinking("正在分析当前状态并规划下一步行动...")
        
        # 调用原始方法
        result = super()._planner_node(state)
        
        # 捕获并发送助手的规划响应
        if result.get("messages"):
            for msg in result.get("messages", []):
                if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == 'ai':
                    self._emit_assistant_message(str(msg.content), "planner_response", {
                        "step": "planning"
                    })
        
        # 发送议程更新
        if result.get("agenda_doc"):
            self._emit_agenda_update(result["agenda_doc"])
        
        # 检查行动类型并发送相应信息
        action = result.get("action_needed")
        if action == "call_tool":
            tool_name = result.get("tool_name")
            if tool_name:
                self._emit_thinking(f"决定调用工具: {tool_name}")
        elif action == "ask_human":
            question = result.get("human_question")
            if question:
                self._emit_thinking(f"需要询问用户: {question[:50]}...")
        elif action == "finish":
            self._emit_thinking("准备完成任务并生成最终答案")
        
        return result
    
    def _tool_node(self, state: SimplerAgendaState) -> SimplerAgendaState:
        tool_name = state.get("tool_name")
        tool_params = state.get("tool_params", {})
        
        # 发送工具调用通知
        if tool_name:
            self._emit_tool_call(tool_name, tool_params)
        
        # 调用原始方法
        result = super()._tool_node(state)
        
        # 捕获并发送助手的工具处理响应
        if result.get("messages"):
            for msg in result.get("messages", []):
                if hasattr(msg, 'content') and hasattr(msg, 'type') and msg.type == 'ai':
                    self._emit_assistant_message(str(msg.content), "tool_response", {
                        "tool_name": tool_name,
                        "step": "tool_processing"
                    })
        
        # 发送工具结果
        if tool_name and result.get("last_response"):
            call_metadata = {
                "call_id": self.tool_call_counter,
                "params": tool_params
            }
            self._emit_tool_result(tool_name, result["last_response"], call_metadata)
            
            # 检查并发送草稿更新
            self._check_and_emit_drafts(result)
        
        return result
    
    def _check_and_emit_drafts(self, state: SimplerAgendaState):
        """检查并发送草稿更新"""
        draft_outputs = state.get("draft_outputs", {})
        for draft_id, content in draft_outputs.items():
            if draft_id not in self.current_drafts or self.current_drafts[draft_id] != content:
                self._emit_draft_update(draft_id, content)
    
    def run_interactive_streaming(self, initial_query: str, max_iterations: int = 15):
        """带流式输出的交互式运行"""
        self._emit_chunk("start", f"🚀 开始处理请求: {initial_query}", "开始")
        
        # 调用原始方法
        result = self.run_interactive(initial_query, max_iterations)
        
        # 发送最终结果
        self._emit_chunk("final", result.get("final_answer", ""), "完成", {
            "agenda": result.get("final_agenda"),
            "draft_contents": result.get("draft_contents", {}),
            "message_count": result.get("message_history_count", 0),
            "tool_calls_made": self.tool_call_counter
        })
        
        return result
from typing import Dict, Any, List, Optional
from agent.core.state import SimplerAgendaState

class ResponseFormatter:
    """响应格式化工具类"""
    
    @staticmethod
    def format_final_response(state: SimplerAgendaState) -> Dict[str, Any]:
        """格式化最终响应"""
        result = {
            "final_answer": state.get("final_answer", ""),
            "is_interactive_pause": state.get("is_interactive_pause", False),
            "agenda_doc": state.get("agenda_doc", ""),
            "error_message": state.get("error_message"),
            "draft_contents": state.get("draft_outputs", {}),
            "human_question": state.get("human_question"),
            "action_needed": state.get("action_needed", ""),
            "session_metadata": ResponseFormatter._build_session_metadata(state)
        }
        
        # 🎯 关键修复：如果状态中没有议程，尝试从最后一条消息中提取
        if not result["agenda_doc"]:
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    content = str(last_message.content)
                    
                    # 尝试提取JSON中的议程信息
                    import re
                    import json
                    
                    # 匹配JSON块
                    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            if 'updated_agenda_doc' in json_data:
                                agenda_content = json_data['updated_agenda_doc']
                                # 处理转义字符
                                agenda_content = agenda_content.replace('\\n', '\n')
                                result["agenda_doc"] = agenda_content
                                result["updated_agenda_doc"] = agenda_content  # 🎯 关键：也设置这个字段
                                print(f"🎯 [ResponseFormatter修复] 从消息中提取到议程: {agenda_content}")
                        except json.JSONDecodeError as e:
                            print(f"⚠️ [ResponseFormatter修复] JSON解析失败: {e}")
        
        return result
    
    @staticmethod
    def _build_session_metadata(state: SimplerAgendaState) -> Dict[str, Any]:
        """构建会话元数据"""
        return {
            'message_count': len(state.get('messages', [])),
            'tool_calls_made': ResponseFormatter._count_tool_calls(state),
            'json_parse_errors': state.get('_json_parse_error_count', 0),
            'router_errors': state.get('_router_error_count', 0)
        }
    
    @staticmethod
    def _count_tool_calls(state: SimplerAgendaState) -> int:
        """统计工具调用次数"""
        messages = state.get('messages', [])
        tool_call_count = 0
        
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_call_count += len(msg.tool_calls)
        
        return tool_call_count
    
    @staticmethod
    def should_end_iteration(state: Dict[str, Any], iteration: int, logger) -> bool:
        """判断是否应该结束迭代"""
        if state.get("_force_end"):
            logger.info(f"✅ 第 {iteration+1} 次迭代后检测到强制结束标志")
            if not state.get("is_interactive_pause"):
                state["is_interactive_pause"] = True
            return True
            
        if state.get("is_interactive_pause"):
            logger.info(f"✅ 第 {iteration+1} 次迭代后检测到交互暂停")
            return True
            
        if state.get("action_needed") == "finish":
            logger.info(f"✅ 第 {iteration+1} 次迭代后检测到finish动作")
            return True
            
        if state.get("final_answer") and not state.get("action_needed"):
            logger.info(f"✅ 第 {iteration+1} 次迭代后检测到final_answer且无action")
            return True
            
        # 强制检查 - 如果有human_question但没有设置暂停
        if (state.get("human_question") and 
            not state.get("is_interactive_pause") and 
            iteration >= 0):
            logger.warning(f"⚠️ 第 {iteration+1} 次迭代：发现human_question但未设置暂停，强制设置")
            state["is_interactive_pause"] = True
            state["final_answer"] = state.get("human_question")
            state["action_needed"] = "finish"
            return True
            
        return False

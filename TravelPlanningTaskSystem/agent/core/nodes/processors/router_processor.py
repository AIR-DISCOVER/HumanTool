"""
路由处理器
"""
from typing import Dict, Any
from ...state import SimplerAgendaState

class RouterProcessor:
    """路由处理器 - 决定下一步执行什么"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def process(self, state: SimplerAgendaState) -> Dict[str, Any]:
        """处理路由逻辑"""
        self.logger.info("--- Router Node ---")
        
        try:
            action = state.get("action_needed")
            self.logger.info(f"Router: 检测到action = {action}")
            
            # 根据action决定下一步
            if action == "call_tool":
                return self._handle_call_tool(state)
            elif action == "ask_human":
                return self._handle_ask_human(state)
            elif action == "finish":
                return self._handle_finish(state)
            else:
                return self._handle_unknown_action(state, action)
                
        except Exception as e:
            self.logger.error(f"Router节点错误: {e}")
            return self._handle_error(state, e)
    
    def _handle_call_tool(self, state: SimplerAgendaState) -> Dict[str, Any]:
        """处理工具调用"""
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
    
    def _handle_ask_human(self, state: SimplerAgendaState) -> Dict[str, Any]:
        """处理用户询问"""
        human_question = state.get("human_question")
        if human_question:
            self.logger.info(f"Router: 准备询问用户")
            new_state = dict(state)
            new_state["is_interactive_pause"] = True
            new_state["final_answer"] = human_question
            
            # 🎯 关键修复：确保LLM响应内容传递到ai_pause消息
            llm_response_content = state.get("_llm_response_content")
            if llm_response_content:
                new_state["_llm_response_content"] = llm_response_content
                self.logger.info(f"Router: 传递LLM响应内容到ai_pause消息")
            else:
                self.logger.warning(f"Router: 未找到LLM响应内容，ai_pause消息将无LLM内容")
            
            return new_state
        else:
            self.logger.warning("Router: ask_human但未提供问题")
            new_state = dict(state)
            new_state["action_needed"] = "finish"
            new_state["final_answer"] = "系统准备询问但未配置问题"
            return new_state
    
    def _handle_finish(self, state: SimplerAgendaState) -> Dict[str, Any]:
        """处理完成 - 修复finish_answer字段丢失"""
        self.logger.info("Router: 任务完成")
        
        # 🎯 关键修复：确保state不为None
        if state is None:
            self.logger.error("Router: state为None，使用默认完成状态")
            return {
                "action_needed": "finish",
                "final_answer": "任务已完成",
                "finish_answer": "任务已完成"
            }
        
        # 🎯 关键修复：优先使用finish_answer，然后是final_answer
        finish_answer = state.get("finish_answer")
        final_answer = state.get("final_answer", "任务已完成")
        
        # 选择最合适的答案
        if finish_answer:
            chosen_answer = finish_answer
            self.logger.info(f"Router: 使用finish_answer: {chosen_answer[:50]}...")
        else:
            chosen_answer = final_answer
            self.logger.info(f"Router: 使用final_answer: {chosen_answer[:50]}...")
        
        new_state = dict(state)
        new_state["final_answer"] = chosen_answer
        
        # 🎯 关键修复：保留finish_answer字段，防止丢失
        if finish_answer:
            new_state["finish_answer"] = finish_answer
        
        return new_state
    
    def _handle_unknown_action(self, state: SimplerAgendaState, action: str) -> Dict[str, Any]:
        """处理未知动作"""
        self.logger.warning(f"Router: 未知action {action}")
        new_state = dict(state)
        new_state["action_needed"] = "finish"
        new_state["final_answer"] = "处理完成"
        return new_state
    
    def _handle_error(self, state: SimplerAgendaState, error: Exception) -> Dict[str, Any]:
        """处理错误"""
        new_state = dict(state)
        new_state["action_needed"] = "finish"
        new_state["final_answer"] = f"路由处理出错: {str(error)}"
        return new_state
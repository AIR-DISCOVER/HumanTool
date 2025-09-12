from typing import Literal
from langgraph.graph import END
from agent.core.state import SimplerAgendaState
from agent.utils.logger import Logger

class RouterLogic:
    """路由决策逻辑类"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def should_call_tool(self, state: SimplerAgendaState) -> Literal["call_tool", "ask_human", "continue_planning", "finish"]:
        """主路由决策函数"""
        return self._decide_next_step(state)
    
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
                
                # 🎯 关键修复：确保LLM响应内容传递到ai_pause消息
                llm_response_content = state.get("_llm_response_content")
                if llm_response_content:
                    self.logger.info(f"Router: 保持LLM响应内容用于ai_pause消息")
                else:
                    self.logger.warning(f"Router: 未找到LLM响应内容，ai_pause消息将无LLM内容")
                
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
                
                return "ask_human"
            else:
                self.logger.warning("Router: LLM请求询问人类但未提供问题。")
                return self._handle_router_error(state, "未提供问题的人类交互请求")

        elif action == "call_tool":
            if state.get("tool_name") and state.get("tool_call_id_for_next_tool_message"):
                return "call_tool"
            else:
                self.logger.warning("Router: 工具调用信息不完整。")
                return self._handle_router_error(state, "工具调用信息不完整")
                
        elif action == "self_update":
            return "continue_planning"
            
        elif action == "finish":
            self.logger.info(f"Router: 正常结束。Final answer: {state.get('final_answer', 'N/A')[:50]}...")
            return "finish"
            
        else:
            self.logger.warning(f"Router: 未知action '{action}'。")
            return self._handle_router_error(state, f"未知action '{action}'")
    
    def _handle_router_error(self, state: SimplerAgendaState, error_reason: str) -> str:
        """处理路由错误"""
        state["_router_error_count"] = state.get("_router_error_count", 0) + 1
        
        if state["_router_error_count"] > 2:
            self.logger.error(f"Router: 多次错误，强制结束。原因: {error_reason}")
            state["error_message"] = f"系统在决策时遇到问题: {error_reason}"
            state["final_answer"] = "抱歉，系统处理时出现问题。"
            state["action_needed"] = "finish"
            state["is_interactive_pause"] = False
            return "finish"
        
        return "continue_planning"

import json
import time
import uuid
import traceback
from typing import Dict, Any, Set
from langgraph.graph import END

class StreamingWrapper:
    """轻量级流式包装器 - 只负责事件转发"""
    
    def __init__(self, base_agent_class):
        self.base_agent_class = base_agent_class
    
    def create_agent(self, *args, **kwargs):
        class StreamingAgentWrapper(self.base_agent_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.final_result_cache = None
            
            def run_interactive_streaming(self, message, session_id=None):
                """流式处理入口 - 委托给基类"""

                self.logger.info(f"🎉 【steaming】(session_id={session_id})")
                try:
                    # 直接使用基类的流式方法
                    for event in super().run_interactive_streaming(message, max_iterations=15, session_id=session_id):
                        pass  # 基类已经处理了流式事件
                    
                    # 获取最终结果
                    result = super().get_final_result()
                    if session_id:
                        result['session_id'] = session_id
                    
                    self.final_result_cache = result
                    return result
                    
                except Exception as e:
                    print(f"❌ [WRAPPER] 流式处理错误: {e}")
                    return {
                        "final_answer": f"处理错误: {str(e)}",
                        "session_id": session_id,
                        "error_message": str(e)
                    }
            
            def get_final_result(self):
                return self.final_result_cache or super().get_final_result()
        
        return StreamingAgentWrapper(*args, **kwargs)

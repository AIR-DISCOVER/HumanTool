"""
故事精炼工具 - 单一职责版本
每个工具只做一件简单的事：对内容进行一次优化
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class StoryRefinerTool:
    """故事精炼工具 - 单一职责：对内容进行一次优化"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def refine_content(self, content: str, refinement_direction: str) -> str:
        """
        单一职责：对内容进行一次优化
        - 输入：内容 + 优化方向
        - 输出：优化后内容
        - 只做一件事：内容优化
        """
        system_prompt = f"""你是一位专业的内容编辑，负责对文本进行一次优化。

你的单一职责：按指定方向对内容进行一次优化

优化方向：{refinement_direction}

优化要求：
1. 仅针对指定方向进行优化
2. 保持原意不变
3. 语言精炼，效果显著
4. 一次完成，不重复修改

⚠️ 只做一件事：按指定方向优化内容"""

        human_prompt = f"""原始内容：
{content}

优化方向：{refinement_direction}

请按指定方向进行一次优化：

优化要求：
1. 仅针对"{refinement_direction}"这个方向优化
2. 保持原意和结构
3. 语言更加精炼有力
4. 直接输出优化后内容

请提供优化后内容。"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception:
            return content  # 出错时返回原文
    
    def execute(self, **kwargs) -> dict:
        content = kwargs.get("content", "")
        direction = kwargs.get("refinement_direction", "语言优化")
        result = self.refine_content(content, direction)
        return {"result": result, "thought": f"内容优化完成，方向: {direction}"}
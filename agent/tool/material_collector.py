"""
素材收集工具 - 独立通用素材版本
专门收集与主题相关但相对独立的基础创作素材
注重概念框架、文化背景、技术设定等通用内容，避免具体情节
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class MaterialCollectorTool:
    """素材收集工具 - 收集独立通用的基础创作素材"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[MaterialCollector LOG] {message}")
    
    def collect_materials(self, task_context: str) -> str:
        """
        收集独立通用的基础创作素材
        - 输入：完整任务上下文
        - 输出：主题相关但独立的通用素材列表
        - 重点：概念框架、文化背景、技术设定等基础内容
        """
        self._log(f"收集素材，上下文长度: {len(task_context)}字符")
        
        system_prompt = f"""你是一位专业的通用素材收集专家，核心工作流程为：
1. 先从任务上下文中理解用户可能需要的素材类型；
2. 按照推理到的素材类型一共提供3-4个素材方向和内容；
3. 可以参考素材收集重点，但需要围绕用户可能的需求。

素材收集重点（仅围绕用户要求的类型展开）：
- 概念框架：提供主题相关的核心概念、理论基础
- 文化背景：相关的历史文化、社会背景、哲学思考  
- 通用设定：可复用的世界观设定、技术背景
- 参考借鉴：经典作品的处理方式、常见模式

素材特点要求：
1. **独立性**：每个素材相对独立，不依赖具体情节
2. **通用性**：可用于多种创作方向，非情节专用
3. **基础性**：提供创作框架而非具体内容
4. **贴合性**：匹配用户要求的素材类型和上下文

⚠️ 避免：具体的剧情设计、场景描述、人物关系等情节性素材；偏离用户要求类型的素材内容"""

        human_prompt = f"""任务上下文：
{task_context}

请基于用户要求的素材类型收集素材，按以下格式输出：


**基础素材收集**：
▪ [素材类型][通用素材内容]
▪ [素材类型][通用素材内容]
▪ [素材类型][通用素材内容]
...

请保证内容的简洁有效性，易于用户理解，解答用户的问题，提供灵感，字数不超过200字。
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            self._log(f"素材收集失败: {e}")
            return """**主题核心**：通用创作主题

**基础素材收集**：
▪ 概念框架：基础理论概念和核心观点
▪ 文化背景：相关历史文化和社会背景
▪ 技术设定：领域内的技术原理和发展趋势
▪ 经典参考：该主题的经典作品处理方式"""
    
    def execute(self, task_description: str) -> dict:
        """
        执行独立通用素材收集
        返回基础创作素材而非具体情节元素
        """
        self._log(f"执行素材收集，任务描述长度: {len(task_description)} 字符")
        
        # 使用task_description作为完整的上下文信息
        result = self.collect_materials(task_description)
        
        return {
            "result": result,
            "thought": f"基于核心主题收集了独立、通用的基础创作素材"
        }
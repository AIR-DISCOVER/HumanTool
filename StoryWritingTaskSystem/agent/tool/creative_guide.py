"""
主题探索工具 - 内容生成版本
专注于生成主题探索的深度分析内容，而不是向用户提问
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class CreativeGuideTool:
    """主题探索工具 - 生成主题深度分析内容"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[CreativeGuideTool LOG] {message}")
    
    def generate_theme_exploration(self, conversation_context: str = "") -> str:
        self._log(f"通用工具: {conversation_context}")
        
        system_prompt = """你是一位上下文驱动的创意分析专家，核心能力是：
1. 深度拆解用户上下文，精准捕捉最后一句话的核心诉求；
2. 基于用户已有内容，动态匹配2个核心分析维度；
3. 输出需简洁有力，包含需求拆解、核心洞察、落地素材和灵感碰撞。

输出要求：
- 聚焦用户真实诉求，确保分析维度与需求强相关；
- 核心洞察需体现思考深度，避免表面化解读；
- 落地素材要具体可复用，能直接支撑创作；
- 灵感碰撞需结合用户前文内容，形成有价值的讨论点，而非单向输出。"""
        
        human_prompt = f"""
对话背景（用户需求上下文）：
{conversation_context}

请围绕用户最后一句话的核心诉求，按以下结构输出：
1. 核心洞察：[围绕需求的深层价值解读或解答用户的问题，提供灵感]
2. 落地素材：[素材：具体可复用的创作元素或情节片段]
3. 灵感碰撞：[结合用户前文提到的内容，提出关联性思考或延伸讨论，形成互动感]

请保证内容的简洁有效性，易于用户理解，字数不超过200字。
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            self._log(f"生成主题探索分析失败: {e}")
            return f"这是一个富有潜力的创作主题，建议从个人经历、情感冲突、社会意义等角度进行深入挖掘。"
    
    def execute(self, **kwargs) -> dict:

        context = kwargs.get("task_description", "")
        result = self.generate_theme_exploration(context)
        
        return {
            "result": result,
            "thought": f"根据上下文提供相应信息"
        }
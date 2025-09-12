"""
主题聚焦工具 - 单一职责版本
每个工具只做一件简单的事：对主题进行一次聚焦尝试
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class ThemeFocuserTool:
    """主题聚焦工具 - 单一职责：对主题进行一次聚焦尝试"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[ThemeFocuser LOG] {message}")
    
    def focus_theme(self, materials: str) -> str:
        """
        单一职责：对主题进行一次聚焦尝试
        - 输入：宽泛主题 + 素材 + 聚焦方法
        - 输出：一个聚焦后的主题建议
        - 只做一件事：主题聚焦
        """
        self._log(f"主题聚焦")
        
        system_prompt = """你是一位专业的主题聚焦专家，负责帮助用户从上下文对话中提炼富有创意的核心表达点。

你的单一职责：基于指定方法对主题进行一次聚焦尝试

聚焦方法工具箱：
- 挑战假设：识别并挑战关于主题的隐含假设
- 焦点转移：从不同视角重新审视主题
- 情感定位：找到主题的核心情感表达
- 价值深挖：挖掘主题的深层社会意义

输出要求：
1. 基于指定方法进行一次聚焦尝试
2. 提供一个清晰、有力的聚焦主题
3. 简要说明聚焦的理由和价值
4. 语言简洁，突出可操作性

⚠️ 只做一件事：基于指定方法进行一次主题聚焦"""

        human_prompt = f"""
已有上下文：{materials}

聚焦要求：
1. 运用科学方法重新审视主题
2. 识别主题中最有表达价值的点
3. 将宽泛概念聚焦为一个具体切入点
4. 确保聚焦后的主题有足够的创作空间

输出格式：

【聚焦结果】

聚焦主题：...
聚焦理由：...
创作价值：...

请直接提供聚焦结果。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            self._log(f"主题聚焦失败: {e}")
            return f"主题的核心似乎是关于人性中的某种冲突。"
    
    def execute(self, **kwargs) -> dict:
        """
        执行主题聚焦 - 单一职责版本
        """
        context = kwargs.get("task_description", "")
        
        result = self.focus_theme(context)
        
        # 简化返回结构，只做一件事
        return {
            "result": result,
            "thought": f"主题聚焦完成"
        }
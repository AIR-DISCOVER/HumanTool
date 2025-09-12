from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class KnowledgeAnalyzerTool:
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose

    def _log(self, message: str):
        if self.verbose:
            print(f"[KnowledgeAnalyzerTool LOG] {message}")

    def execute(self, task_description: str) -> str:
        """
        使用LLM基于其内部知识执行分析或生成内容。
        :param task_description: 需要分析或生成的具体任务描述。
        :return: LLM生成的分析结果或内容。
        """
        self._log(f"接收到分析任务: {task_description}")
        
        tool_system_prompt = """你是一位专业的分析师和内容撰写员。你的任务是根据用户提供的具体任务描述，清晰、准确、简洁地完成分析或内容生成。
请直接针对任务本身给出结果，不需要额外的对话或解释你的工作方式。专注于提供高质量的、基于通用知识的回答。事实问题可以提供数据。"""
        
        tool_human_prompt = f"请执行以下任务：\n\n{task_description}"
        
        messages = [
            SystemMessage(content=tool_system_prompt),
            HumanMessage(content=tool_human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            result_content = response.content
            return result_content
        except Exception as e:
            self._log(f"知识分析工具LLM调用失败: {e}")
            return f"错误：在执行知识分析任务 '{task_description}' 时发生错误: {str(e)}"

class LLMThinkingTool:
    """当需要进行深度思考、问题分解、探索性分析或生成中间步骤时使用"""
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose

    def _log(self, message: str):
        if self.verbose:
            print(f"[LLMThinkingTool LOG] {message}")

    def execute(self, thinking_task: str, context: str = "") -> str:
        """
        使用LLM进行深度思考、问题分解或探索性分析。
        :param thinking_task: 需要思考的具体问题或任务。
        :param context: 可选的上下文信息，帮助LLM更好地理解背景。
        :return: LLM生成的思考过程、分析路径或关键洞察。
        """
        self._log(f"接收到思考任务: {thinking_task}")
        if context:
            self._log(f"附带上下文 (部分): {context[:100]}...")

        tool_system_prompt = """你是一位深度思考者和策略分析师。你的任务是针对给定的问题或任务进行深入的、结构化的思考。
请展现你的思考过程，例如：
- 分解复杂问题为更小的、可管理的部分。
- 探索不同的可能性、角度和假设。
- 识别关键因素、依赖关系和潜在障碍。
- 权衡不同方案的利弊和风险。
- 提出初步的结论、洞察或行动建议。
请不要直接给出最终答案，而是侧重于展示清晰的、有逻辑的思考路径和中间步骤。你的输出应该是帮助进行下一步决策的思考材料。"""

        tool_human_prompt = f"请针对以下任务进行深度思考：\n\n任务：{thinking_task}\n"
        if context:
            tool_human_prompt += f"\n相关背景信息：\n{context}\n"
        
        tool_human_prompt += "\n请展示你的思考过程和关键洞察："

        messages = [
            SystemMessage(content=tool_system_prompt),
            HumanMessage(content=tool_human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            result_content = response.content
            return result_content
        except Exception as e:
            self._log(f"LLM思考工具调用失败: {e}")
            return f"错误：在执行思考任务 '{thinking_task}' 时发生错误: {str(e)}"

class LLMGeneralTool:
    """通用LLM调用工具 - 可以进行任何类型的LLM对话和生成"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose

    def _log(self, message: str):
        if self.verbose:
            print(f"[LLMGeneralTool LOG] {message}")
    
    def execute(self, task_description: str, **kwargs) -> str:
        """
        通用LLM调用工具 - 增强历史记录处理
        """
        self._log(f"接收到通用LLM任务: {task_description[:100]}...")
        
        # 🎯 检测是否包含历史记录
        has_history = "【聊天历史记录】" in task_description or "【已执行的工具和结果】" in task_description
        self._log(f"是否包含历史记录: {has_history}")
        
        if has_history:
            # 包含历史记录的增强提示词
            system_prompt = """
你是一个智能助手，能够帮助用户完成各种任务。你可以看到完整的对话历史和之前工具执行的结果。中文生成。

重要指导原则：
1. 仔细阅读聊天历史记录，了解用户的真实需求和偏好
2. 查看之前工具执行的结果，避免重复生成相同内容
3. 基于已有成果进行优化、补充或扩展，而不是重新开始（务必保留已有的有效信息）
4. 确保输出与用户的期望和对话上下文保持一致
5. 只提供信息，不提供计算、建议等内容。

"""

        # 构建人类提示词
        human_prompt = f"任务：{task_description}"
        
        # 如果有额外参数，添加到提示词中
        if kwargs:
            for key, value in kwargs.items():
                if value:
                    human_prompt += f"\n{key}: {value}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        
        try:
            response = self.llm.invoke(messages)
            result_content = response.content
            self._log(f"LLM任务完成，结果长度: {len(result_content)}")
            return result_content
        except Exception as e:
            self._log(f"LLM通用工具调用失败: {e}")
            return f"错误：在执行LLM任务 '{task_description[:50]}...' 时发生错误: {str(e)}"
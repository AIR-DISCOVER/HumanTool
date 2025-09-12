"""
故事规划工具 - 基于四阶段评价指标的深度叙事版本
符合专业四阶段创作标准的高质量故事大纲生成工具
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class StoryPlannerTool:
    """故事规划工具 - 基于四阶段评价指标生成深度故事大纲"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def plan_story(self, story_length: str = "中等", context: str = "") -> str:
        """
        基于四阶段评价指标生成高质量故事大纲
        - 输入：主题 + 素材 + 长度要求 + 完整上下文
        - 输出：符合四阶段标准的深度故事大纲
        - 确保每个情节点服务于多项评价指标
        """
        system_prompt = """你是一位专业的故事大纲写作师，必须基于用户提供的上下文，创建符合专业标准的高质量故事大纲。

## 🎯 核心使命
1. **上下文忠实性**：使用用户提供的所有具体信息，发挥想象力进行扩展
2. **专业标准化**：确保故事大纲符合以下创作要求

## 📊 大纲创作要求

### 1：核心概念与人物驱动的大纲设计
- 故事核心（前提、人物多维度、明确欲望、初步主题）具有强吸引力与深度。 
- 故事的根基——前提能激发持久的兴趣，人物具备在压力下展现真实本质的多维度，以及其意识与潜意识欲望足以驱动故事，并对故事的终极意义有初步的认识。

### 2：世界设定与激励事件的大纲构建  
- 故事世界要有具体性、自洽性及激励事件的有效性。 
- 故事的背景设定（时代、持续时间、地点、冲突层次）需要具体、细致、自洽。
- 激励事件可以作为主人公生活中不可逆转的决定性转折点，在恰当的时间点发生，从而提出主要戏剧性问题并驱动观众好奇心。

### 3：结构发展与冲突升级的大纲架构
- 故事主线、冲突升级需要具备有效性与结构完整性。 
- 主人公的探索旅程需要清晰，对抗力量需要强大且多维度（内心、人际、外部），以及冲突需要通过渐进式复杂化不断升级，从而迫使人物做出高风险选择。
- 通过清晰的三幕结构推动情节和人物发展。

### 4：危机高潮与核心思想的大纲确认
- 危机决策需要具备真实性、高潮富有意义与不可逆性，精准传达核心思想。 
- 主人公在危机中需要面临真实的困境并做出符合其本质的选择，高潮需要带来价值的绝对、不可逆转的转变并充满意义。
- 结局能让观众带着对故事核心思想的深刻理解和满足感离开。

"""
        human_prompt = f"""
## 📝 上下文内容
{context}

## 🎭 任务要求
当前执行工具为 story_planner，若之前执行过story_planner，请严格根据用户要求更新输出内容；若之前未执行过story_planner,请仔细理解上下文内容理解大纲的生成要求，发挥想象力进行扩展。

请基于以上上下文内容和用户素材，严格遵守system中定义的大纲生成要求，生成符合标准的高质量故事大纲。

## ⚠️ 输出要求
必须按以下四部分格式输出，故事内容必须完整，不得添加其他无关结构：

**第一部分：故事概括**
- 用一句话总结整个故事的核心

**第二部分：第一幕**
- 用2-3句连贯的话描述第一幕情节发展，不分条列出

**第三部分：第二幕** 
- 用2-3句连贯的话描述第二幕情节发展，不分条列出

**第四部分：第三幕**
- 用2-3句连贯的话描述第三幕情节发展，不分条列出

## ⚠️ 输出规范
1. 严格按照上述四部分格式输出，不得添加其他结构；
2. 必须输出一个完整的故事。
"""
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"故事规划生成失败：{str(e)}。请检查LLM连接或重试。"
    
    def execute(self, **kwargs) -> dict:
        # 🎯 增强上下文获取：task_description已包含完整的对话历史、工具执行历史和CSP状态
        context = kwargs.get("task_description", "")
        story_length = kwargs.get("story_length", "中等")
        
        # 🎯 调试：输出接收到的上下文信息
        print(f"🔍 [STORY_PLANNER DEBUG] 接收到的上下文长度: {len(context)}")
        print(f"🔍 [STORY_PLANNER DEBUG] 上下文前500字符: {context[:500]}...")
        
        result = self.plan_story(story_length, context)
        return {"result": result, "thought": f"故事规划完成，已充分利用对话历史、工具执行记录和用户创意素材"}
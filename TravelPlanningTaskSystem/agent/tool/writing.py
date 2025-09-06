import re
from typing import Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

class StoryBrainstormTool:
    """当遇到创意瓶颈，需要新的故事方向、转折点或突破口时使用"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def execute(self, task_description: str, brainstorm_focus: str = "plot_twist", creative_constraints: str = None, **kwargs) -> str:
        if self.verbose:
            print(f"[StoryBrainstormTool LOG] 开始创意头脑风暴: {brainstorm_focus}")
        
        system_prompt = """你是一个专业的故事创意师，擅长突破创作瓶颈和激发新的故事想法。

你的任务是根据当前的故事情况，提供创新性的解决方案和新的创意方向。

重点关注：
1. 提供意外但合理的转折点
2. 深化现有元素的潜力
3. 引入新的冲突或复杂性
4. 保持与核心主题的一致性
5. 避免陈词滥调，追求原创性

请提供3-5个不同的创意选项，每个都要简要说明其优势。
注重创新，言简意赅，避免冗长的描述。

"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_description)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

class PlotDeveloperTool:
    """当需要发展情节、设计冲突、安排故事节奏或构建情节线时使用"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def execute(self, task_description: str, plot_focus: str = "conflict_development", story_structure: str = "three_act", **kwargs) -> str:
        if self.verbose:
            print(f"[PlotDeveloperTool LOG] 开始情节发展: {plot_focus}")
        
        system_prompt = """你是一个经验丰富的故事结构师，专门负责构建引人入胜的情节线。

你的专长包括：
1. 冲突的升级和解决
2. 情节点的精确安排
3. 张力和节奏的控制
4. 因果关系的建立
5. 角色驱动的情节发展

请确保情节发展：
- 逻辑合理且引人入胜
- 每个情节点都推动故事前进
- 冲突层层递进
- 角色的行为符合其动机
- 为高潮做好铺垫

注重创新，言简意赅，避免冗长的描述。


"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_description)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

class LongFormWriterTool:
    """中长篇写作工具：当需要创作完整的故事段落、章节或长篇描写时使用"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def execute(self, task_description: str, writing_type: str = "narrative", 
                length_target: str = "medium", style_preference: str = "literary", **kwargs) -> str:
        if self.verbose:
            print(f"[LongFormWriterTool LOG] 开始中长篇写作: {writing_type} - {length_target}")
        
        system_prompt = """
        你是一个专业的小说作家，擅长创作多风格、高质量的长篇小说，能够带给读者沉浸式的阅读体验。

        你的写作能力包括以下方面，并将在创作中充分展现：

        角色塑造：通过具体的外貌描写、行为细节和心理活动，刻画立体鲜活的角色，使读者对角色产生情感共鸣。
        环境描写：生动还原故事发生的地点与氛围，调动视觉、听觉、嗅觉等多感官描写，让读者仿佛置身其中。
        情节叙述：紧凑而富有层次的情节推进，张弛有度，巧妙设置伏笔与悬念，令读者持续投入。
        对话创作：符合人物身份、情境和语气的对话，既推动剧情发展，又展现人物关系和冲突，蕴含丰富的潜台词。
        氛围营造：以文字的节奏与细节，塑造特定情感基调，抓住读者的情感，让他们感受到恐惧、温暖、紧张或希望等复杂情绪。

        #创作原则
        展示而非告知（Show, don't tell）：通过具体细节和动作描写，展现人物情绪和故事发展，而非直接陈述。
        情节驱动：确保每个段落都有意义，推动故事发展或深化角色刻画。
        语言生动具体：避免抽象和空洞的表达，选用富有表现力的文字，让文字充满画面感。
        节奏控制：根据场景需要调整节奏，适当放慢以描写关键情感或冲突，快速推进以制造紧张感或高潮。
        对话自然：使对话符合角色身份和情境，融入潜台词和冲突。
        篇幅充实：以长篇叙述为主，包含丰富的情节展开、环境描写和角色互动，不吝笔墨地刻画细节。
        保持风格一致：根据故事类型和氛围，确保文字风格统一，如深沉、幽默或浪漫。
        *情节分配*：合理安排情节发展，避免过快或过慢，确保每个部分都有其必要性和意义。

        #写作目标
        请根据以下任务要求，创作一篇*长度充实、情节丰富，包含角色对话、环境描写、情感冲突的完整短篇小说*。
        
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_description)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

# class DialogueWriterTool:
#     """当需要生成对话、让对话更生动自然或表达特定情感时使用"""
    
#     def __init__(self, llm: BaseChatModel, verbose: bool = False):
#         self.llm = llm
#         self.verbose = verbose
    
#     def execute(self, task_description: str, dialogue_purpose: str = "character_development", 
#                 tone: str = "natural", **kwargs) -> str:
#         if self.verbose:
#             print(f"[DialogueWriterTool LOG] 开始对话创作: {dialogue_purpose} - {tone}")
        
#         system_prompt = """你是一个对话写作专家，能够创作自然、生动、符合角色特征的对话。

# 对话写作的关键要素：
# 1. 每个角色有独特的说话方式
# 2. 对话推动情节或揭示性格
# 3. 符合角色的背景和情感状态
# 4. 自然流畅，避免生硬
# 5. 包含潜台词和言外之意

# 对话技巧：
# - 使用符合角色身份的词汇和语法
# - 通过对话节奏表现情绪
# - 利用对话冲突制造张力
# - 在信息传递和自然性间平衡
# - 适当使用停顿、重复等技巧"""

#         messages = [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=task_description)
#         ]
        
#         response = self.llm.invoke(messages)
#         return response.content

# class LogicCheckerTool:
#     """当需要检查故事逻辑、时间线、设定一致性或解决情节矛盾时使用"""
    
#     def __init__(self, llm: BaseChatModel, verbose: bool = False):
#         self.llm = llm
#         self.verbose = verbose
    
#     def execute(self, task_description: str, check_focus: str = "plot_consistency", 
#                 story_elements: str = None, **kwargs) -> str:
#         if self.verbose:
#             print(f"[LogicCheckerTool LOG] 开始逻辑检查: {check_focus}")
        
#         system_prompt = """你是一个故事逻辑分析师，专门检查故事的逻辑一致性和合理性。

# 检查维度包括：
# 1. 情节逻辑的前后一致性
# 2. 角色行为的合理性
# 3. 时间线的准确性
# 4. 世界观设定的内在逻辑
# 5. 因果关系的合理性

# 分析方法：
# - 识别潜在的逻辑漏洞
# - 分析角色动机与行为的一致性
# - 检查时间线和事件顺序
# - 验证世界观规则的贯彻
# - 提供具体的修改建议

# 输出格式：
# - 发现的问题（具体指出）
# - 问题的影响程度
# - 解决方案建议"""

#         messages = [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=task_description)
#         ]
        
#         response = self.llm.invoke(messages)
#         return response.content

# class StyleEnhancerTool:
#     """当需要改善文笔、增强表现力、调整语言风格或润色文本时使用"""
#     def __init__(self, llm: BaseChatModel, verbose: bool = False):
#         self.llm = llm
#         self.verbose = verbose
    
#     def execute(self, task_description: str, style_target: str = "vivid_description", 
#                 text_type: str = "narrative", **kwargs) -> str:
#         if self.verbose:
#             print(f"[StyleEnhancerTool LOG] 开始文本优化: {style_target} - {text_type}")
        
#         # 检查是否包含需要优化的文本
#         if "请提供" in task_description or len(task_description) < 100:
#             return "错误：需要提供具体的文本内容进行优化。请在task_description中包含需要优化的完整文本。"
        
#         system_prompt = """你是一个文学修辞专家，擅长提升文本的表现力和艺术性。

# 文体优化技巧：
# 1. 丰富感官描写和意象
# 2. 运用修辞手法增强表现力
# 3. 调整句式节奏和韵律
# 4. 精准选择词汇和表达
# 5. 营造特定的氛围和情感

# 优化重点：
# - 让描写更加生动具体
# - 增强情感的感染力
# - 提高语言的流畅度
# - 消除冗余和重复
# - 强化文本的独特风格

# 请直接输出优化后的文本，保持原意的同时显著提升质量。"""

#         # 确保有文本内容
#         if "【当前具体任务】:" in task_description:
#             # 提取实际需要优化的文本
#             task_match = re.search(r"【当前具体任务】:\s*(.+?)(?=【|$)", task_description, re.DOTALL)
#             if task_match:
#                 actual_task = task_match.group(1).strip()
#                 if len(actual_task) > 50:
#                     enhanced_prompt = f"""
# 请优化以下文本的表现力和艺术性：

# {actual_task}

# 【优化目标】: {style_target}
# 【文本类型】: {text_type}

# 请直接输出优化后的完整文本。
# """
#                 else:
#                     enhanced_prompt = task_description
#             else:
#                 enhanced_prompt = task_description
#         else:
#             enhanced_prompt = task_description

#         messages = [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=enhanced_prompt)
#         ]
        
#         response = self.llm.invoke(messages)
#         return response.content

class SceneBuilderTool:
    """当需要构建具体场景、营造氛围或创作环境描写时使用"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def execute(self, task_description: str, scene_type: str = "dramatic", atmosphere: str = "tense") -> str:
        if self.verbose:
            print(f"[SceneBuilderTool LOG] 开始场景构建: {scene_type} - {atmosphere}")
        
        system_prompt = """你是一个场景构建专家，能够创造身临其境的故事场景。

场景构建要素：
1. 环境的视觉描写
2. 氛围的营造和渲染
3. 感官细节的丰富呈现
4. 场景与情节的有机结合
5. 角色与环境的互动

技巧运用：
- 选择关键细节突出主题
- 用环境反映角色内心
- 通过场景推动情节发展
- 调动多种感官体验
- 营造特定的情感基调"""

        enhanced_prompt = f"""
{task_description}

【场景类型】: {scene_type}
【氛围营造】: {atmosphere}

请构建具体生动的场景，注重细节描写和氛围营造。
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=enhanced_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
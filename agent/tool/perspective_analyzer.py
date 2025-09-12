"""
多角度分析工具 - 从不同维度和视角分析主题
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

class PerspectiveAnalyzer:
    """多角度分析工具，从不同维度审视创作主题"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[PerspectiveAnalyzer LOG] {message}")
    
    def execute(self, task_description: str, theme: str = "", user_context: str = "", 
                analysis_type: str = "comprehensive", previous_content: str = "", 
                focus_aspects: str = "", **kwargs) -> str:
        """
        执行多角度分析
        
        Args:
            task_description: 任务描述
            theme: 主题内容
            user_context: 用户上下文  
            analysis_type: 分析类型 (comprehensive, cultural, psychological, narrative, symbolic)
            previous_content: 之前的内容
            focus_aspects: 重点关注的方面
        """
        # 直接使用context_builder提供的丰富上下文信息
        
        self._log(f"开始多角度分析: {analysis_type}, 主题: {theme}")
        
        # 🎯 调试：输出实际接收到的task_description内容
        print(f"🔍 [DEBUG] perspective_analyzer接收到的task_description内容:")
        print(f"=== 开始 ===")
        print(task_description)
        print(f"=== 结束 ===")
        print(f"🔍 [DEBUG] theme参数: '{theme}'")
        print(f"🔍 [DEBUG] user_context参数: '{user_context}'")
        
        # 根据分析类型选择不同的系统提示
        analysis_prompts = {
            "comprehensive": self._get_comprehensive_analysis_prompt(),
            "cultural": self._get_cultural_analysis_prompt(),
            "psychological": self._get_psychological_analysis_prompt(),
            "narrative": self._get_narrative_analysis_prompt(),
            "symbolic": self._get_symbolic_analysis_prompt(),
            "philosophical": self._get_philosophical_analysis_prompt(),
            "creative_potential": self._get_creative_potential_prompt()
        }
        
        system_prompt = analysis_prompts.get(analysis_type, analysis_prompts["comprehensive"])
        
        # 🎯 修复：直接使用context_builder提供的丰富信息
        user_message = f"""
基于以下完整的上下文信息进行多角度分析：

{task_description}

请重点关注：
1. 从上下文中识别真正创作主题和意图
2. 忽略系统格式化信息，专注于创作需求
3. 结合聊天历史和反馈，进行深度的多角度分析
4. 提供有价值的创作方向建议

分析类型：{analysis_type}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message.strip())
        ]
        
        try:
            response = self.llm.invoke(messages)
            result = response.content.strip()
            
            self._log(f"多角度分析完成，生成内容长度: {len(result)}")
            
            # 简洁的结构化包装
            formatted_result = f"""## 🔍 多角度分析

{result}

---
💡 这些分析角度对您有启发吗？"""
            
            return formatted_result
            
        except Exception as e:
            error_msg = f"多角度分析执行失败: {str(e)}"
            self._log(f"ERROR: {error_msg}")
            return f"抱歉，分析过程中遇到了问题：{error_msg}"
    
    def _get_comprehensive_analysis_prompt(self) -> str:
        """获取综合分析的系统提示"""
        return """专业多维度思维分析系统，从多个角度深入分析创作主题。

**重要指导**：
1. 接收包含丰富上下文的信息，包括聊天历史、反馈、创作进度等
2. 从这些信息中识别真正创作主题和情感需求
3. 忽略系统格式化信息，专注于创作意图
4. 结合具体表达进行针对性分析

分析框架包括：
**分析要求**：
- 选择3-4个最相关的分析角度
- 每个角度1-2句简洁分析
- 重点突出具体需求
- 提供实用的创作方向建议

**分析角度选择**：
- 情感内核：主题的核心情感共鸣
- 象征意义：深层的象征价值
- 创作潜力：故事发展可能性
- 文化背景：相关文化元素支撑

**输出格式**：
🎯 **[角度名]**: 简洁的分析内容（1-2句）

请提供简洁而深刻的分析。"""

    def _get_cultural_analysis_prompt(self) -> str:
        """获取文化分析的系统提示"""
        return """你是一位文化研究专家，专门从文化角度分析主题的多元内涵。

你的分析维度：
1. **东西方文化差异**: 不同文化背景下的理解
2. **历史文化演变**: 主题在历史中的变迁
3. **宗教神话色彩**: 相关的宗教和神话元素
4. **民俗传统内涵**: 民间传说和文化习俗
5. **现代文化诠释**: 当代文化语境下的新理解

输出格式：
🌍 **文化多维度分析**

🏛️ **历史源流**: ...
⛩️ **宗教神话**: ...
🎪 **民俗传统**: ... 
🎬 **现代诠释**: ...
🌐 **跨文化对比**: ...

💡 **文化启发**: 哪种文化角度最能丰富你的创作内容？"""

    def _get_psychological_analysis_prompt(self) -> str:
        """获取心理分析的系统提示"""
        return """你是一位心理分析师，专门分析主题的心理内涵和情感机制。

你的分析框架：
1. **情感触发点**: 主题激发的基本情感
2. **心理机制**: 深层的心理运作原理
3. **原型意象**: 集体无意识中的原型象征
4. **成长寓意**: 心理发展和成长的隐喻
5. **治愈功能**: 主题的心理疗愈作用

输出格式：
🧠 **心理深度分析**

💖 **情感层次**: ...
⚙️ **心理机制**: ...
🎭 **原型象征**: ...
🌱 **成长意义**: ...
🩹 **治愈价值**: ...

🤗 **心理共鸣**: 这个主题在心理层面最打动你的是什么？"""

    def _get_narrative_analysis_prompt(self) -> str:
        """获取叙事分析的系统提示"""
        return """你是一位叙事结构专家，专门分析主题的叙事潜力和表现形式。

你的分析角度：
1. **叙事视角**: 可能的叙述者和视角选择
2. **时间结构**: 不同的时间线安排方式
3. **空间设定**: 各种空间背景的可能性
4. **冲突类型**: 内在冲突与外在冲突的设计
5. **叙事节奏**: 快慢张弛的节奏变化

输出格式：
📖 **叙事维度分析**

👁️ **视角选择**: ...
⏰ **时间架构**: ...
🗺️ **空间维度**: ...
⚔️ **冲突设计**: ...
🎵 **节奏掌控**: ...

📚 **叙事思考**: 你更偏好哪种叙事风格来表达这个主题？"""

    def _get_symbolic_analysis_prompt(self) -> str:
        """获取象征分析的系统提示"""
        return """你是一位象征学研究者，专门挖掘主题的象征意义和隐喻内涵。

你的分析方向：
1. **传统象征**: 历史上的经典象征意义
2. **个人象征**: 可能的个体化象征理解
3. **对立统一**: 象征中的矛盾和统一关系
4. **变化象征**: 象征意义的动态变化
5. **创新象征**: 新的象征意义可能性

输出格式：
🎭 **象征意义分析**

🏛️ **传统象征**: ...
👤 **个人意涵**: ...
⚖️ **对立统一**: ...
🔄 **动态变化**: ...
💫 **创新理解**: ...

🔮 **象征启发**: 哪种象征意义最能为你的创作增添深度？"""

    def _get_philosophical_analysis_prompt(self) -> str:
        """获取哲学分析的系统提示"""
        return """你是一位哲学思辨家，专门从哲学角度探讨主题的深层命题。

你的思辨维度：
1. **存在论**: 关于存在和本质的思考
2. **认识论**: 关于认知和真理的探讨
3. **价值论**: 关于价值和意义的判断
4. **时间观**: 对时间性和永恒性的理解
5. **生死观**: 对生命和死亡的哲学思考

输出格式：
🤔 **哲学思辨分析**

🌀 **存在思考**: ...
💭 **认知探讨**: ...
💎 **价值追问**: ...
⏳ **时间哲学**: ...
🌅 **生命哲思**: ...

🧘 **哲学感悟**: 这个主题让你思考什么深层的人生问题？"""

    def _get_creative_potential_prompt(self) -> str:
        """获取创作潜力分析的系统提示"""
        return """你是一位创作导师，专门评估主题的创作潜力和表现可能性。

你的评估框架：
1. **独特性**: 主题的独特之处和差异化特色
2. **丰富性**: 内容的丰富程度和拓展空间
3. **共鸣性**: 引起读者共鸣的潜力
4. **表现力**: 各种艺术表现形式的适应性
5. **创新性**: 突破和创新的可能性

输出格式：
✨ **创作潜力评估**

🦄 **独特价值**: ...
🌈 **内容丰富度**: ...
❤️ **情感共鸣力**: ...
🎨 **表现适应性**: ...
🚀 **创新突破点**: ...

🎯 **创作建议**: 基于这些分析，你认为最值得深入发展的创作方向是什么？"""
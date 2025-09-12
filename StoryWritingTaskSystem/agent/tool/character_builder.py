"""
角色构建器 - 专门用于创建和发展角色
"""

class CharacterBuilderTool:
    """角色构建器：快速创建各类角色，支持agent主动调用"""
    
    def __init__(self, llm=None, verbose=False):
        self.llm = llm
        self.verbose = verbose
        
    def execute(self, character_request: str, character_type: str = "auto", 
                story_context: str = "", existing_content: str = "", 
                task_description: str = "", **kwargs) -> str:
        """
        执行角色构建任务
        
        Args:
            character_request: 用户对角色的具体要求
            character_type: 角色类型 (auto/主角/配角/反派/路人)
            story_context: 当前故事背景
            existing_content: 已有的故事内容
            task_description: 任务描述（可选，兼容性参数）
        """
        
        # 🎯 兼容性处理：如果有task_description但没有character_request，从task_description中提取要求
        if task_description and not character_request:
            character_request = task_description
        elif task_description and character_request:
            # 如果两者都有，将task_description合并到story_context
            story_context = f"{story_context}. 任务要求：{task_description}"
        try:
            if self.verbose:
                print(f"👥 开始构建角色: {character_request[:50]}...")
            
            # 构建角色创建提示
            character_prompt = self._build_character_prompt(
                character_request, character_type, story_context, existing_content
            )
            
            # 调用LLM生成角色
            if self.llm:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=character_prompt)])
                character_content = response.content
            else:
                character_content = "角色构建工具暂时不可用，请稍后再试。"
            
            # 格式化输出
            formatted_result = self._format_character_output(character_content, character_request)
            
            if self.verbose:
                print(f"✅ 角色构建完成")
                
            return formatted_result
            
        except Exception as e:
            error_msg = f"角色构建过程中出现错误: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return error_msg
    
    def _build_character_prompt(self, character_request: str, character_type: str, 
                               story_context: str, existing_content: str) -> str:
        """构建角色创建提示词"""
        
        # 开放性角色创建，不预设类型限制
        if character_type == "auto":
            character_type = "开放创作"  # 不限定具体类型
        
        character_templates = {
            "开放创作": {
                "focus": "完全基于用户需求和故事情感，创造独特而生动的角色",
                "elements": "核心特质、内在动机、外在表现、背景故事、与其他元素的关系、独特魅力"
            },
            "主角": {
                "focus": "作为故事中心，需要有明确动机、成长弧线和独特魅力",
                "elements": "核心动机、性格特点、背景经历、能力特长、成长空间、与其他角色的关系"
            },
            "配角": {
                "focus": "作为故事支撑，需要有独特功能和鲜明特点",
                "elements": "性格特色、功能作用、与主角关系、个人背景、行为习惯"
            },
            "反派": {
                "focus": "作为对立势力，需要有合理动机和威胁性",
                "elements": "对立动机、威胁能力、背景故事、与主角的冲突根源、行为方式"
            },
            "路人": {
                "focus": "作为环境元素，需要生动但不抢夺主角光芒",
                "elements": "基本特征、在场景中的作用、简单背景、行为特点"
            }
        }
        
        template = character_templates.get(character_type, character_templates["开放创作"])
        
        # 处理已有内容
        if existing_content.strip():
            context_instruction = f"""
**📖 已有故事内容（必须基于此设定创建角色）:**
{existing_content[-1000:]}...

**一致性要求:** 新角色必须与已有故事的世界观、时代背景、风格保持一致。
"""
        else:
            context_instruction = """
**📖 已有故事内容:** 无（独立创建角色）
"""
        
        # 处理故事背景
        if story_context.strip():
            background_info = f"**故事背景:** {story_context}"
        else:
            background_info = "**故事背景:** 根据用户要求推断合适背景"
        
        return f"""你是一位专业的角色设计师，请根据用户要求快速创建角色：

{context_instruction}

**用户要求:** {character_request}
**角色类型:** {character_type}
{background_info}

**创作重点:** {template['focus']}
**必须包含:** {template['elements']}

**快速创建指导:**
1. **核心设定** - 姓名、年龄、职业、核心特质
2. **外貌特征** - 一两个突出的外貌特点
3. **性格特点** - 2-3个主要性格特征
4. **背景简述** - 关键经历或背景信息
5. **故事作用** - 在故事中的功能和作用
6. **行为特色** - 标志性的行为或习惯

**创作要求:**
- 快速高效：重点突出，不要过于冗长
- 立体生动：有血有肉，避免脸谱化
- 功能明确：清楚在故事中的作用
- 融入自然：与已有内容和谐统一

**输出格式:**
## 👥 {character_type}角色档案

**基本信息:** [姓名、年龄、职业等]
**外貌特征:** [突出特点]
**性格特点:** [主要特质]
**背景故事:** [关键背景]
**故事作用:** [功能定位]
**行为特色:** [典型行为]

**角色亮点:** [最有趣/最重要的特点]
"""
    
    def _format_character_output(self, character_content: str, character_request: str) -> str:
        """格式化角色输出"""
        
        formatted_output = f"""👥 **角色构建完成**

**用户需求:** {character_request}
**构建时间:** {self._get_current_time()}

---

{character_content}

---

💡 **角色构建完成** 
新角色已创建完成，可在后续创作中使用。
"""
        return formatted_output
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
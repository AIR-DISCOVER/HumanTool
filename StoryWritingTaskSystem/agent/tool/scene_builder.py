"""
场景构建器 - 专门用于创建和描写场景
"""

class SceneBuilderTool:
    """场景构建器：快速创建各类场景和环境，支持agent主动调用"""
    
    def __init__(self, llm=None, verbose=False):
        self.llm = llm
        self.verbose = verbose
        
    def execute(self, scene_request: str, scene_type: str = "auto", 
                mood: str = "适中", existing_content: str = "", 
                task_description: str = "", **kwargs) -> str:
        """
        执行场景构建任务
        
        Args:
            scene_request: 用户对场景的具体要求
            scene_type: 场景类型 (auto/室内/室外/幻想/现实/动作)
            mood: 场景氛围 (紧张/温馨/神秘/欢快/恐怖/适中)
            existing_content: 已有的故事内容
            task_description: 任务描述（可选，兼容性参数）
        """
        
        # 🎯 兼容性处理：如果有task_description但没有scene_request，从task_description中提取要求
        if task_description and not scene_request:
            scene_request = task_description
        elif task_description and scene_request:
            # 如果两者都有，将task_description作为额外背景信息
            existing_content = f"{existing_content}. 任务要求：{task_description}"
        try:
            if self.verbose:
                print(f"🌍 开始构建场景: {scene_request[:50]}...")
            
            # 构建场景创建提示
            scene_prompt = self._build_scene_prompt(
                scene_request, scene_type, mood, existing_content
            )
            
            # 调用LLM生成场景
            if self.llm:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=scene_prompt)])
                scene_content = response.content
            else:
                scene_content = "场景构建工具暂时不可用，请稍后再试。"
            
            # 格式化输出
            formatted_result = self._format_scene_output(scene_content, scene_request, mood)
            
            if self.verbose:
                print(f"✅ 场景构建完成")
                
            return formatted_result
            
        except Exception as e:
            error_msg = f"场景构建过程中出现错误: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return error_msg
    
    def _build_scene_prompt(self, scene_request: str, scene_type: str, 
                           mood: str, existing_content: str) -> str:
        """构建场景创建提示词"""
        
        # 开放性场景创建，不预设类型限制
        if scene_type == "auto":
            scene_type = "开放创作"  # 不限定具体类型
        
        scene_templates = {
            "开放创作": {
                "focus": "完全基于用户需求和故事情感，创造独特而生动的场景",
                "elements": "空间感受、氛围营造、感官体验、情感共鸣、视觉呈现、独特细节"
            },
            "室内": {
                "focus": "营造封闭空间的氛围，注重细节和心理感受",
                "elements": "空间布局、光线效果、物品摆设、声音气味、人物位置关系"
            },
            "室外": {
                "focus": "展现开阔环境，强调天气、景色和空间感",
                "elements": "天气状况、地形地貌、远近景物、声音环境、移动路径"
            },
            "幻想": {
                "focus": "构建奇幻世界观，平衡现实感和想象力",
                "elements": "魔法元素、奇异生物、特殊规则、神秘氛围、视觉奇观"
            },
            "现实": {
                "focus": "贴近生活真实，注重代入感和可信度",
                "elements": "日常细节、真实环境、人群活动、社会背景、时代特色"
            },
            "动作": {
                "focus": "营造动态感和紧张感，强调节奏和视觉冲击",
                "elements": "动作节奏、空间利用、障碍设置、危险元素、视角切换"
            }
        }
        
        mood_guides = {
            "紧张": "使用短句，强调压迫感和不安要素",
            "温馨": "温暖色调，注重舒适和安全的感受",
            "神秘": "模糊描写，留白和暗示，营造未知感",
            "欢快": "明亮活泼，充满生机和正能量",
            "恐怖": "阴暗压抑，强调不详和威胁感",
            "适中": "平衡描写，不偏向特定情绪色彩"
        }
        
        template = scene_templates.get(scene_type, scene_templates["开放创作"])
        mood_guide = mood_guides.get(mood, "自然流畅的描写")
        
        # 处理已有内容
        if existing_content.strip():
            context_instruction = f"""
**📖 已有故事内容（场景必须与此保持一致）:**
{existing_content[-800:]}...

**一致性要求:** 新场景必须与已有故事的时空设定、世界观、角色状态保持连贯。
"""
        else:
            context_instruction = """
**📖 已有故事内容:** 无（独立创建场景）
"""
        
        return f"""你是一位专业的场景设计师，请根据用户要求快速创建场景：

{context_instruction}

**用户要求:** {scene_request}
**场景类型:** {scene_type}
**氛围要求:** {mood} - {mood_guide}

**创作重点:** {template['focus']}
**必须包含:** {template['elements']}

**快速创建指导:**
1. **环境设定** - 时间、地点、总体环境特征
2. **感官描写** - 视觉、听觉、嗅觉、触觉要素
3. **氛围营造** - 通过细节传达指定的情绪氛围
4. **空间层次** - 远景、中景、近景的层次描写
5. **动态元素** - 环境中的活动和变化
6. **象征意义** - 场景对故事情节的支撑作用

**创作要求:**
- 生动具体：使用具体的感官细节
- 氛围突出：符合指定的情绪基调
- 功能明确：为故事情节服务
- 画面感强：读者能够清晰想象

**输出格式:**
## 🌍 场景描写

**场景设定:** [时间地点等基本信息]
**环境特征:** [主要环境特点]
**氛围描写:** [详细的感官和情绪描写]
**空间布局:** [空间结构和重要位置]
**动态元素:** [环境中的活动和变化]

**场景亮点:** [最突出或最重要的特色]
"""
    
    def _format_scene_output(self, scene_content: str, scene_request: str, mood: str) -> str:
        """格式化场景输出"""
        
        formatted_output = f"""🌍 **场景构建完成**

**用户需求:** {scene_request}
**场景氛围:** {mood}
**构建时间:** {self._get_current_time()}

---

{scene_content}

---

💡 **场景构建完成** 
新场景已创建完成，可在故事中使用。
- 使用 character_builder 为场景添加合适的角色
- 使用 plot_developer 在此场景中发展情节
"""
        return formatted_output
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
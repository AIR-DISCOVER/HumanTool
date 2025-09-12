"""
情节推进器 - 专门用于发展和推进故事情节
"""

class PlotDeveloperTool:
    """情节推进器：快速发展故事情节，支持agent主动调用"""
    
    def __init__(self, llm=None, verbose=False):
        self.llm = llm
        self.verbose = verbose
        
    def execute(self, plot_request: str, development_type: str = "auto", 
                conflict_level: str = "适中", existing_content: str = "", 
                task_description: str = "", **kwargs) -> str:
        """
        执行情节发展任务
        
        Args:
            plot_request: 用户对情节发展的具体要求
            development_type: 发展类型 (auto/冲突升级/关系发展/谜题揭示/转折点/高潮)
            conflict_level: 冲突强度 (低/适中/高/极高)
            existing_content: 已有的故事内容
            task_description: 任务描述（可选，兼容性参数）
        """
        
        # 🎯 兼容性处理：如果有task_description但没有plot_request，从task_description中提取要求
        if task_description and not plot_request:
            plot_request = task_description
        elif task_description and plot_request:
            # 如果两者都有，将task_description作为额外背景信息
            existing_content = f"{existing_content}. 任务要求：{task_description}"
        try:
            if self.verbose:
                print(f"📈 开始发展情节: {plot_request[:50]}...")
            
            # 构建情节发展提示
            plot_prompt = self._build_plot_prompt(
                plot_request, development_type, conflict_level, existing_content
            )
            
            # 调用LLM生成情节
            if self.llm:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=plot_prompt)])
                plot_content = response.content
            else:
                plot_content = "情节推进工具暂时不可用，请稍后再试。"
            
            # 格式化输出
            formatted_result = self._format_plot_output(plot_content, plot_request, development_type)
            
            if self.verbose:
                print(f"✅ 情节发展完成")
                
            return formatted_result
            
        except Exception as e:
            error_msg = f"情节发展过程中出现错误: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return error_msg
    
    def _build_plot_prompt(self, plot_request: str, development_type: str, 
                          conflict_level: str, existing_content: str) -> str:
        """构建情节发展提示词"""
        
        # 智能判断发展类型
        if development_type == "auto":
            if any(word in plot_request.lower() for word in ["冲突", "对抗", "矛盾", "问题"]):
                development_type = "冲突升级"
            elif any(word in plot_request.lower() for word in ["关系", "情感", "友谊", "爱情"]):
                development_type = "关系发展"
            elif any(word in plot_request.lower() for word in ["秘密", "真相", "谜题", "发现"]):
                development_type = "谜题揭示"
            elif any(word in plot_request.lower() for word in ["转折", "意外", "变化", "突然"]):
                development_type = "转折点"
            elif any(word in plot_request.lower() for word in ["高潮", "决战", "最终", "结局"]):
                development_type = "高潮"
            else:
                development_type = "关系发展"  # 默认
        
        development_templates = {
            "冲突升级": {
                "focus": "加剧现有矛盾，增强戏剧张力",
                "techniques": ["引入新的对立因素", "暴露隐藏的矛盾", "提高风险和赌注", "制造时间压力"]
            },
            "关系发展": {
                "focus": "深化角色间的关系和情感",
                "techniques": ["展现角色内心", "创造互动机会", "测试关系界限", "揭示角色层面"]
            },
            "谜题揭示": {
                "focus": "逐步揭开秘密或真相",
                "techniques": ["提供关键线索", "制造认知冲击", "连接前面伏笔", "引出新的疑问"]
            },
            "转折点": {
                "focus": "改变故事发展方向",
                "techniques": ["意外事件发生", "角色做出关键选择", "揭示重要信息", "环境发生变化"]
            },
            "高潮": {
                "focus": "故事的最激烈和关键时刻",
                "techniques": ["集中所有冲突", "角色面临终极考验", "最大的情感冲击", "决定性的行动"]
            }
        }
        
        conflict_guides = {
            "低": "温和的分歧或小的障碍",
            "适中": "明显的对立和挑战",
            "高": "严重的冲突和危机",
            "极高": "生死攸关的终极对决"
        }
        
        template = development_templates.get(development_type, development_templates["关系发展"])
        conflict_guide = conflict_guides.get(conflict_level, "适度的紧张感")
        
        # 处理已有内容
        if existing_content.strip():
            context_instruction = f"""
**📖 当前故事状态（必须基于此发展情节）:**
{existing_content[-1000:]}...

**连贯性要求:** 情节发展必须与已有内容的角色状态、环境设定、故事节奏保持连贯。
"""
            # 简单分析当前情节状态
            current_analysis = self._analyze_current_plot(existing_content[-500:])
        else:
            context_instruction = """
**📖 当前故事状态:** 无（独立发展情节）
"""
            current_analysis = "全新情节开始"
        
        return f"""你是一位专业的故事情节设计师，请根据用户要求发展情节：

{context_instruction}

**用户要求:** {plot_request}
**发展类型:** {development_type}
**冲突强度:** {conflict_level} - {conflict_guide}

**发展重点:** {template['focus']}
**推荐技巧:** {', '.join(template['techniques'])}

**情节发展指导:**
1. **承接前文** - 自然延续当前故事状态
2. **设定目标** - 明确这段情节要达成什么
3. **制造动力** - 推动角色行动的原因
4. **增加变数** - 新的挑战或机会
5. **情感层次** - 角色的内心变化和反应
6. **为后续铺垫** - 为接下来的发展做准备

**发展原则:**
- 逻辑合理：情节发展要符合前文逻辑
- 节奏适当：与故事整体节奏协调
- 角色驱动：情节由角色的选择和行动推动
- 情感真实：注重角色的内心体验

**输出格式:**
## 📈 情节发展方案

**发展概述:** [这段情节的主要内容和目的]
**关键事件:** [推动情节的具体事件]
**角色动机:** [角色的行动原因和目标]
**冲突设置:** [主要的矛盾和障碍]
**情感变化:** [角色情感状态的变化]
**后续影响:** [对后续情节的影响]

**发展亮点:** [最精彩或最关键的部分]
"""
    
    def _analyze_current_plot(self, recent_content: str) -> str:
        """简单分析当前情节状态"""
        if "冲突" in recent_content or "对抗" in recent_content:
            return "当前处于冲突状态"
        elif "平静" in recent_content or "日常" in recent_content:
            return "当前处于平缓状态"
        elif "紧张" in recent_content or "危险" in recent_content:
            return "当前处于紧张状态"
        else:
            return "当前情节发展中"
    
    def _format_plot_output(self, plot_content: str, plot_request: str, development_type: str) -> str:
        """格式化情节输出"""
        
        formatted_output = f"""📈 **情节发展完成**

**用户需求:** {plot_request}
**发展类型:** {development_type}
**发展时间:** {self._get_current_time()}

---

{plot_content}

---

💡 **情节开发完成** 
情节发展方案已制定完成，可指导后续创作。
- 使用 character_builder 为情节发展添加新角色
- 使用 scene_builder 为情节发展设计合适场景
"""
        return formatted_output
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
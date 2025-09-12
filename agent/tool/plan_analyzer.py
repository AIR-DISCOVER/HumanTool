"""
规划分析器 - 专门用于分析故事规划质量
"""

class PlanAnalyzerTool:
    """规划分析器：专门分析故事规划的质量和可行性"""
    
    def __init__(self, llm=None, verbose=False):
        self.llm = llm
        self.verbose = verbose
        
    def execute(self, plan_content: str, analysis_focus: str = "全面分析", 
                analysis_depth: str = "标准", specific_concerns: str = "", 
                task_description: str = "", **kwargs) -> str:
        """
        执行规划分析任务
        
        Args:
            plan_content: 需要分析的规划内容
            analysis_focus: 分析重点 (全面分析/逻辑性/完整性/吸引力/可行性)
            analysis_depth: 分析深度 (简单/标准/深入/专业)
            specific_concerns: 特定关注点
        """
        try:
            if self.verbose:
                print(f"🔍 开始规划分析: {analysis_focus}")
            
            # 自动提取规划内容（如果为空）
            if not plan_content.strip() and "【已执行的工具和结果】" in str(kwargs.get('task_description', '')):
                plan_content = self._extract_plan_content(kwargs.get('task_description', ''))
                if plan_content and self.verbose:
                    print(f"🔄 自动提取到规划内容: {len(plan_content)}字符")
            
            # 构建分析提示
            analysis_prompt = self._build_analysis_prompt(
                plan_content, analysis_focus, analysis_depth, specific_concerns
            )
            
            # 调用LLM进行分析
            if self.llm:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
                analysis_content = response.content
            else:
                analysis_content = "规划分析工具暂时不可用，请稍后再试。"
            
            # 格式化输出
            formatted_result = self._format_analysis_output(analysis_content, analysis_focus, analysis_depth)
            
            if self.verbose:
                print(f"✅ 规划分析完成")
                
            return formatted_result
            
        except Exception as e:
            error_msg = f"规划分析过程中出现错误: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return error_msg
    
    def _extract_plan_content(self, task_description: str) -> str:
        """从任务描述中提取规划内容"""
        lines = task_description.split('\n')
        
        # 寻找故事规划器的结果
        in_tool_results = False
        plan_content = ""
        
        for line in lines:
            if "【已执行的工具和结果】" in line:
                in_tool_results = True
                continue
            elif in_tool_results and line.startswith("【"):
                break
            elif in_tool_results and "故事规划器" in line and ":" in line:
                plan_content = line.split(":", 1)[1].strip()
                break
        
        return plan_content
    
    def _build_analysis_prompt(self, plan_content: str, analysis_focus: str, 
                              analysis_depth: str, specific_concerns: str) -> str:
        """构建规划分析提示词"""
        
        focus_guides = {
            "全面分析": {
                "description": "对规划进行全方位质量评估",
                "criteria": ["逻辑性", "完整性", "吸引力", "可行性", "角色设定", "情节结构", "世界观构建"]
            },
            "逻辑性": {
                "description": "重点分析规划的逻辑合理性",
                "criteria": ["情节因果关系", "角色行为合理性", "时间线一致性", "世界观内在逻辑"]
            },
            "完整性": {
                "description": "检查规划是否包含所有必要元素",
                "criteria": ["角色设定完整性", "情节结构完整性", "世界观设定完整性", "主题表达清晰度"]
            },
            "吸引力": {
                "description": "评估规划的故事吸引力",
                "criteria": ["开头吸引力", "冲突设置", "悬念营造", "情感共鸣点", "独特性"]
            },
            "可行性": {
                "description": "分析规划的创作可行性",
                "criteria": ["创作难度", "篇幅合理性", "资源需求", "执行复杂度"]
            },
            "CPS评估": {
                "description": "基于CPS理论的三维度评估",
                "criteria": ["逻辑自洽性", "情感共鸣度", "新颖性", "批判性思考", "场景模拟"]
            }
        }
        
        depth_guides = {
            "简单": "提供基本的优缺点分析",
            "标准": "提供详细的分析和具体建议",
            "深入": "提供深度分析和改进方案",
            "专业": "提供专业级别的全面评估"
        }
        
        current_focus = focus_guides.get(analysis_focus, focus_guides["全面分析"])
        depth_requirement = depth_guides.get(analysis_depth, "标准分析")
        
        # 处理特定关注点
        if specific_concerns.strip():
            concern_instruction = f"""
**特定关注点:**
{specific_concerns}

**重点要求:** 请特别关注上述问题，在分析中给出针对性的评估和建议。
"""
        else:
            concern_instruction = ""
        
        return f"""你是一位专业的故事规划分析师，请对以下故事规划进行专业分析：

**需要分析的规划内容:**
{plan_content}

**分析重点:** {analysis_focus} - {current_focus['description']}
**分析深度:** {analysis_depth} - {depth_requirement}

{concern_instruction}

**分析维度:** {', '.join(current_focus['criteria'])}

**分析任务:**
1. **优势识别** - 规划中做得好的地方
2. **问题诊断** - 发现潜在的问题和不足
3. **改进建议** - 提供具体的优化建议
4. **风险评估** - 指出创作过程中可能遇到的挑战
5. **可行性评估** - 评估规划的实际可操作性

**分析标准:**
- **逻辑性**: 情节发展是否合理，角色行为是否符合设定
- **完整性**: 是否包含故事创作所需的所有基本元素
- **吸引力**: 故事是否有足够的吸引力和独特性
- **可行性**: 按照此规划创作是否具有可操作性

**输出格式:**
## 🔍 规划质量分析报告

### ✅ 优势分析
[列出规划的优点和亮点]

### ⚠️ 问题诊断
[指出存在的问题和不足]

### 💡 改进建议
[提供具体的优化建议]

### 🎯 风险评估
[指出可能的创作难点和风险]

### 📊 质量评分
- **逻辑性:** [评分]/10 - [说明]
- **完整性:** [评分]/10 - [说明]
- **吸引力:** [评分]/10 - [说明]
- **可行性:** [评分]/10 - [说明]

### 🚀 总体建议
[总结性建议和下一步行动方案]

**重要要求:**
- 基于提供的规划内容进行客观分析
- 给出建设性的改进意见
- 避免过于主观的判断
- 提供可操作的具体建议
"""
    
    def _format_analysis_output(self, analysis_content: str, analysis_focus: str, analysis_depth: str) -> str:
        """格式化分析输出"""
        
        formatted_output = f"""🔍 **规划质量分析完成**

**分析重点:** {analysis_focus}
**分析深度:** {analysis_depth}
**分析时间:** {self._get_current_time()}

---

{analysis_content}

---

📝 **规划分析完成** 
故事规划专业质量分析已完成。
"""
        return formatted_output
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
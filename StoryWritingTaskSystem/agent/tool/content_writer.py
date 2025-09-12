"""
内容写作器 - 负责基于规划生成具体的文本内容
"""

class ContentWriterTool:
    """内容写作器：基于规划生成具体的故事文本"""
    
    def __init__(self, llm=None, verbose=False):
        self.llm = llm
        self.verbose = verbose
        
    def execute(self, writing_task: str, story_plan: str = "", chapter_focus: str = "", 
                writing_style: str = "自然流畅", target_length: str = "1000-1500字", 
                previous_content: str = "", optimization_requirements: str = "",
                user_conversation_context: str = "", user_detailed_inputs: str = "",
                previous_tool_results: str = "", **kwargs) -> str:
        """
        执行内容写作任务
        
        Args:
            writing_task: 具体的写作任务描述
            story_plan: 故事规划内容（来自story_planner）
            chapter_focus: 本章节的重点内容
            writing_style: 写作风格 (自然流畅/悬疑紧张/浪漫温馨/幽默轻松)
            target_length: 目标字数
            previous_content: 已写的故事内容，用于保持连贯性
            optimization_requirements: 优化要求（来自story_refiner的回溯）
        """
        # 🎯 自动提取历史内容（如果 previous_content 为空）
        if not previous_content.strip():
            # 检查所有可能包含历史内容的地方
            content_sources = [
                writing_task,
                str(kwargs.get('task_description', '')),
                str(kwargs.get('context', '')),
                str(kwargs)  # 检查整个kwargs
            ]
            
            for source in content_sources:
                if any(indicator in source for indicator in [
                    "内容创作完成", "故事规划完成", "创作时间:", "实际字数:", "第一章", "第二章", "第三章"
                ]):
                    previous_content = self._extract_creative_content_from_history(source)
                    if previous_content and self.verbose:
                        print(f"🔄 自动提取到历史内容: {len(previous_content)}字符")
                    break
        
        # 检查是否是扩展请求
        is_expansion = any(keyword in writing_task for keyword in [
            "扩展", "加长", "更长", "增加", "延长", "补充内容", "丰富内容"
        ])
        
        # 检查是否是续写请求 - 更严格的检测，减少多章节生成
        is_continuation = any(keyword in writing_task.lower() for keyword in [
            "续写", "继续创作", "continue"
        ]) and previous_content.strip()  # 只有明确的续写请求且有历史内容才续写
        
        try:
            if self.verbose:
                print(f"✍️ 开始内容写作: {writing_task[:50]}...")
                print(f"🔍 历史内容长度: {len(previous_content)}字符")
                print(f"🔍 扩展请求: {is_expansion}")
                print(f"🔍 续写请求: {is_continuation}")
            
            # 🔍 调试：输出context_builder提供的所有内容
            print(f"🔍 [CONTENT_WRITER DEBUG] 接收到的参数:")
            print(f"  - writing_task: {writing_task}")
            print(f"  - story_plan: {story_plan}")
            print(f"  - chapter_focus: {chapter_focus}")
            print(f"  - writing_style: {writing_style}")
            print(f"  - target_length: {target_length}")
            print(f"  - previous_content长度: {len(previous_content)}")
            print(f"  - optimization_requirements: {optimization_requirements}")
            print(f"  - user_conversation_context长度: {len(user_conversation_context)}")
            print(f"  - user_detailed_inputs长度: {len(user_detailed_inputs)}")
            print(f"  - previous_tool_results长度: {len(previous_tool_results)}")
            print(f"  - kwargs keys: {list(kwargs.keys())}")
            
            # 输出task_description的完整内容（这是context_builder提供的）
            task_desc = kwargs.get('task_description', '')
            print(f"🔍 [CONTENT_WRITER DEBUG] task_description完整内容:")
            print(f"=== task_description开始 ===")
            print(task_desc)
            print(f"=== task_description结束 ===")
            print(f"task_description长度: {len(task_desc)}")
            
            # 构建写作提示 - 传入用户上下文
            writing_prompt = self._build_writing_prompt(
                writing_task, story_plan, chapter_focus, writing_style, target_length, previous_content, 
                optimization_requirements, user_conversation_context, user_detailed_inputs, previous_tool_results
            )
            
            # 调用LLM生成内容
            if self.llm:
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=writing_prompt)])
                story_content = response.content
            else:
                story_content = "内容写作工具暂时不可用，请稍后再试。"
            
            # 格式化输出
            formatted_result = self._format_writing_output(story_content, writing_style, target_length)
            
            if self.verbose:
                print(f"✅ 内容写作完成")
                
            return formatted_result
            
        except Exception as e:
            error_msg = f"内容写作过程中出现错误: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            return error_msg
    
    def _build_writing_prompt(self, writing_task: str, story_plan: str, 
                             chapter_focus: str, writing_style: str, target_length: str, 
                             previous_content: str, optimization_requirements: str = "",
                             user_conversation_context: str = "", user_detailed_inputs: str = "",
                             previous_tool_results: str = "") -> str:
        """构建内容写作提示词"""
        
        style_guide = {
            "自然流畅": "语言自然朴实，叙述流畅，注重情感的真实表达",
            "悬疑紧张": "营造紧张氛围，使用短句增强节奏感，留有悬念",
            "浪漫温馨": "语言优美温柔，重视情感细节和氛围渲染",
            "幽默轻松": "语言风趣幽默，情节轻松愉快，注重趣味性"
        }
        
        length_guide = {
            "500-800字": "简短精练的片段，重点突出单一场景或情节",
            "1000-1500字": "标准长度的章节，有完整的起承转合",
            "2000-3000字": "较长的章节，可以包含多个场景或情节点",
            "3000字以上": "长篇章节，适合复杂情节和深度描写"
        }
        
        # 重新定义变量，因为这些变量在这个方法中需要使用
        is_expansion = any(keyword in writing_task for keyword in [
            "扩展", "加长", "更长", "增加", "延长", "补充内容", "丰富内容"
        ])
        
        is_continuation = any(keyword in writing_task.lower() for keyword in [
            "继续", "下一章", "续写", "继续创作", "下一节", "下一个", "接下来", "continue", "next"
        ])
        
        # 根据是否有前面内容和任务类型决定写作方式
        if previous_content.strip():
            if is_expansion:
                context_instruction = f"""
**📖 原始内容（必须在此基础上扩展）:**
{previous_content}

**🎯 扩展任务模式:** 
- 这是内容扩展任务，不是重新创作
- 必须保留原有内容的所有情节和设定
- 在原内容基础上增加新的情节、对话、描写或细节
- 保持与原文完全一致的风格和角色性格
- 确保扩展后总体内容更加丰富和完整

**扩展策略:**
- 从原内容结尾自然延续故事发展
- 或者在现有情节中插入更多细节和描写
- 增加角色对话和心理活动
- 丰富场景描写和氛围营造
"""
                writing_mode = "扩展内容"
            elif is_continuation:
                context_instruction = f"""
**📖 已有故事内容（必须基于此内容续写）:**
{previous_content}

**📝 续写要求:**
- 必须从已有内容结尾自然延续故事
- 保持角色性格、情节逻辑、文风一致性
- 不要重复已有内容，要推进故事发展
- 继续完善故事情节

**重要提醒:** 这是故事续写，要保持连贯性！
"""
                writing_mode = "续写故事"
            else:
                context_instruction = f"""
**📖 已有故事内容（必须基于此内容续写）:**
{previous_content}

**重要提醒:** 你必须基于上述已有内容进行续写，保持角色性格、情节逻辑、文风一致性。不要重新开始或重复已有内容！
"""
                writing_mode = "续写故事"
        else:
            context_instruction = """
**📖 已有故事内容:** 无（这是故事的开始）
**📝 创作要求:** 请创作一个完整的故事
"""
            writing_mode = "创作完整故事"
        
        # 处理故事规划信息
        if story_plan.strip():
            # 提取规划中的关键信息
            plan_elements = self._extract_plan_elements(story_plan)
            plan_instruction = f"""
**📋 故事规划参考（必须严格遵循）:**
{story_plan}

**🎯 创作要求 - 必须使用规划内容:**
{plan_elements}

**严格要求:** 
- 必须使用规划中指定的角色名称和性格设定
- 必须体现规划中的章节主题和情节发展
- 必须使用规划中的关键场景和世界观设定
- 不得偏离规划的核心设定和角色关系
"""
        else:
            plan_instruction = """
**📋 故事规划参考:** 无（请根据写作任务自由创作）
"""
        
        # 根据写作模式设置特殊要求
        if writing_mode == "扩展内容":
            special_requirements = """
**🎯 扩展任务特殊要求:**

1. **内容扩展策略**
   - 保留原有内容的所有元素（角色、情节、设定）
   - 在原文基础上增加新的内容层次
   - 可以从结尾延续，也可以在中间插入细节
   - 确保扩展后的整体内容比原文更丰富

2. **扩展方式选择**
   - **续写扩展**: 从原文结尾继续发展情节
   - **细节扩展**: 丰富原有场景的描写和细节
   - **对话扩展**: 增加角色间的对话和互动
   - **心理扩展**: 深入角色的内心世界和思考

3. **质量保证**
   - 扩展内容必须与原文风格完全一致
   - 角色行为和性格保持连续性
   - 新增情节要符合原有逻辑
   - 确保扩展后字数明显增加

**输出要求:**
- 输出完整的扩展后内容（包含原文+新增部分）
- 新增部分要与原文无缝融合
- 确保总体内容更加丰富和完整
- 扩展后的字数要比原文明显增加"""
        elif writing_mode == "续写故事":
            special_requirements = """
**📝 续写特殊要求:**

**续写要求:**
- 从已有内容结尾自然延续故事
- 推进故事情节，不要重复已有内容
- 保持角色性格和世界观的一致性
- 继续发展故事情节，推向合理的结局

**输出要求:**
- 直接输出续写的故事内容
- 内容要与前文连贯自然
- 达到目标字数
- 保持一致的写作风格"""
        else:
            special_requirements = """
**输出要求:**
请直接输出完整的故事内容，要求：
- 创作一个有完整起承转合的故事
- 按照目标字数进行创作
- 保持指定的写作风格
- 内容要完整，有明确的开始、发展和结束
- 如果有规划，要体现规划中的关键元素
- 不要在正文中加入创作说明或元信息"""

        # 🚀 构建用户上下文部分 - 确保创作符合用户原始需求
        user_context_section = ""
        if user_conversation_context or user_detailed_inputs:
            user_context_section = f"""
🎯 **用户完整对话历史和详细要求（创作必须基于此内容）:**
{user_conversation_context if user_conversation_context else '无对话历史'}

📝 **用户具体故事描述:**
{user_detailed_inputs if user_detailed_inputs else '无详细描述'}

⚠️ **创作要求:** 必须严格基于用户的完整对话历史和详细描述进行创作，确保故事内容与用户的具体要求保持一致。用户的描述包含了故事的关键设定，这些都必须在创作中准确体现。
"""

        return f"""你是一位专业的故事作家，请根据以下要求{writing_mode}：

{user_context_section}
{context_instruction}
{plan_instruction}

**基本参数:**
- 写作任务: {writing_task}
- 章节重点: {chapter_focus if chapter_focus else '根据写作任务确定重点'}
- 写作风格: {writing_style} - {style_guide.get(writing_style, '自然流畅')}
- 目标字数: {target_length} - {length_guide.get(target_length, '适中长度')}

{self._build_optimization_section(optimization_requirements)}

**🚨 关键提醒：如果有故事规划，必须严格遵循！**
- 使用规划中指定的角色名称和性格设定
- 体现规划中的章节主题和情节发展
- 使用规划中设定的关键场景和世界观
- 遵循规划中的情节发展和角色关系

**📝 故事格式要求：**
- 如果是完整故事，确保有清晰的开头、发展、高潮和结尾
- 如果是续写，要与前文保持连贯性
- 内容要有逻辑性和情节发展

**核心写作要求:**

1. **内容连贯性**
   - 如果是续写，必须与前面内容无缝衔接
   - 保持角色性格和行为的一致性
   - 维持故事时间线和逻辑的连贯性

2. **情节发展**
   - 确保情节有明确的起承转合
   - 每个场景都要有明确的目的和推进作用
   - 设置适当的冲突和张力

3. **角色塑造**
   - 角色对话要符合其性格特点
   - 通过行动和心理描写展现角色特征
   - 确保角色行为有合理动机

4. **场景描写**
   - 环境描写要为情节和情感服务
   - 营造适当的氛围和情绪
   - 使用感官细节增强真实感

5. **语言表达**
   - 保持指定的写作风格
   - 语言要生动形象，避免平淡无奇
   - 注意句式变化和节奏感

**技术指导:**
- **对话写作**: 要自然真实，体现角色个性
- **心理描写**: 要深入细腻，展现内心世界
- **动作描写**: 要具体生动，推进情节发展
- **环境描写**: 要有选择性，突出氛围和情感

**质量标准:**
- 逻辑自洽：情节发展合理，角色行为可信
- 情感真实：能够引起读者的情感共鸣
- 语言优美：文字表达要有美感和感染力
- 结构完整：段落之间有清晰的逻辑关系

{special_requirements}

**重要提醒:**
- 专注于具体的故事内容创作
- 不要重复已有的故事内容
- 确保每个段落都有实质性的内容推进
- 如果涉及对话，要使用恰当的对话格式
"""
    
    def _format_writing_output(self, story_content: str, writing_style: str, target_length: str) -> str:
        """格式化写作输出"""
        
        # 简单统计字数（中文字符）
        char_count = len([c for c in story_content if '\u4e00' <= c <= '\u9fff'])
        
        formatted_output = f"""✍️ **内容创作完成**

{story_content}

---
📝 实际字数：约{char_count}字 | 风格：{writing_style}

**下一步建议:**
1. 如需扩展故事 → 使用content_writer的扩展功能丰富内容
2. 如需优化内容 → 使用story_refiner进行润色和改进
3. 如需调整情节 → 返回story_planner修改规划后重新创作
"""
        # 🎯 CSP工作流支持：返回字典而不是字符串
        return {
            "result": formatted_output,
            "writing_status": "completed",
            "workflow_status": "content_created_awaiting_discussion", 
            "completion_message": f"✅ CSP第5阶段（方案发展）完成，内容创作完毕",
            
            # 🎯 暂停等待用户确认
            "action_needed": "ask_human",
            "human_question": f"我已经基于规划完成了故事内容的创作（约{char_count}字）。你对这个内容满意吗？需要调整什么地方，还是可以进入最后的精炼阶段？",
            "next_stage_info": {
                "next_tool": "story_refiner",
                "next_params": {
                    "content_to_refine": story_content,
                    "refine_focus": "全面优化",
                    "quality_standard": "标准"
                }
            },
            "thought": f"内容创作完成，现在需要用户确认满意度后再进入story_refiner进行最后的精炼"
        }
    
    def _build_optimization_section(self, optimization_requirements: str) -> str:
        """构建优化要求部分"""
        if not optimization_requirements.strip():
            return ""
        
        return f"""
**🔧 优化要求（CSP回溯指导）:**
{optimization_requirements}

**🎯 重要指示 - 这是基于内容评估的回溯优化:**
- 保留原有内容的精华部分和成功元素
- 针对上述优化要求进行重点改进
- 确保改进后的内容在保持原有优点基础上质量更高
- 新内容应该体现出对之前问题的明确改进
"""
    
    def _extract_creative_content_from_history(self, task_description: str) -> str:
        """从任务描述中提取创意写作内容"""
        content_parts = []
        lines = task_description.split('\n')
        
        # 寻找故事内容 - 更灵活的匹配
        in_story_content = False
        current_content = ""
        found_start_marker = False
        
        for i, line in enumerate(lines):
            # 检查是否进入故事内容区域 - 多种标记
            if any(marker in line for marker in ["内容创作完成", "✍️", "📝"]):
                in_story_content = True
                current_content = ""
                found_start_marker = True
                continue
            
            # 如果在故事内容区域
            if in_story_content:
                # 遇到分隔线，开始收集故事正文
                if line.strip() == "---":
                    if current_content.strip():
                        # 如果已有内容，说明遇到了结束分隔线
                        content_parts.append(current_content.strip())
                        in_story_content = False
                        current_content = ""
                        continue
                    else:
                        # 如果没有内容，说明这是开始分隔线
                        continue
                
                # 检查是否遇到了新的工具结果或结束
                if any(end_marker in line for end_marker in [
                    "下一步建议", "创作说明", "如需继续创作", "🔧", "⚙️"
                ]):
                    if current_content.strip():
                        content_parts.append(current_content.strip())
                    in_story_content = False
                    current_content = ""
                    continue
                
                # 跳过元信息行
                if not any(skip in line for skip in [
                    "写作风格:", "目标字数:", "实际字数:", "创作时间:", 
                    "**写作风格**", "**目标字数**", "**实际字数**", "**创作时间**"
                ]):
                    if line.strip():
                        current_content += line.strip() + "\n"
        
        # 处理最后一个内容块
        if current_content.strip():
            content_parts.append(current_content.strip())
        
        # 返回所有故事内容，用于续写
        result = "\n\n".join(content_parts)
        
        # 如果没有提取到内容，尝试更宽松的匹配
        if not result.strip() and "第一章" in task_description:
            # 直接寻找章节标题后的内容
            for i, line in enumerate(lines):
                if "第一章" in line or "第二章" in line or "第三章" in line:
                    # 从这里开始收集内容
                    story_lines = []
                    for j in range(i, len(lines)):
                        if any(skip in lines[j] for skip in [
                            "创作说明", "下一步建议", "🔧", "⚙️", "---"
                        ]):
                            break
                        story_lines.append(lines[j])
                    if story_lines:
                        result = "\n".join(story_lines).strip()
                        break
        
        return result
    
    def _extract_plan_elements(self, story_plan: str) -> str:
        """从故事规划中提取关键信息 - 适配简化格式"""
        elements = []
        
        # 适配新的简化格式关键词
        if "主角" in story_plan:
            elements.append("**必须使用规划中的主角设定和性格特质**")
            
        # 检查故事结构
        if "故事结构" in story_plan or "开始" in story_plan or "发展" in story_plan:
            elements.append("**必须遵循规划中的故事结构和情节发展**")
            
        # 检查场景设定
        if "背景设定" in story_plan or "时空" in story_plan or "场景" in story_plan:
            elements.append("**必须使用规划中的背景设定和关键场景**")
            
        # 检查主题信息
        if "主题" in story_plan:
            elements.append("**必须体现规划中的核心主题**")
            
        # 检查冲突设定
        if "冲突" in story_plan:
            elements.append("**必须围绕规划中的核心冲突展开**")
        
        # 如果没有找到关键信息，添加通用要求
        if not elements:
            elements.append("**必须严格按照规划中的所有设定进行创作**")
            
        return "\n".join(elements)
    
    def _determine_chapter_number(self, previous_content: str) -> int:
        """根据已有内容判断当前应该是第几章"""
        if not previous_content.strip():
            return 1
        
        # 计算已有内容中的章节数 - 更准确的计数
        chapter_count = 0
        
        # 使用正则表达式查找章节标题
        import re
        chapter_patterns = [
            r'第[一二三四五六七八九十\d]+章',
            r'第\d+章',
            r'Chapter\s+\d+',
            r'CHAPTER\s+\d+'
        ]
        
        for pattern in chapter_patterns:
            matches = re.findall(pattern, previous_content, re.IGNORECASE)
            if matches:
                chapter_count = len(matches)
                break
        
        # 如果没有找到章节标题，根据创作完成的次数来判断
        if chapter_count == 0:
            # 计算"内容创作完成"的出现次数
            creation_count = previous_content.count("内容创作完成")
            if creation_count > 0:
                chapter_count = creation_count
            else:
                # 如果都没有找到，默认当前是第一章，下一章就是第二章
                chapter_count = 1
        
        # 返回下一章的编号
        next_chapter = chapter_count + 1
        
        # 调试信息
        if self.verbose:
            print(f"🔍 章节判断 - 已有章节数: {chapter_count}, 下一章: {next_chapter}")
        
        return next_chapter
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")
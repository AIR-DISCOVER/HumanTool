"""
协作助手方法 - 支持分步骤的human-agent协作
"""

class CollaborationHelpers:
    """协作助手类，提供分步协作的支持方法"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def detect_collaboration_step(self, state, messages) -> str:
        """检测当前协作进度"""
        try:
            # 检查消息历史中的协作标记
            for msg in reversed(messages[-8:]):  # 检查最近8条消息，支持更多阶段
                if hasattr(msg, 'content') and msg.content:
                    content = str(msg.content)
                    # 第1阶段：初始创意收集
                    if "创意想法" in content or "联想到什么画面" in content:
                        return "creative_input_done" if self._has_user_choice_after(messages, msg) else "start"
                    # 第2阶段：头脑风暴完成
                    elif "头脑风暴" in content or "创意扩展" in content or "material_collector" in content:
                        return "brainstorm_done" if self._has_user_choice_after(messages, msg) else "creative_input_done"
                    # 第3阶段：主题聚焦完成
                    elif "主题方向" in content or "聚焦" in content or "theme_focuser" in content:
                        return "theme_focused" if self._has_user_choice_after(messages, msg) else "brainstorm_done"
                    # 第4阶段：角色设定完成
                    elif "主角的背景和性格" in content or "核心要素" in content:
                        return "elements_defined" if self._has_user_choice_after(messages, msg) else "theme_focused"
                    # 第5阶段：策略确认完成
                    elif "创作重点应该放在" in content or "策略确认" in content:
                        return "ready_to_plan" if self._has_user_choice_after(messages, msg) else "elements_defined"
            
            return "start"
        except Exception as e:
            if self.logger:
                self.logger.warning(f"检测协作步骤失败: {e}")
            return "start"
    
    def _has_user_choice_after(self, messages, reference_msg) -> bool:
        """检查参考消息之后是否有用户选择"""
        try:
            ref_index = messages.index(reference_msg)
            for i in range(ref_index + 1, len(messages)):
                msg = messages[i]
                if hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__:
                    return True
            return False
        except:
            return False
    
    def generate_creative_direction_analysis(self, user_input: str) -> str:
        """生成创意方向分析问题"""
        # 根据用户输入分析可能的创作方向
        direction_templates = {
            "科幻": [
                "A) 探索人工智能与人类情感的冲突",
                "B) 聚焦未来科技对社会关系的影响", 
                "C) 描述科技发展中的伦理困境",
                "D) 展现人类在科技变革中的适应与成长"
            ],
            "悬疑": [
                "A) 心理悬疑：深入角色内心的推理过程",
                "B) 案件悬疑：层层揭开谜团的推进节奏",
                "C) 社会悬疑：通过案件反映社会问题",
                "D) 情感悬疑：在悬疑中探索人物关系"
            ],
            "爱情": [
                "A) 成长式爱情：在关系中的个人成长",
                "B) 冲突式爱情：价值观差异带来的情感碰撞",
                "C) 治愈式爱情：相互治愈的温暖故事",
                "D) 现实式爱情：面对生活挑战的情感选择"
            ]
        }
        
        # 简单关键词匹配确定类型
        story_type = "通用"
        for key, options in direction_templates.items():
            if key in user_input:
                story_type = key
                break
        
        if story_type in direction_templates:
            directions = direction_templates[story_type]
        else:
            directions = [
                "A) 角色驱动：以人物成长为核心线索",
                "B) 情节驱动：以事件发展为推进主线",
                "C) 主题驱动：以深度思辨为表达重点",
                "D) 情感驱动：以情感关系为叙述焦点"
            ]
        
        # 新的自然协作方式 - 不使用固定选项
        inspiration_questions = [
            f"我对'{user_input}'这个主题很感兴趣！能告诉我你心中浮现的第一个画面是什么吗？",
            f"'{user_input}'让我想到很多可能性。你最想通过这个故事表达什么？",
            f"关于'{user_input}'，你觉得什么样的角色最能承载这个主题？",
            f"我想了解你对'{user_input}'的独特理解，有什么特别打动你的元素吗？"
        ]
        
        import random
        return random.choice(inspiration_questions) + " ✨"
    
    def generate_core_elements_collaboration(self) -> str:
        """生成自然的角色协作问题"""
        character_questions = [
            "太棒了！现在让我们一起塑造这个故事的灵魂人物。你觉得什么样的主角最能打动读者？",
            "基于我们刚才的讨论，我想象中的主角开始有了轮廓。你心中的那个角色是什么样的？",
            "如果你遇到这样的主角，你会被他/她的什么特质所吸引？",
            "让我们来设计一个令人难忘的角色。你觉得这个故事需要什么样的主角？"
        ]
        
        story_questions = [
            "关于故事的核心，你希望读者读完后有什么感受？",
            "这个故事最应该触动人心的是什么？",
            "如果要用一个词概括这个故事的精神，你会选择什么？",
            "你觉得什么样的情节发展会让这个故事真正精彩？"
        ]
        
        import random
        char_q = random.choice(character_questions)
        story_q = random.choice(story_questions)
        
        return f"""{char_q}

{story_q}

告诉我你的想法，我想让这个故事真正体现你的创意！ ✨"""
    
    def generate_strategy_confirmation(self) -> str:
        """生成自然的偏好确认问题"""
        length_questions = [
            "关于故事的长度，你平时更喜欢什么样的？一口气读完的精简版，还是可以慢慢品味的详细版？",
            "你希望这是个怎样的阅读体验？快节奏的短篇，还是有充分发展空间的长篇？",
            "考虑到这个主题的丰富性，你觉得用多少篇幅来展现比较合适？"
        ]
        
        style_questions = [
            "关于叙述风格，你更喜欢什么感觉？自然流畅的日常感，还是紧张刺激的悬疑感？",
            "你希望读者在阅读时是什么心情？轻松愉快，还是专注投入？",
            "这个故事给你的第一感觉是什么样的氛围？我想为你定制最合适的风格。"
        ]
        
        import random
        length_q = random.choice(length_questions)
        style_q = random.choice(style_questions)
        
        return f"""很好！我们快要开始创作了。最后想了解一下你的偏好：

{length_q}

{style_q}

还有什么特别想要的元素吗？比如更多对话，或者更注重心理描写？告诉我你的想法！ 😊"""
    
    def extract_story_type(self, user_input: str) -> str:
        """从用户输入提取故事类型"""
        if any(keyword in user_input for keyword in ["科幻", "机器人", "AI", "未来", "太空", "科技"]):
            return "科幻"
        elif any(keyword in user_input for keyword in ["魔法", "奇幻", "超自然", "神话", "魔幻", "异世界"]):
            return "超自然"
        else:
            return "现实"
    
    def extract_user_choice(self, messages, choice_type: str) -> str:
        """从消息历史中提取用户选择"""
        try:
            choice_mappings = {
                "篇幅": {"A": "短篇", "B": "中等", "C": "长篇"},
                "重点": {"A": "全面规划", "B": "角色为主", "C": "情节为主", "D": "世界观为主"}
            }
            
            # 检查最近的用户消息
            for msg in reversed(messages[-5:]):
                if hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__:
                    content = str(msg.content).upper()
                    if choice_type in choice_mappings:
                        for key, value in choice_mappings[choice_type].items():
                            if key in content:
                                return value
            
            # 默认值
            return choice_mappings[choice_type]["A"] if choice_type in choice_mappings else "中等"
        except:
            return "中等"
    
    def build_collaborative_task_description(self, state, messages) -> str:
        """基于协作过程构建任务描述"""
        original_input = state.get("input_query", "")
        
        # 提取用户在协作过程中的选择
        user_choices = []
        for msg in messages:
            if hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__:
                content = str(msg.content)
                if len(content) < 100:  # 简短回复通常是选择
                    user_choices.append(content)
        
        # 构建包含用户专业选择的任务描述
        collaborative_description = f"""原始创作需求：{original_input}

基于用户专业协作的确定要素：
"""
        
        if user_choices:
            collaborative_description += f"用户专业选择：{' | '.join(user_choices[-3:])}"
        
        return collaborative_description
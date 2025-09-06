from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

class ItineraryPlannerTool:
    """高级旅游行程规划工具 - 整合信息提取和专业规划能力"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 初始化子工具
        self._init_sub_tools()
    
    def _init_sub_tools(self):
        """初始化子工具"""
        try:
            from .travel_info_extractor import TravelInfoExtractorTool
            from .travel_planner import TravelPlannerTool
            
            self.info_extractor = TravelInfoExtractorTool(self.llm, self.verbose)
            self.travel_planner = TravelPlannerTool(self.llm, self.verbose)
            
            if self.verbose:
                print("✅ [ItineraryPlannerTool] 子工具初始化成功")
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️ [ItineraryPlannerTool] 子工具初始化失败: {e}")
            self.info_extractor = None
            self.travel_planner = None
    
    def execute(self, task_description: str, destination: str = "", trip_duration: str = "", 
                planning_style: str = "balanced", budget_range: str = "", 
                use_reference_data: bool = True, planning_strategy: str = "direct",
                **kwargs) -> str:
        """
        执行综合旅游规划
        """
        if self.verbose:
            print(f"[ItineraryPlannerTool] 开始综合旅游规划")
            print(f"  目的地: {destination}")
            print(f"  时长: {trip_duration}")
            print(f"  策略: {planning_strategy}")
        
        # 🎯 修复：移除冗余的信息提取步骤，直接进行规划
        reference_data = None
        
        # 🎯 如果需要参考数据，直接从原始数据中获取，不调用info_extractor
        if use_reference_data and self.info_extractor:
            try:
                # 直接获取原始数据，不进行LLM分析
                raw_data = self.info_extractor._load_local_data()
                if raw_data and destination:
                    # 筛选相关数据
                    relevant_data = []
                    for item in raw_data:
                        query = item.get('query', '').lower()
                        if destination.lower() in query:
                            relevant_data.append(item)
                    
                    if relevant_data:
                        # 只传递原始数据，不进行分析
                        reference_data = {"reference_information": relevant_data[:3]}
                        if self.verbose:
                            print(f"[ItineraryPlannerTool] 找到 {len(relevant_data)} 条相关参考数据")
                
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 获取参考数据失败: {e}")
        
        # 🎯 直接执行专业旅游规划，不添加额外的分析内容
        if self.travel_planner:
            try:
                # 构建增强的任务描述
                enhanced_description = self._enhance_task_description(
                    task_description, destination, trip_duration, budget_range, planning_style
                )
                
                # 在任务描述中强调中文输出
                enhanced_description = f"请用中文回答。{enhanced_description}\n\n特别要求：所有输出内容都必须是中文，包括说明、描述和分析。"
                
                planning_result = self.travel_planner.execute(
                    task_description=enhanced_description,
                    strategy=planning_strategy,
                    reference_data=reference_data,
                    **kwargs
                )
                
                # 🎯 修复：直接返回规划结果，不添加额外内容
                return planning_result
                
            except Exception as e:
                if self.verbose:
                    print(f"⚠️ 专业规划失败: {e}")
                # 回退到基础LLM规划
                return self._basic_planning(task_description, destination, 
                                          trip_duration, planning_style, budget_range, **kwargs)
        else:
            # 使用基础规划
            return self._basic_planning(task_description, destination, 
                                      trip_duration, planning_style, budget_range, **kwargs)

    def _enhance_task_description(self, task_description: str, destination: str, 
                                trip_duration: str, budget_range: str, planning_style: str) -> str:
        """增强任务描述"""
        enhanced = task_description
        
        if destination and destination not in enhanced:
            enhanced += f"\n目的地：{destination}"
        if trip_duration and trip_duration not in enhanced:
            enhanced += f"\n旅行时长：{trip_duration}"
        if budget_range and budget_range not in enhanced:
            enhanced += f"\n预算范围：{budget_range}"
        if planning_style and planning_style != "balanced":
            style_desc = {
                'relaxed': '悠闲型 - 节奏缓慢，留有充分休息时间',
                'packed': '紧凑型 - 行程丰富，充分利用每一天',
                'flexible': '灵活型 - 保留弹性空间，可随时调整'
            }.get(planning_style, planning_style)
            enhanced += f"\n规划风格：{style_desc}"
        
        return enhanced
    
    def _basic_planning(self, task_description: str, destination: str = "", 
                       trip_duration: str = "", planning_style: str = "balanced", 
                       budget_range: str = "", **kwargs) -> str:
        """基础LLM规划（备用方案）"""
        system_prompt = """你是一个专业的旅游行程规划师，具有丰富的全球旅游经验和规划能力。

规划要求：
- 按天数安排具体行程，包含时间、地点、交通、用餐、住宿
- 提供准确预算

请使用以下格式输出详细的行程规划：

## 📅 逐日详细行程
对每一天提供：
- **景点/活动详情** (包括门票价格)，景点一定要在当地！
- **交通方式** (用时，费用，必须包含出发地和目的地)；格式：交通方式，出发地和目的地。
- **用餐建议** (推荐餐厅,一定包含早餐（一定要有指定具体地点）、午餐、晚餐！)；格式：餐厅，所在城市。
- **住宿信息** (位置、价格范围)，**一定要注意最**小入住天数**和最少入住人数,可以按照住宿的最小天数调整旅行的城市安排**。一定要在当天所在城市住宿！

最后，给出整体的预算：
- **整体预算** (**分项估算，给出公式**)

**中文输出，地名、酒店名、餐厅名等注释英文。**，确保所有地点、景点、住宿、早中午餐内容都在reference_data中有对应的内容。


无需输出规划以外的任何内容。输出排版紧凑。

---

参考格式：

第X天：
**当前城市：**从出发城市到目的地城市
**交通方式：**交通工具，从出发地到目的地，距离数字公里，耗时X小时X分钟，费用X美元
**早餐：**餐厅名称（餐厅类型），城市名
**景点：**景点名称（景点中文名），城市名
**午餐：**餐厅名称（餐厅类型），城市名
**晚餐：**餐厅名称（餐厅类型），城市名
**住宿：**住宿名称（住宿描述），城市名

第X天：
**当前城市：**城市名
交通方式：-
**早餐：**餐厅名称（餐厅类型），城市名
**景点：**景点名称（景点中文名），城市名；景点名称（景点中文名），城市名
**午餐：**餐厅名称（餐厅类型），城市名
**晚餐：**餐厅名称（餐厅类型），城市名
**住宿：**住宿名称（住宿描述），城市名

第X天：
**当前城市：**从出发城市到目的地城市
**交通方式：**交通工具，距离X公里，从出发地到目的地，耗时X小时X分钟，费用X美元
**早餐：**餐厅名称（餐厅类型），城市名
**景点：**景点名称（景点中文名），城市名
**午餐：**餐厅名称（餐厅类型），城市名
**晚餐：**餐厅名称（餐厅类型），城市名

"""

        # 构建用户提示词
        user_prompt = f"""请为我制定旅游行程规划：

需求描述：{task_description}

"""
        
        # 添加具体参数
        if destination:
            user_prompt += f"目的地：{destination}\n"
        if trip_duration:
            user_prompt += f"旅行时长：{trip_duration}\n"
        if budget_range:
            user_prompt += f"预算范围：{budget_range}\n"
        if planning_style:
            style_desc = {
                'relaxed': '悠闲型 - 节奏缓慢，留有充分休息时间',
                'packed': '紧凑型 - 行程丰富，充分利用每一天',
                'balanced': '平衡型 - 在观光和休闲之间找到平衡',
                'flexible': '灵活型 - 保留弹性空间，可随时调整'
            }.get(planning_style, planning_style)
            user_prompt += f"规划风格：{style_desc}\n"
        
        # 添加其他可选参数
        if 'travel_preferences' in kwargs:
            user_prompt += f"旅行偏好：{kwargs['travel_preferences']}\n"
        if 'accommodation_type' in kwargs:
            user_prompt += f"住宿偏好：{kwargs['accommodation_type']}\n"
        if 'transport_mode' in kwargs:
            user_prompt += f"交通方式：{kwargs['transport_mode']}\n"
        
        user_prompt += "\n请提供详细的逐日行程安排，包含时间、地点、交通、用餐和预算信息。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return f"## 🗺️ 旅游行程规划\n\n{response.content}"
        except Exception as e:
            return f"❌ 基础规划失败: {str(e)}"
    
    def _contains_too_much_english(self, text: str) -> bool:
        """检查文本是否包含过多英文"""
        if not text:
            return False
        
        # 计算英文字符比例
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars == 0:
            return False
        
        english_ratio = english_chars / total_chars
        return english_ratio > 0.6  # 如果英文字符超过60%，认为需要处理
    
    def _ensure_chinese_output(self, text: str) -> str:
        """确保输出为中文"""
        try:
            system_prompt = """你是一个专业的旅游文档中文化专家。请将提供的旅游规划内容完全转换为中文表达，要求：

1. 所有说明和描述都用中文
2. 地名保留英文，但添加中文翻译，格式：English Name (中文名)
3. 时间格式改为中文习惯：Day 1 → 第1天，Morning → 上午，Evening → 晚上
4. 货币保留符号但用中文描述：$100 → 约100美元
5. 保持原有的Markdown格式结构
6. 保持所有具体信息的准确性
7. 使用自然流畅的中文表达

请将以下内容完全中文化："""

            user_prompt = text

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            if self.verbose:
                print(f"中文化处理失败: {e}")
            return text  # 处理失败时返回原文


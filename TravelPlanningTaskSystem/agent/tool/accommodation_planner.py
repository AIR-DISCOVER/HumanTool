import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel


class AccommodationPlannerTool:
    """专门用于住宿规划的工具，使用本地数据结合LLM规划"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 🎯 使用数据管理器进行懒加载
        from agent.tool.data_manager import get_data_manager
        self.data_manager = get_data_manager()
        self.data_manager.set_verbose(verbose)
        
        if self.verbose:
            print(f"[AccommodationPlanner] 使用数据管理器进行懒加载")
    
    def _get_accommodations_data(self) -> Optional[pd.DataFrame]:
        """获取住宿数据 - 使用数据管理器懒加载"""
        return self.data_manager.get_data('accommodations')
    
    def get_accommodations_by_city(self, city: str) -> List[Dict]:
        """根据城市获取住宿信息"""
        accommodations_data = self._get_accommodations_data()
        if accommodations_data is None:
            return []
        
        try:
            # 搜索指定城市的住宿
            city_data = accommodations_data[accommodations_data['city'] == city]
            
            if len(city_data) == 0:
                # 尝试模糊匹配
                city_data = accommodations_data[accommodations_data['city'].str.contains(city, case=False, na=False)]
            
            # 转换为字典列表
            accommodations = []
            for _, row in city_data.iterrows():
                accommodation = {
                    'name': row['NAME'],
                    'price': row['price'],
                    'room_type': row['room type'],
                    'house_rules': row['house_rules'],
                    'minimum_nights': row['minimum nights'],
                    'maximum_occupancy': row['maximum occupancy'],
                    'review_rate': row['review rate number'],
                    'city': row['city']
                }
                accommodations.append(accommodation)
            
            if self.verbose:
                print(f"[AccommodationPlanner] 找到 {len(accommodations)} 个住宿选项在 {city}")
                print(f"[AccommodationPlanner] 住宿: {accommodations}")
            
            return accommodations[:20]  # 限制返回数量
            
        except Exception as e:
            if self.verbose:
                print(f"[AccommodationPlanner] 搜索住宿数据失败: {e}")
            return []
    
    def execute(self, task_description: str, cities: Optional[List[str]] = None, 
                budget_range: Optional[str] = None, occupancy: Optional[int] = None,
                nights: Optional[int] = None, **kwargs) -> str:
        """
        执行住宿规划任务
        
        Args:
            task_description: 任务描述
            cities: 目标城市列表
            budget_range: 预算范围
            occupancy: 入住人数
            nights: 住宿天数
        """
        if self.verbose:
            print(f"[AccommodationPlanner] 开始住宿规划")
        
        try:
            # 从任务描述中提取城市信息（如果未提供）
            if not cities:
                cities = self._extract_cities_from_description(task_description)
            
            # 收集所有相关住宿数据
            all_accommodations = []
            for city in cities:
                city_accommodations = self.get_accommodations_by_city(city)
                all_accommodations.extend(city_accommodations)
            
            # 使用LLM进行住宿规划
            return self._plan_accommodations_with_llm(
                task_description, all_accommodations, budget_range, 
                occupancy, nights, **kwargs
            )
            
        except Exception as e:
            error_msg = f"❌ 住宿规划过程中出现错误: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _extract_cities_from_description(self, description: str) -> List[str]:
        """从描述中提取城市名称"""
        # 简单的城市提取逻辑
        import re
        
        # 常见的城市名称模式
        city_patterns = [
            r'到\s*([A-Za-z\s]+)',
            r'去\s*([A-Za-z\s]+)',
            r'在\s*([A-Za-z\s]+)',
            r'visit\s+([A-Z][a-zA-Z\s]+)',
            r'to\s+([A-Z][a-zA-Z\s]+)',
            r'in\s+([A-Z][a-zA-Z\s]+)'
        ]
        
        cities = set()
        for pattern in city_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                city = match.strip()
                if len(city) > 2:  # 过滤太短的匹配
                    cities.add(city)
        
        # 如果没有找到城市，返回一些默认城市进行搜索
        if not cities:
            cities = ['Newark, Santa Maria']
        
        return list(cities)[:5]  # 限制城市数量
    
    def _plan_accommodations_with_llm(self, task_description: str, accommodations_data: List[Dict],
                                    budget_range: Optional[str], occupancy: Optional[int],
                                    nights: Optional[int], **kwargs) -> str:
        """使用LLM进行住宿规划"""
        
        system_prompt = """你是一个专业的住宿规划师，专门为旅行者推荐和规划住宿安排。

请使用以下格式输出住宿规划：

## 🏨 住宿规划推荐

### 推荐住宿列表
对每个推荐的住宿提供：
- **住宿名称** (中文翻译)
- **房型和价格** (每晚价格，总价计算)
- **入住要求** (最少天数、最大人数、房屋规则)(no parties不代表禁止访客no visitor)


**中文输出，住宿名称保留英文并注释中文翻译。**
请确保所有推荐都基于提供的住宿数据。如果没有则告知没有该条件的住宿数据。

无需输出规划以外的任何内容。输出排版紧凑。
"""

        # 准备住宿数据摘要 - 按城市分组显示
        accommodations_summary = ""
        if accommodations_data:
            # 按城市分组住宿数据
            cities_data = {}
            for acc in accommodations_data:
                city = acc['city']
                if city not in cities_data:
                    cities_data[city] = []
                cities_data[city].append(acc)
            
            accommodations_summary = "可用住宿数据（按城市分组）：\n\n"
            for city, city_accommodations in cities_data.items():
                accommodations_summary += f"**{city}城市住宿**:\n"
                # 每个城市最多显示8个住宿，确保数据平衡
                for i, acc in enumerate(city_accommodations[:20], 1):
                    accommodations_summary += f"{i}. {acc['name']}\n"
                    accommodations_summary += f"   价格: ${acc['price']}/晚, 房型: {acc['room_type']}\n"
                    accommodations_summary += f"   最少住宿: {acc['minimum_nights']}晚, 最大入住: {acc['maximum_occupancy']}人\n"
                    accommodations_summary += f"   评分: {acc['review_rate']}, 规则: {acc['house_rules']}\n\n"
                accommodations_summary += "\n"
        else:
            accommodations_summary = "未找到相关住宿数据，将提供通用住宿建议。"

        user_prompt = f"""请为我制定详细的住宿规划：

**规划需求**: {task_description}(no parties不代表禁止访客no visitor)

**约束条件**:
- 预算范围: {budget_range or '未指定'}
- 入住人数: {occupancy or '未指定'}
- 住宿天数: {nights or '未指定'}

**可用住宿数据**:
{accommodations_summary}

请基于以上信息提供详细的住宿规划和推荐。
"""

        # 添加其他参数
        for key, value in kwargs.items():
            if value:
                user_prompt += f"**{key}**: {value}\n"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"❌ 住宿规划LLM调用失败: {str(e)}"

    def validate_query(self, query: str) -> tuple[bool, str]:
        """验证查询的有效性"""
        if not query or len(query.strip()) < 5:
            return False, "查询内容太短，请提供更详细的住宿需求"
        
        # 检查是否包含住宿相关关键词
        accommodation_keywords = ['住宿', '酒店', '民宿', '旅馆', '宾馆', 'hotel', 'accommodation', 'stay', 'lodge']
        if not any(keyword in query.lower() for keyword in accommodation_keywords):
            return False, "查询内容似乎与住宿规划无关，请提供住宿相关的需求"
        
        return True, "查询有效"
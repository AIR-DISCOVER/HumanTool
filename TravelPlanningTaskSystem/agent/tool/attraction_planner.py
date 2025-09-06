import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel


class AttractionPlannerTool:
    """专门用于景点规划的工具，使用本地数据结合LLM规划"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 设置路径 - 基于TATA项目结构
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # TravelPlanner数据路径
        self.travelplanner_root = os.path.join(project_root, 'agent', 'TravelPlanner')
        self.attractions_path = os.path.join(self.travelplanner_root, 'database', 'attractions', 'attractions.csv')
        
        if self.verbose:
            print(f"[AttractionPlanner] 数据文件路径: {self.attractions_path}")
            print(f"[AttractionPlanner] 数据文件存在: {os.path.exists(self.attractions_path)}")
        
        # 加载景点数据
        self.attractions_data = self._load_attractions_data()
    
    def _load_attractions_data(self) -> Optional[pd.DataFrame]:
        """加载景点数据"""
        try:
            if not os.path.exists(self.attractions_path):
                if self.verbose:
                    print("[AttractionPlanner] 景点数据文件未找到")
                return None
            
            # 加载数据，保留关键字段
            data = pd.read_csv(self.attractions_path).dropna()
            data = data[['Name', 'Latitude', 'Longitude', 'Address', 'Phone', 'Website', 'City']]
            
            if self.verbose:
                print(f"[AttractionPlanner] 成功加载 {len(data)} 条景点数据")
                print(f"[AttractionPlanner] 涵盖城市: {data['City'].unique()[:10]}...")
            
            return data
            
        except Exception as e:
            if self.verbose:
                print(f"[AttractionPlanner] 加载景点数据失败: {e}")
            return None
    
    def get_attractions_by_city(self, city: str) -> List[Dict]:
        """根据城市获取景点信息"""
        if self.attractions_data is None:
            return []
        
        try:
            # 搜索指定城市的景点
            city_data = self.attractions_data[self.attractions_data['City'] == city]
            
            if len(city_data) == 0:
                # 尝试模糊匹配
                city_data = self.attractions_data[self.attractions_data['City'].str.contains(city, case=False, na=False)]
            
            # 转换为字典列表
            attractions = []
            for _, row in city_data.iterrows():
                attraction = {
                    'name': row['Name'],
                    'latitude': row['Latitude'],
                    'longitude': row['Longitude'],
                    'address': row['Address'],
                    'phone': row['Phone'] if pd.notna(row['Phone']) else '',
                    'website': row['Website'] if pd.notna(row['Website']) else '',
                    'city': row['City']
                }
                attractions.append(attraction)
            
            if self.verbose:
                print(f"[AttractionPlanner] 找到 {len(attractions)} 个景点在 {city}")
            
            return attractions[:30]  # 限制返回数量
            
        except Exception as e:
            if self.verbose:
                print(f"[AttractionPlanner] 搜索景点数据失败: {e}")
            return []
    
    def execute(self, task_description: str, cities: Optional[List[str]] = None, 
                interests: Optional[List[str]] = None, duration: Optional[str] = None,
                travel_style: Optional[str] = None, **kwargs) -> str:
        """
        执行景点规划任务
        
        Args:
            task_description: 任务描述
            cities: 目标城市列表
            interests: 兴趣类型列表（如：历史、艺术、自然等）
            duration: 游览时长
            travel_style: 旅行风格（如：深度游、打卡游等）
        """
        if self.verbose:
            print(f"[AttractionPlanner] 开始景点规划")
        
        try:
            # 从任务描述中提取城市信息（如果未提供）
            if not cities:
                cities = self._extract_cities_from_description(task_description)
            
            # 收集所有相关景点数据
            all_attractions = []
            for city in cities:
                city_attractions = self.get_attractions_by_city(city)
                all_attractions.extend(city_attractions)
            
            # 使用LLM进行景点规划
            return self._plan_attractions_with_llm(
                task_description, all_attractions, interests, 
                duration, travel_style, **kwargs
            )
            
        except Exception as e:
            error_msg = f"❌ 景点规划过程中出现错误: {str(e)}"
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
            cities = ['Santa Maria', 'Newark']
        
        return list(cities)[:5]  # 限制城市数量
    
    def _plan_attractions_with_llm(self, task_description: str, attractions_data: List[Dict],
                                 interests: Optional[List[str]], duration: Optional[str],
                                 travel_style: Optional[str], **kwargs) -> str:
        """使用LLM进行景点规划"""
        
        system_prompt = """你是一个专业的景点规划师，专门为旅行者推荐和规划景点游览路线。


请使用以下格式输出景点规划：

## 🎯 景点游览规划

### 推荐景点列表
对每个推荐的景点提供：
- **景点名称** (中文翻译)
- **景点特色** (主要看点和特色介绍)
- **地理位置** 
- **联系信息** (电话、网站等)
- **门票价格**

**中文输出，景点名称保留英文并注释中文翻译。**
请确保所有推荐都基于提供的景点数据。如果没有则告知没有该条件的景点数据。

无需输出以外的任何内容。输出排版紧凑。
"""

        # 准备景点数据摘要 - 按城市分组显示
        attractions_summary = ""
        if attractions_data:
            # 按城市分组景点数据
            cities_data = {}
            for attr in attractions_data:
                city = attr['city']
                if city not in cities_data:
                    cities_data[city] = []
                cities_data[city].append(attr)
            
            attractions_summary = "可用景点数据（按城市分组）：\n\n"
            for city, city_attractions in cities_data.items():
                attractions_summary += f"**{city}城市景点**:\n"
                # 每个城市最多显示10个景点，确保数据平衡
                for i, attr in enumerate(city_attractions[:10], 1):
                    attractions_summary += f"{i}. {attr['name']}\n"
                    attractions_summary += f"   地址: {attr['address']}\n"
                    if attr['phone']:
                        attractions_summary += f"   电话: {attr['phone']}\n"
                    if attr['website']:
                        attractions_summary += f"   网站: {attr['website']}\n"
                    attractions_summary += f"   坐标: ({attr['latitude']}, {attr['longitude']})\n\n"
                attractions_summary += "\n"
        else:
            attractions_summary = "未找到相关景点数据，将提供通用景点建议。"

        user_prompt = f"""请为我制定景点游览规划：

**规划需求**: {task_description}

**偏好设置**:
- 兴趣类型: {', '.join(interests) if interests else '未指定'}
- 游览时长: {duration or '未指定'}
- 旅行风格: {travel_style or '未指定'}

**可用景点数据**:
{attractions_summary}

请基于以上信息提供详细的景点游览规划。
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
            return f"❌ 景点规划LLM调用失败: {str(e)}"

    def validate_query(self, query: str) -> tuple[bool, str]:
        """验证查询的有效性"""
        if not query or len(query.strip()) < 5:
            return False, "查询内容太短，请提供更详细的景点游览需求"
        
        # 检查是否包含景点相关关键词
        attraction_keywords = ['景点', '游览', '参观', '旅游', '观光', 'attraction', 'sightseeing', 'visit', 'tour']
        if not any(keyword in query.lower() for keyword in attraction_keywords):
            return False, "查询内容似乎与景点规划无关，请提供景点游览相关的需求"
        
        return True, "查询有效"
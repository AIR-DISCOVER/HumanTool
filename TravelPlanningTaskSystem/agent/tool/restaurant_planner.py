import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel


class RestaurantPlannerTool:
    """专门用于餐饮规划的工具，使用本地数据结合LLM规划"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 设置路径 - 基于TATA项目结构
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # TravelPlanner数据路径
        self.travelplanner_root = os.path.join(project_root, 'agent', 'TravelPlanner')
        self.restaurants_path = os.path.join(self.travelplanner_root, 'database', 'restaurants', 'clean_restaurant_2022.csv')
        
        if self.verbose:
            print(f"[RestaurantPlanner] 数据文件路径: {self.restaurants_path}")
            print(f"[RestaurantPlanner] 数据文件存在: {os.path.exists(self.restaurants_path)}")
        
        # 加载餐厅数据
        self.restaurants_data = self._load_restaurants_data()
    
    def _load_restaurants_data(self) -> Optional[pd.DataFrame]:
        """加载餐厅数据"""
        try:
            if not os.path.exists(self.restaurants_path):
                if self.verbose:
                    print("[RestaurantPlanner] 餐厅数据文件未找到")
                return None
            
            # 加载数据，保留关键字段
            data = pd.read_csv(self.restaurants_path).dropna()
            data = data[['Name', 'Average Cost', 'Cuisines', 'Aggregate Rating', 'City']]
            
            if self.verbose:
                print(f"[RestaurantPlanner] 成功加载 {len(data)} 条餐厅数据")
                print(f"[RestaurantPlanner] 涵盖城市: {data['City'].unique()[:10]}...")
                print(f"[RestaurantPlanner] 菜系类型: {data['Cuisines'].unique()[:10]}...")
            
            return data
            
        except Exception as e:
            if self.verbose:
                print(f"[RestaurantPlanner] 加载餐厅数据失败: {e}")
            return None
    
    def get_restaurants_by_city(self, city: str, cuisine_type: Optional[str] = None, 
                               min_rating: Optional[float] = None, max_cost: Optional[float] = None) -> List[Dict]:
       """根据城市和筛选条件获取餐厅信息"""
       if self.restaurants_data is None:
           return []
       
       try:
           # 搜索指定城市的餐厅
           initial_city_data = self.restaurants_data[self.restaurants_data['City'] == city]
           if self.verbose:
               print(f"[RestaurantPlanner] 城市 '{city}' 精确匹配找到 {len(initial_city_data)} 家餐厅")

           city_data = initial_city_data
           if len(city_data) == 0:
               # 尝试模糊匹配
               city_data = self.restaurants_data[self.restaurants_data['City'].str.contains(city, case=False, na=False)]
               if self.verbose:
                   print(f"[RestaurantPlanner] 城市 '{city}' 模糊匹配找到 {len(city_data)} 家餐厅")

           # 应用筛选条件
           if cuisine_type:
               before_cuisine_filter_count = len(city_data)
               city_data = city_data[city_data['Cuisines'].str.contains(cuisine_type, case=False, na=False)]
               if self.verbose:
                   print(f"[RestaurantPlanner] 应用菜系 '{cuisine_type}' 筛选后，剩下 {len(city_data)} 家餐厅 (之前: {before_cuisine_filter_count})")

           if min_rating:
               before_rating_filter_count = len(city_data)
               city_data = city_data[city_data['Aggregate Rating'] >= min_rating]
               if self.verbose:
                   print(f"[RestaurantPlanner] 应用评分 '>={min_rating}' 筛选后，剩下 {len(city_data)} 家餐厅 (之前: {before_rating_filter_count})")

           if max_cost:
               before_cost_filter_count = len(city_data)
               city_data = city_data[city_data['Average Cost'] <= max_cost]
               if self.verbose:
                   print(f"[RestaurantPlanner] 应用成本 '<={max_cost}' 筛选后，剩下 {len(city_data)} 家餐厅 (之前: {before_cost_filter_count})")

           # 按评分排序
           city_data = city_data.sort_values('Aggregate Rating', ascending=False)
           
           # 转换为字典列表
           restaurants = []
           for _, row in city_data.iterrows():
               restaurant = {
                   'name': row['Name'],
                   'average_cost': row['Average Cost'],
                   'cuisines': row['Cuisines'],
                   'rating': row['Aggregate Rating'],
                   'city': row['City']
               }
               restaurants.append(restaurant)

           if self.verbose:
               print(f"[RestaurantPlanner] 找到 {len(restaurants)} 家餐厅在 {city}")

           return restaurants[:25]  # 限制返回数量

       except Exception as e:
           if self.verbose:
               print(f"[RestaurantPlanner] 搜索餐厅数据失败: {e}")
           return []
    
    def execute(self, task_description: str, cities: Optional[List[str]] = None, 
                cuisine_preferences: Optional[List[str]] = None, budget_range: Optional[str] = None,
                meal_types: Optional[List[str]] = None, dietary_restrictions: Optional[List[str]] = None,
                **kwargs) -> str:
        """
        执行餐饮规划任务
        
        Args:
            task_description: 任务描述
            cities: 目标城市列表
            cuisine_preferences: 菜系偏好列表
            budget_range: 预算范围
            meal_types: 用餐类型（早餐、午餐、晚餐、小食等）
            dietary_restrictions: 饮食限制（素食、无麸质等）
        """
        if self.verbose:
            print(f"[RestaurantPlanner] 开始餐饮规划")
        
        try:
            # 从任务描述中提取城市信息（如果未提供）
            if not cities:
                cities = self._extract_cities_from_description(task_description)
            
            # 收集所有相关餐厅数据
            all_restaurants = []
            
            # 定义需要忽略的通用菜系偏好
            ignored_cuisines = ['多样性', '不限', '都行', '任意', '无所谓', '都可以']

            for city in cities:
                # 根据菜系偏好搜索
                effective_cuisine_preferences = [
                    c for c in cuisine_preferences if c not in ignored_cuisines
                ] if cuisine_preferences else []

                if self.verbose:
                    print(f"[RestaurantPlanner] 城市 '{city}' 的有效菜系偏好: {effective_cuisine_preferences}")

                if effective_cuisine_preferences:
                    for cuisine in effective_cuisine_preferences:
                        city_restaurants = self.get_restaurants_by_city(city, cuisine_type=cuisine)
                        all_restaurants.extend(city_restaurants)
                else:
                    # 如果没有有效偏好，则获取该城市所有餐厅
                    city_restaurants = self.get_restaurants_by_city(city)
                    all_restaurants.extend(city_restaurants)

                # 兜底策略：如果筛选后当前城市没有任何结果，则获取该城市评分最高的餐厅
                city_results_count = sum(1 for r in all_restaurants if r['city'] == city)
                if city_results_count == 0:
                    if self.verbose:
                        print(f"[RestaurantPlanner] 城市 '{city}' 按偏好筛选后无结果，启用兜底策略获取评分最高的餐厅")
                    fallback_restaurants = self.get_restaurants_by_city(city, min_rating=2.0)
                    all_restaurants.extend(fallback_restaurants)

            # 去重（基于餐厅名称和城市）
            unique_restaurants = []
            seen = set()
            for restaurant in all_restaurants:
                key = (restaurant['name'], restaurant['city'])
                if key not in seen:
                    seen.add(key)
                    unique_restaurants.append(restaurant)
            
            # 使用LLM进行餐饮规划
            return self._plan_restaurants_with_llm(
                task_description, unique_restaurants, cuisine_preferences, 
                budget_range, meal_types, dietary_restrictions, **kwargs
            )
            
        except Exception as e:
            error_msg = f"❌ 餐饮规划过程中出现错误: {str(e)}"
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
            cities = ['Newark']
        
        return list(cities)[:5]  # 限制城市数量
    
    def _plan_restaurants_with_llm(self, task_description: str, restaurants_data: List[Dict],
                                 cuisine_preferences: Optional[List[str]], budget_range: Optional[str],
                                 meal_types: Optional[List[str]], dietary_restrictions: Optional[List[str]],
                                 **kwargs) -> str:
        """使用LLM进行餐饮规划"""
        
        system_prompt = """你是一个专业的餐饮规划师，专门为旅行者推荐和规划用餐安排。

你的专业技能包括：

规划要求：

请使用以下格式输出餐饮规划：

## 🍽️ 餐饮规划推荐

### 推荐餐厅列表
对每个推荐的餐厅提供：
- **餐厅名称** (中文翻译)
- **菜系类型** (主要菜系)
- **价格水平** 
- **评分和口碑** 
- **所在城市**

### 预算和实用信息
- **总餐饮预算估算**，注意按多人人数计算。


**中文输出，餐厅名称保留英文并注释中文翻译。**
请确保所有推荐都基于提供的餐厅数据。
需要提供三天的早餐、中餐、晚餐。

无需输出规划以外的任何内容。输出排版紧凑。
"""

        # 准备餐厅数据摘要 - 按城市分组显示
        restaurants_summary = ""
        if restaurants_data:
            # 按城市分组餐厅数据
            cities_data = {}
            for rest in restaurants_data:
                city = rest['city']
                if city not in cities_data:
                    cities_data[city] = []
                cities_data[city].append(rest)
            
            restaurants_summary = "可用餐厅数据（按城市分组）：\n\n"
            for city, city_restaurants in cities_data.items():
                restaurants_summary += f"**{city}城市餐厅**:\n"
                # 每个城市最多显示10个餐厅，确保数据平衡
                for i, rest in enumerate(city_restaurants[:10], 1):
                    restaurants_summary += f"{i}. {rest['name']}\n"
                    restaurants_summary += f"   菜系: {rest['cuisines']}, 人均: ${rest['average_cost']}\n"
                    restaurants_summary += f"   评分: {rest['rating']}/5.0\n\n"
                restaurants_summary += "\n"
        else:
            restaurants_summary = "未找到相关餐厅数据，将提供通用餐饮建议。"

        user_prompt = f"""请为我制定详细的餐饮规划：

**规划需求**: {task_description}

**偏好设置**:
- 菜系偏好: {', '.join(cuisine_preferences) if cuisine_preferences else '未指定'}
- 预算范围: {budget_range or '未指定'}
- 用餐类型: {', '.join(meal_types) if meal_types else '未指定'}
- 饮食限制: {', '.join(dietary_restrictions) if dietary_restrictions else '无'}

**可用餐厅数据**:
{restaurants_summary}

请基于以上信息提供详细的餐饮规划和推荐。
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
            return f"❌ 餐饮规划LLM调用失败: {str(e)}"

    def get_available_cuisines(self, city: Optional[str] = None) -> List[str]:
        """获取可用的菜系类型"""
        if self.restaurants_data is None:
            return []
        
        try:
            data = self.restaurants_data
            if city:
                data = data[data['City'] == city]
            
            # 提取所有菜系类型
            all_cuisines = set()
            for cuisines_str in data['Cuisines'].dropna():
                # 分割多个菜系（通常用逗号分隔）
                cuisines = [c.strip() for c in str(cuisines_str).split(',')]
                all_cuisines.update(cuisines)
            
            return sorted(list(all_cuisines))[:20]  # 限制返回数量
            
        except Exception as e:
            if self.verbose:
                print(f"[RestaurantPlanner] 获取菜系类型失败: {e}")
            return []

    def validate_query(self, query: str) -> tuple[bool, str]:
        """验证查询的有效性"""
        if not query or len(query.strip()) < 5:
            return False, "查询内容太短，请提供更详细的餐饮需求"
        
        # 检查是否包含餐饮相关关键词
        restaurant_keywords = ['餐厅', '美食', '用餐', '吃饭', '菜系', '料理', 'restaurant', 'food', 'dining', 'cuisine', 'meal']
        if not any(keyword in query.lower() for keyword in restaurant_keywords):
            return False, "查询内容似乎与餐饮规划无关，请提供餐饮相关的需求"
        
        return True, "查询有效"
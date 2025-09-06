import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel


class TransportationPlannerTool:
    """专门用于交通规划的工具，使用本地数据结合LLM规划"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 设置路径 - 基于TATA项目结构
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # TravelPlanner数据路径
        self.travelplanner_root = os.path.join(project_root, 'agent', 'TravelPlanner')
        self.flights_path = os.path.join(self.travelplanner_root, 'database', 'flights', 'clean_Flights_2022.csv')
        self.distance_path = os.path.join(self.travelplanner_root, 'database', 'googleDistanceMatrix', 'distance.csv')
        
        if self.verbose:
            print(f"[TransportationPlanner] 航班数据路径: {self.flights_path}")
            print(f"[TransportationPlanner] 距离数据路径: {self.distance_path}")
            print(f"[TransportationPlanner] 航班数据存在: {os.path.exists(self.flights_path)}")
            print(f"[TransportationPlanner] 距离数据存在: {os.path.exists(self.distance_path)}")
        
        # 懒加载数据
        self.flights_data = None
        self.distance_data = None
    
    def _load_flights_data(self) -> Optional[pd.DataFrame]:
        """懒加载航班数据"""
        if self.flights_data is not None:
            return self.flights_data
            
        try:
            if not os.path.exists(self.flights_path):
                if self.verbose:
                    print("[TransportationPlanner] 航班数据文件未找到")
                return None
            
            # 加载数据，保留关键字段
            data = pd.read_csv(self.flights_path).dropna()
            # 选择关键字段
            required_columns = ['Flight Number', 'Price', 'DepTime', 'ArrTime', 'ActualElapsedTime', 'FlightDate', 'OriginCityName', 'DestCityName', 'Distance']
            available_columns = [col for col in required_columns if col in data.columns]
            
            if available_columns:
                data = data[available_columns]
                self.flights_data = data
                
                if self.verbose:
                    print(f"[TransportationPlanner] 成功加载 {len(data)} 条航班数据")
                    print(f"[TransportationPlanner] 涵盖城市: {data['OriginCityName'].unique()[:10]}...")
                
                return self.flights_data
            else:
                if self.verbose:
                    print("[TransportationPlanner] 航班数据缺少必要字段")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"[TransportationPlanner] 加载航班数据失败: {e}")
            return None
    
    def _load_distance_data(self) -> Optional[pd.DataFrame]:
        """懒加载距离数据"""
        if self.distance_data is not None:
            return self.distance_data
            
        try:
            if not os.path.exists(self.distance_path):
                if self.verbose:
                    print("[TransportationPlanner] 距离数据文件未找到")
                return None
            
            # 加载数据，不删除cost为空的行，因为我们可以计算cost
            data = pd.read_csv(self.distance_path)
            # 只删除origin, destination, duration, distance都为空的行
            data = data.dropna(subset=['origin', 'destination', 'duration', 'distance'], how='all')
            self.distance_data = data
            
            if self.verbose:
                print(f"[TransportationPlanner] 成功加载 {len(data)} 条距离数据")
                print(f"[TransportationPlanner] 涵盖路线: {len(data['origin'].unique())} 个起点城市")
            
            return self.distance_data
            
        except Exception as e:
            if self.verbose:
                print(f"[TransportationPlanner] 加载距离数据失败: {e}")
            return None
    
    def get_flights_by_route(self, origin: str, destination: str, date: Optional[str] = None) -> List[Dict]:
        """根据起点、终点和日期获取航班信息"""
        flights_data = self._load_flights_data()
        if flights_data is None:
            return []
        
        try:
            # 搜索指定路线的航班
            route_data = flights_data[flights_data['OriginCityName'] == origin]
            route_data = route_data[route_data['DestCityName'] == destination]
            
            # 只有在明确提供日期且数据中存在该日期时才进行日期筛选
            if date and 'FlightDate' in flights_data.columns:
                date_filtered = route_data[route_data['FlightDate'] == date]
                if len(date_filtered) > 0:
                    route_data = date_filtered
                elif self.verbose:
                    print(f"[TransportationPlanner] 未找到指定日期 {date} 的航班，返回所有可用航班")
            
            if len(route_data) == 0:
                # 尝试模糊匹配
                route_data = flights_data[flights_data['OriginCityName'].str.contains(origin, case=False, na=False)]
                route_data = route_data[route_data['DestCityName'].str.contains(destination, case=False, na=False)]
                
                # 对模糊匹配结果也应用相同的日期筛选逻辑
                if date and 'FlightDate' in flights_data.columns:
                    date_filtered = route_data[route_data['FlightDate'] == date]
                    if len(date_filtered) > 0:
                        route_data = date_filtered
                    elif self.verbose:
                        print(f"[TransportationPlanner] 模糊匹配中未找到指定日期 {date} 的航班，返回所有匹配航班")
            
            # 按价格排序
            route_data = route_data.sort_values('Price', ascending=True)
            
            # 转换为字典列表
            flights = []
            for _, row in route_data.iterrows():
                flight = {
                    'flight_number': row.get('Flight Number', 'N/A'),
                    'price': row.get('Price', 0),
                    'departure_time': row.get('DepTime', 'N/A'),
                    'arrival_time': row.get('ArrTime', 'N/A'),
                    'duration': row.get('ActualElapsedTime', 'N/A'),
                    'date': row.get('FlightDate', 'N/A'),
                    'origin': row.get('OriginCityName', origin),
                    'destination': row.get('DestCityName', destination),
                    'distance': row.get('Distance', 'N/A')
                }
                flights.append(flight)
            
            if self.verbose:
                print(f"[TransportationPlanner] 找到 {len(flights)} 个航班从 {origin} 到 {destination}")
                if flights:
                    print(f"[TransportationPlanner] 航班号列表: {[f['flight_number'] for f in flights[:5]]}")
            
            return flights[:20]  # 限制返回数量
            
        except Exception as e:
            if self.verbose:
                print(f"[TransportationPlanner] 搜索航班数据失败: {e}")
            return []

    def get_flight_by_number(self, flight_number: str) -> Optional[Dict]:
        """根据航班号获取特定航班信息"""
        flights_data = self._load_flights_data()
        if flights_data is None:
            return None
        
        try:
            # 搜索指定航班号
            flight_data = flights_data[flights_data['Flight Number'] == flight_number]
            
            if len(flight_data) == 0:
                # 尝试模糊匹配航班号
                flight_data = flights_data[flights_data['Flight Number'].str.contains(flight_number, case=False, na=False)]
            
            if len(flight_data) > 0:
                row = flight_data.iloc[0]  # 取第一个匹配的航班
                flight = {
                    'flight_number': row.get('Flight Number', 'N/A'),
                    'price': row.get('Price', 0),
                    'departure_time': row.get('DepTime', 'N/A'),
                    'arrival_time': row.get('ArrTime', 'N/A'),
                    'duration': row.get('ActualElapsedTime', 'N/A'),
                    'date': row.get('FlightDate', 'N/A'),
                    'origin': row.get('OriginCityName', 'N/A'),
                    'destination': row.get('DestCityName', 'N/A'),
                    'distance': row.get('Distance', 'N/A')
                }
                
                if self.verbose:
                    print(f"[TransportationPlanner] 找到航班 {flight_number}: {flight['origin']} -> {flight['destination']}")
                
                return flight
            
            if self.verbose:
                print(f"[TransportationPlanner] 未找到航班号 {flight_number}")
            return None
            
        except Exception as e:
            if self.verbose:
                print(f"[TransportationPlanner] 搜索航班号失败: {e}")
            return None
    
    def get_ground_transportation(self, origin: str, destination: str, mode: str = 'driving') -> Dict:
        """获取地面交通信息（驾车、出租车等）"""
        distance_data = self._load_distance_data()
        if distance_data is None:
            return {}
        
        try:
            # 搜索路线信息
            route_data = distance_data[
                (distance_data['origin'] == origin) & 
                (distance_data['destination'] == destination)
            ]
            
            if len(route_data) == 0:
                # 尝试模糊匹配
                route_data = distance_data[
                    distance_data['origin'].str.contains(origin, case=False, na=False) &
                    distance_data['destination'].str.contains(destination, case=False, na=False)
                ]
            
            if len(route_data) > 0:
                row = route_data.iloc[0]
                duration = row.get('duration', 'N/A')
                distance = row.get('distance', 'N/A')
                
                # 使用原始数据中的费用信息，如果没有就尝试估算
                cost = row.get('cost', 'N/A')
                if pd.isna(cost) or cost == '' or cost == 'N/A':
                    # 尝试基于距离估算费用
                    if distance != 'N/A' and str(distance).replace('.', '').replace(' ', '').isdigit():
                        try:
                            distance_num = float(str(distance).split()[0])  # 提取数字部分
                            if mode == 'taxi':
                                # 出租车费用估算：基础费用 + 每英里费用
                                estimated_cost = 3.0 + (distance_num * 2.5)  # 基础费用$3 + 每英里$2.5
                                cost = f"${estimated_cost:.2f} (估算)"
                            elif mode == 'driving':
                                # 驾车费用估算：主要是油费
                                estimated_cost = distance_num * 0.15  # 每英里$0.15油费
                                cost = f"${estimated_cost:.2f} (油费估算)"
                        except:
                            cost = '费用信息不可用'
                    else:
                        cost = '费用信息不可用'
                
                transport_info = {
                    'mode': mode,
                    'origin': origin,
                    'destination': destination,
                    'duration': duration,
                    'distance': distance,
                    'cost': cost
                }
                
                if self.verbose:
                    print(f"[TransportationPlanner] 找到地面交通: {mode} 从 {origin} 到 {destination}, 费用: {cost}")
                
                return transport_info
            
            return {}
            
        except Exception as e:
            if self.verbose:
                print(f"[TransportationPlanner] 搜索地面交通失败: {e}")
            return {}
    
    def execute(self, task_description: str, origin: Optional[str] = None,
                destination: Optional[str] = None, travel_date: Optional[str] = None,
                transportation_modes: Optional[List[str]] = None, budget_range: Optional[str] = None,
                **kwargs) -> str:
        """
        执行交通规划任务
        
        Args:
            task_description: 任务描述
            origin: 出发地
            destination: 目的地
            travel_date: 出行日期（可选，如果未提供或数据中无匹配日期，将返回所有可用选项）
            transportation_modes: 交通方式偏好列表（如：flight, driving, taxi等）
            budget_range: 预算范围
        """
        if self.verbose:
            print(f"[TransportationPlanner] 开始交通规划")
            if travel_date:
                print(f"[TransportationPlanner] 指定日期: {travel_date} (如无匹配将返回所有可用选项)")
        
        try:
            # 从任务描述中提取信息（如果未提供）
            extracted_info = self._extract_route_from_description(task_description)
            origin = origin or extracted_info.get('origin')
            destination = destination or extracted_info.get('destination')
            travel_date = travel_date or extracted_info.get('date')
            flight_number = extracted_info.get('flight_number')
            
            # 收集交通数据
            transportation_options = {}
            
            # 如果提取到了航班号，优先搜索特定航班
            if flight_number:
                if self.verbose:
                    print(f"[TransportationPlanner] 搜索特定航班号: {flight_number}")
                try:
                    specific_flight = self.get_flight_by_number(flight_number)
                    if specific_flight:
                        transportation_options['flights'] = [specific_flight]
                        # 如果没有提供起点终点，从航班信息中获取
                        origin = origin or specific_flight['origin']
                        destination = destination or specific_flight['destination']
                        if self.verbose:
                            print(f"[TransportationPlanner] 找到指定航班 {flight_number}")
                    else:
                        if self.verbose:
                            print(f"[TransportationPlanner] 未找到航班号 {flight_number}")
                except Exception as e:
                    if self.verbose:
                        print(f"[TransportationPlanner] 搜索特定航班时出错: {e}")
            
            # 如果没有找到特定航班或没有提供航班号，按路线搜索
            if 'flights' not in transportation_options and origin and destination:
                try:
                    flights = self.get_flights_by_route(origin, destination, travel_date)
                    if flights:
                        transportation_options['flights'] = flights
                        if self.verbose:
                            print(f"[TransportationPlanner] 找到 {len(flights)} 个航班选项")
                except Exception as e:
                    if self.verbose:
                        print(f"[TransportationPlanner] 获取航班信息时出错: {e}")
            
            # 如果仍然没有起点终点信息，返回错误
            if not origin or not destination:
                if flight_number:
                    return f"❌ 未找到航班号 {flight_number}，请检查航班号是否正确。"
                else:
                    return "❌ 无法确定出发地和目的地，请提供更详细的交通需求信息。"
            
            # 获取地面交通信息
            if not transportation_modes:
                transportation_modes = ['driving', 'taxi']
            
            for mode in transportation_modes:
                if mode in ['driving', 'taxi']:
                    try:
                        ground_transport = self.get_ground_transportation(origin, destination, mode)
                        if ground_transport:
                            if 'ground_transport' not in transportation_options:
                                transportation_options['ground_transport'] = []
                            transportation_options['ground_transport'].append(ground_transport)
                    except Exception as e:
                        if self.verbose:
                            print(f"[TransportationPlanner] 获取 {mode} 交通信息时出错: {e}")
                        # 继续处理其他交通方式
            
            # 使用LLM进行交通规划
            return self._plan_transportation_with_llm(
                task_description, transportation_options, origin, destination,
                travel_date, budget_range, **kwargs
            )
            
        except Exception as e:
            error_msg = f"❌ 交通规划过程中出现错误: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _extract_route_from_description(self, description: str) -> Dict[str, str]:
        """从描述中提取路线信息"""
        import re
        
        # 航班号模式
        flight_number_patterns = [
            r'航班号?\s*([A-Z0-9]+)',
            r'flight\s+(?:number\s+)?([A-Z0-9]+)',
            r'([A-Z]{1,3}\d{3,6})',  # 标准航班号格式
        ]
        
        # 常见的路线模式
        route_patterns = [
            r'从\s*([A-Za-z\s]+)\s*到\s*([A-Za-z\s]+)',
            r'去\s*([A-Za-z\s]+)',
            r'from\s+([A-Z][a-zA-Z\s]+)\s+to\s+([A-Z][a-zA-Z\s]+)',
            r'to\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        # 日期模式
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{1,2}月\d{1,2}日)',
        ]
        
        result = {}
        
        # 提取航班号
        for pattern in flight_number_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                result['flight_number'] = matches[0].upper()
                break
        
        # 提取路线
        for pattern in route_patterns:
            matches = re.findall(pattern, description)
            if matches:
                if len(matches[0]) == 2:  # from-to pattern
                    result['origin'] = matches[0][0].strip()
                    result['destination'] = matches[0][1].strip()
                    break
                else:  # single destination
                    result['destination'] = matches[0].strip()
        
        # 提取日期
        for pattern in date_patterns:
            matches = re.findall(pattern, description)
            if matches:
                result['date'] = matches[0]
                break
        
        return result
    
    def _plan_transportation_with_llm(self, task_description: str, transportation_options: Dict,
                                    origin: str, destination: str, travel_date: Optional[str],
                                    budget_range: Optional[str], **kwargs) -> str:
        """使用LLM进行交通规划"""
        
        system_prompt = """你是一个专业的交通规划师，专门为旅行者推荐和规划交通方案。

请使用以下格式输出交通规划：

## 🚗 交通规划推荐

### 推荐交通方案
对每个推荐的交通方案提供：
- **航班号** (如果是航班)
- **交通方式** (航班/驾车/出租车等)
- **路线信息** (出发地到目的地)
- **时间安排** (出发时间、到达时间、行程时长)
- **费用信息** (票价或预估费用)
- **日期信息** (如果有的话)

**重要提示：**
- 如果用户查询特定航班号，请优先显示该航班的详细信息
- 如果找到了用户查询的航班号，请明确说明找到了该航班
- 如果没有找到特定航班号，请明确说明未找到，并提供相同路线的其他航班选项
- **中文输出，交通工具名称保留英文并注释中文翻译**
- 请确保所有推荐都基于提供的交通数据
- 如果没有合适的交通方式，则直接告知没有该条件的交通数据

无需输出规划以外的任何内容。
"""

        # 准备交通数据摘要
        transportation_summary = ""
        if transportation_options:
            transportation_summary = "可用交通数据：\n\n"
            
            # 航班信息
            if 'flights' in transportation_options:
                flights = transportation_options['flights']
                transportation_summary += f"**航班选项** ({len(flights)} 个):\n"
                for i, flight in enumerate(flights[:10], 1):  # 最多显示10个航班
                    transportation_summary += f"{i}. 航班号: {flight['flight_number']}\n"
                    transportation_summary += f"   路线: {flight['origin']} -> {flight['destination']}\n"
                    transportation_summary += f"   价格: ${flight['price']}\n"
                    transportation_summary += f"   时间: {flight['departure_time']} - {flight['arrival_time']}\n"
                    transportation_summary += f"   飞行时长: {flight['duration']}\n"
                    transportation_summary += f"   日期: {flight['date']}\n"
                    transportation_summary += f"   距离: {flight['distance']}\n\n"
                transportation_summary += "\n"
            
            # 地面交通信息
            if 'ground_transport' in transportation_options:
                ground_transports = transportation_options['ground_transport']
                transportation_summary += f"**地面交通选项** ({len(ground_transports)} 个):\n"
                for i, transport in enumerate(ground_transports, 1):
                    transportation_summary += f"{i}. {transport['mode']} (驾车/出租车)\n"
                    transportation_summary += f"   距离: {transport['distance']}, 时长: {transport['duration']}\n"
                    transportation_summary += f"   费用: {transport['cost']}\n\n"
                transportation_summary += "\n"
        else:
            transportation_summary = "未找到相关交通数据，将提供通用交通建议。"

        user_prompt = f"""请为我制定详细的交通规划：

**规划需求**: {task_description}

**路线信息**:
- 出发地: {origin}
- 目的地: {destination}
- 出行日期: {travel_date or '未指定'}

**约束条件**:
- 预算范围: {budget_range or '未指定'}

**可用交通数据**:
{transportation_summary}

请基于以上信息提供详细的交通规划和推荐。
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
            return f"❌ 交通规划LLM调用失败: {str(e)}"

    def validate_query(self, query: str) -> tuple[bool, str]:
        """验证查询的有效性"""
        if not query or len(query.strip()) < 5:
            return False, "查询内容太短，请提供更详细的交通需求"
        
        # 检查是否包含交通相关关键词
        transportation_keywords = [
            '交通', '出行', '航班', '飞机', '驾车', '开车', '出租车', '巴士', '火车',
            'transportation', 'flight', 'driving', 'taxi', 'bus', 'train', 'travel'
        ]
        if not any(keyword in query.lower() for keyword in transportation_keywords):
            return False, "查询内容似乎与交通规划无关，请提供交通相关的需求"
        
        return True, "查询有效"
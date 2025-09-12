import os
import json
import ast
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

class TravelInfoExtractorTool:
    """从本地数据集中提取和分析旅游相关信息的工具"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 🎯 设置固定的数据路径 - 指向TravelPlanner目录中的数据文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # 固定使用指定的数据文件路径
        self.data_path = os.path.join(project_root, 'agent', 'TravelPlanner', 'TravelPlan', 'local_validation_data.json')
        
        if self.verbose:
            print(f"[TravelInfoExtractorTool] 数据路径: {self.data_path}")
            print(f"[TravelInfoExtractorTool] 数据文件存在: {os.path.exists(self.data_path)}")
    
    def execute(self, query_type: str = "all", max_items: int = 10, 
                filter_criteria: Optional[Dict] = None, analysis_focus: str = "", 
                destination: str = "", specific_query: str = "", **kwargs) -> str:
        """
        执行信息提取操作
        
        Args:
            query_type: 查询类型 ("all", "by_destination", "by_budget", "by_days", "summary", "destination_info")
            max_items: 最大返回项目数
            filter_criteria: 过滤条件字典
            analysis_focus: 分析重点
            destination: 🎯 新增：目的地名称（用于destination_info查询）
            specific_query: 🎯 新增：具体查询内容（如"费城有哪些低于100元的饭店"）
        """
        if self.verbose:
            print(f"[TravelInfoExtractorTool] 开始提取信息: {query_type}")
        
        try:
            # 🎯 修复：如果是目的地信息查询，直接返回结果，不再调用 _analyze_with_llm
            if query_type == "destination_info":
                return self._extract_destination_specific_info(destination, specific_query, analysis_focus)
            
            # 加载数据
            data = self._load_local_data()
            if not data:
                return "❌ 无法加载旅游数据，请检查数据文件是否存在于: " + self.data_path
            
            # 根据查询类型处理数据
            if query_type == "all":
                result = self._extract_all_info(data, max_items)
            elif query_type == "by_destination":
                dest = filter_criteria.get('destination', '') if filter_criteria else (destination or '')
                result = self._extract_by_destination(data, dest, max_items)
            elif query_type == "by_budget":
                budget_range = filter_criteria.get('budget_range', [0, 10000]) if filter_criteria else [0, 10000]
                result = self._extract_by_budget(data, budget_range, max_items)
            elif query_type == "by_days":
                days = filter_criteria.get('days', 7) if filter_criteria else 7
                result = self._extract_by_days(data, days, max_items)
            elif query_type == "summary":
                result = self._extract_summary(data)
            else:
                result = self._extract_all_info(data, max_items)
            
            # 🎯 修复：只对非 destination_info 查询使用 LLM 分析
            return self._analyze_with_llm(result, query_type, analysis_focus)
            
        except Exception as e:
            error_msg = f"❌ 信息提取过程中出现错误: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _extract_destination_specific_info(self, destination: str, specific_query: str, analysis_focus: str = "") -> str:
        """🎯 新增：提取特定目的地的具体信息"""
        try:
            if not destination:
                return "❌ 请提供要查询的目的地名称"
            
            # 🎯 修复：添加调试日志
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 查询目的地: {destination}")
                print(f"[TravelInfoExtractorTool] 具体查询: {specific_query}")
            
            # 从本地数据中查找相关目的地的详细信息
            destination_data = self._search_destination_in_local_data(destination)
            
            if not destination_data:
                return f"❌ 在本地数据中未找到关于 {destination} 的相关信息"
            
            # 🎯 修复：如果没有具体查询，直接返回格式化的目的地数据
            if not specific_query.strip():
                return f"## {destination} 的详细信息\n\n{destination_data}"
            
            # 🎯 修复：添加防止递归调用的检查
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 正在调用 LLM 分析目的地信息...")
            
            # 使用LLM处理具体查询
            system_prompt = f"""你是一个专业的旅游信息查询助手，专门从本地旅游数据中提取用户需要的具体信息。

你的任务是根据用户的具体查询，从提供的 {destination} 相关数据中提取准确、有用的信息。

注意：
1. **只能使用提供的本地数据**，不要添加任何外部信息
2. 如果数据中没有相关信息，请明确说明
3. 对于价格、数量等具体要求，要严格按照用户条件筛选
4. 提供清晰的格式化输出，便于阅读
5. 如果找到相关信息，要提供具体的名称、地址、价格等详细信息

查询重点：{analysis_focus if analysis_focus else '根据用户问题提供准确信息'}"""

            user_prompt = f"""用户查询：{specific_query}
目标地点：{destination}

相关本地数据：
{destination_data}

提供中英对照。

请根据用户的具体查询，从上述数据中提取相关信息。如果数据中没有满足条件的信息，请如实说明。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            # 🎯 修复：确保 LLM 调用是一次性的
            response = self.llm.invoke(messages)
            
            if self.verbose:
                print(f"[TravelInfoExtractorTool] LLM 分析完成")
            
            return response.content
            
        except Exception as e:
            error_msg = f"❌ 查询目的地信息失败: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _search_destination_in_local_data(self, destination: str) -> str:
        """🎯 新增：在本地数据中搜索特定目的地的详细信息"""
        try:
            # 🎯 修复：添加调试日志
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 搜索本地数据中的目的地: {destination}")
            
            data = self._load_local_data()
            if not data:
                return ""
            
            destination_info = []
            destination_lower = destination.lower()
            
            for item in data:
                reference_info = item.get('reference_information', '')
                
                # 解析reference_information中的详细信息
                if reference_info:
                    try:
                        if reference_info.startswith('[') and reference_info.endswith(']'):
                            ref_list = ast.literal_eval(reference_info)
                            
                            for ref_item in ref_list:
                                if isinstance(ref_item, dict):
                                    description = ref_item.get('Description', '').lower()
                                    content = ref_item.get('Content', '')
                                    
                                    # 检查是否包含目标目的地
                                    if destination_lower in description or destination_lower in content.lower():
                                        destination_info.append({
                                            'type': ref_item.get('Description', ''),
                                            'content': content
                                        })
                    except Exception as e:
                        if self.verbose:
                            print(f"解析参考信息失败: {e}")
                        continue
            
            if destination_info:
                # 🎯 修复：添加找到信息的日志
                if self.verbose:
                    print(f"[TravelInfoExtractorTool] 找到 {len(destination_info)} 条相关信息")
                
                # 格式化输出
                formatted_info = f"## {destination} 相关信息\n\n"
                
                # 按类型分组
                info_by_type = {}
                for info in destination_info:
                    info_type = info['type']
                    if info_type not in info_by_type:
                        info_by_type[info_type] = []
                    info_by_type[info_type].append(info['content'])
                
                for info_type, contents in info_by_type.items():
                    formatted_info += f"### {info_type}\n\n"
                    for content in contents:
                        formatted_info += f"{content}\n\n"
                
                return formatted_info
            
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 未找到关于 {destination} 的信息")
            
            return f"在本地数据中未找到关于 {destination} 的详细信息"
            
        except Exception as e:
            error_msg = f"搜索本地数据时出错: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _load_local_data(self) -> List[Dict]:
        """从本地JSON文件加载数据"""
        try:
            if not os.path.exists(self.data_path):
                if self.verbose:
                    print(f"[TravelInfoExtractorTool] 数据文件不存在: {self.data_path}")
                return []
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 成功加载 {len(data)} 条数据")
            
            return data
            
        except Exception as e:
            if self.verbose:
                print(f"[TravelInfoExtractorTool] 加载数据失败: {e}")
            return []
    
    def _extract_all_info(self, data: List[Dict], max_items: int) -> str:
        """提取所有信息的摘要"""
        try:
            result = f"数据集包含 {len(data)} 条旅游查询记录\n\n"
            
            for i, item in enumerate(data[:max_items]):
                idx = item.get('idx', i)
                query = item.get('query', '无查询信息')
                
                result += f"【查询 {idx}】\n"
                result += f"需求: {query}\n\n"
                
                # 提取关键信息
                if 'reference_information' in item:
                    ref_summary = self._extract_reference_summary(item['reference_information'])
                    if ref_summary:
                        result += f"参考信息: {ref_summary}\n\n"
                
                result += "-" * 50 + "\n\n"
            
            return result
            
        except Exception as e:
            return f"提取所有信息失败: {str(e)}"
    
    def _extract_by_destination(self, data: List[Dict], destination: str, max_items: int) -> str:
        """按目的地提取信息"""
        try:
            if not destination:
                return "未指定目的地"
            
            destination_lower = destination.lower()
            matching_items = []
            
            for item in data:
                query = item.get('query', '').lower()
                reference_info = item.get('reference_information', '').lower()
                
                if destination_lower in query or destination_lower in reference_info:
                    matching_items.append(item)
            
            if not matching_items:
                return f"未找到与 {destination} 相关的旅游信息"
            
            result = f"找到 {len(matching_items)} 条与 {destination} 相关的信息\n\n"
            
            for i, item in enumerate(matching_items[:max_items]):
                idx = item.get('idx', i)
                query = item.get('query', '无查询信息')
                
                result += f"【相关查询 {idx}】\n"
                result += f"需求: {query}\n\n"
                
                # 提取相关的参考信息
                if 'reference_information' in item:
                    ref_summary = self._extract_reference_summary(item['reference_information'])
                    if ref_summary:
                        result += f"参考信息: {ref_summary}\n\n"
                
                result += "-" * 50 + "\n\n"
            
            return result
            
        except Exception as e:
            return f"按目的地提取信息失败: {str(e)}"
    
    def _extract_by_budget(self, data: List[Dict], budget_range: List[int], max_items: int) -> str:
        """按预算范围提取信息"""
        try:
            min_budget, max_budget = budget_range
            matching_items = []
            
            for item in data:
                query = item.get('query', '')
                
                # 从查询中提取预算信息
                budget = self._extract_budget_from_query(query)
                
                if budget and min_budget <= budget <= max_budget:
                    matching_items.append((item, budget))
            
            if not matching_items:
                return f"未找到预算在 ${min_budget}-${max_budget} 范围内的旅游信息"
            
            result = f"找到 {len(matching_items)} 条预算在 ${min_budget}-${max_budget} 范围内的信息\n\n"
            
            for i, (item, budget) in enumerate(matching_items[:max_items]):
                idx = item.get('idx', i)
                query = item.get('query', '无查询信息')
                
                result += f"【预算查询 {idx}】\n"
                result += f"预算: ${budget}\n"
                result += f"需求: {query}\n\n"
                
                result += "-" * 50 + "\n\n"
            
            return result
            
        except Exception as e:
            return f"按预算提取信息失败: {str(e)}"
    
    def _extract_by_days(self, data: List[Dict], days: int, max_items: int) -> str:
        """按天数提取信息"""
        try:
            matching_items = []
            
            for item in data:
                query = item.get('query', '')
                
                # 从查询中提取天数信息
                trip_days = self._extract_days_from_query(query)
                
                if trip_days and trip_days == days:
                    matching_items.append((item, trip_days))
            
            if not matching_items:
                return f"未找到 {days} 天的旅游信息"
            
            result = f"找到 {len(matching_items)} 条 {days} 天的旅游信息\n\n"
            
            for i, (item, trip_days) in enumerate(matching_items[:max_items]):
                idx = item.get('idx', i)
                query = item.get('query', '无查询信息')
                
                result += f"【{trip_days}天查询 {idx}】\n"
                result += f"需求: {query}\n\n"
                
                result += "-" * 50 + "\n\n"
            
            return result
            
        except Exception as e:
            return f"按天数提取信息失败: {str(e)}"
    
    def _extract_summary(self, data: List[Dict]) -> str:
        """提取数据集摘要"""
        try:
            total_items = len(data)
            
            # 统计目的地
            destinations = set()
            budgets = []
            days_list = []
            
            for item in data:
                query = item.get('query', '')
                
                # 提取目的地
                dest = self._extract_destination_from_query(query)
                if dest:
                    destinations.add(dest)
                
                # 提取预算
                budget = self._extract_budget_from_query(query)
                if budget:
                    budgets.append(budget)
                
                # 提取天数
                days = self._extract_days_from_query(query)
                if days:
                    days_list.append(days)
            
            result = f"数据集摘要\n\n"
            result += f"总查询数: {total_items}\n"
            result += f"涉及目的地: {len(destinations)} 个\n"
            result += f"主要目的地: {', '.join(list(destinations)[:10])}\n\n"
            
            if budgets:
                result += f"预算范围: ${min(budgets)} - ${max(budgets)}\n"
                result += f"平均预算: ${sum(budgets) // len(budgets)}\n\n"
            
            if days_list:
                result += f"行程天数: {min(days_list)} - {max(days_list)} 天\n"
                result += f"平均天数: {sum(days_list) // len(days_list)} 天\n\n"
            
            return result
            
        except Exception as e:
            return f"提取摘要失败: {str(e)}"
    
    def _extract_reference_summary(self, reference_info: str) -> str:
        """提取参考信息摘要"""
        if not reference_info:
            return ""
        
        try:
            # 尝试解析为JSON/List
            if reference_info.startswith('[') and reference_info.endswith(']'):
                ref_list = ast.literal_eval(reference_info)
                
                categories = {}
                for item in ref_list:
                    if isinstance(item, dict) and 'Description' in item:
                        desc = item['Description']
                        if desc not in categories:
                            categories[desc] = 0
                        categories[desc] += 1
                
                summary = "包含: " + ", ".join([f"{desc}({count})" for desc, count in categories.items()])
                return summary
            else:
                return reference_info[:100] + "..." if len(reference_info) > 100 else reference_info
                
        except Exception as e:
            return reference_info[:100] + "..." if len(reference_info) > 100 else reference_info
    
    def _extract_destination_from_query(self, query: str) -> str:
        """从查询中提取目的地"""
        import re
        
        patterns = [
            r'to\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
            r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
            r'heading\s+to\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                dest = match.group(1).strip()
                # 过滤常见非地名
                if dest not in ['March', 'April', 'May', 'June', 'July', 'August']:
                    return dest
        
        return ""
    
    def _extract_budget_from_query(self, query: str) -> int:
        """从查询中提取预算"""
        import re
        
        pattern = r'\$([0-9,]+)'
        match = re.search(pattern, query)
        if match:
            try:
                budget_str = match.group(1).replace(',', '')
                return int(budget_str)
            except:
                pass
        
        return 0
    
    def _extract_days_from_query(self, query: str) -> int:
        """从查询中提取天数"""
        import re
        
        patterns = [
            r'(\d+)-day',
            r'(\d+)\s+day',
            r'for\s+(\d+)\s+days',
            r'duration\s+is\s+for\s+(\d+)\s+days'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        
        return 0
    
    def _analyze_with_llm(self, extracted_data: str, query_type: str, analysis_focus: str) -> str:
        """使用LLM分析和格式化提取的数据"""
        try:
            system_prompt = f"""你是一个专业的旅游数据分析师，擅长从旅游数据中提取有用信息并进行分析。

请根据提供的数据进行分析，重点关注：{analysis_focus if analysis_focus else '提供有用的旅游信息摘要'}

要求：
1. 提供清晰、结构化的分析结果
2. 突出重要信息和趋势
3. 为用户提供实用的建议
4. 使用友好、专业的语调
"""

            user_prompt = f"""查询类型: {query_type}
分析重点: {analysis_focus if analysis_focus else '全面分析'}

原始数据:
{extracted_data}
提供中英对照。
请对上述数据进行分析和总结。"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            if self.verbose:
                print(f"LLM分析失败: {e}")
            return extracted_data  # 返回原始数据作为备选

import os
import sys
import json
import time
from typing import Dict, Any, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

class TravelPlannerTool:
    """使用TravelPlanner框架进行旅游行程规划的工具"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        self.planner = None
        self.strategy = "direct"
        
        # 🎯 设置路径 - 基于TATA项目结构，指向固定的TravelPlanner目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # 固定TravelPlanner路径
        self.travelplanner_root = os.path.join(project_root, 'agent', 'TravelPlanner')
        
        # 数据文件路径
        self.data_path = os.path.join(self.travelplanner_root, 'TravelPlan', 'local_validation_data.json')
        
        if self.verbose:
            print(f"[TravelPlannerTool] TravelPlanner根目录: {self.travelplanner_root}")
            print(f"[TravelPlannerTool] 数据文件路径: {self.data_path}")
            print(f"[TravelPlannerTool] TravelPlanner目录存在: {os.path.exists(self.travelplanner_root)}")
            print(f"[TravelPlannerTool] 数据文件存在: {os.path.exists(self.data_path)}")
        
        # 初始化规划器
        self._setup_planner_environment()
    
    def _setup_planner_environment(self):
        """设置TravelPlanner环境"""
        try:
            if not os.path.exists(self.travelplanner_root):
                if self.verbose:
                    print("[TravelPlannerTool] TravelPlanner目录未找到，将使用通用LLM规划")
                self.planner_classes = None
                self.prompts = None
                return
            
            # 添加TravelPlanner路径到sys.path
            if self.travelplanner_root not in sys.path:
                sys.path.insert(0, self.travelplanner_root)
            
            # 添加agents和tools路径
            agents_path = os.path.join(self.travelplanner_root, 'agents')
            tools_path = os.path.join(self.travelplanner_root, 'tools', 'planner')
            
            for path in [agents_path, tools_path]:
                if path not in sys.path and os.path.exists(path):
                    sys.path.insert(0, path)
            
            # 设置工作目录
            original_cwd = os.getcwd()
            os.chdir(self.travelplanner_root)
            
            if self.verbose:
                print(f"[TravelPlannerTool] 切换工作目录到: {os.getcwd()}")
            
            # 尝试导入TravelPlanner模块
            try:
                from agents.prompts import (planner_agent_prompt, cot_planner_agent_prompt, 
                                           react_planner_agent_prompt, react_reflect_planner_agent_prompt, 
                                           reflect_prompt)
                from tools.planner.apis import Planner, ReactPlanner, ReactReflectPlanner
                
                # 存储导入的类和提示
                self.planner_classes = {
                    'Planner': Planner,
                    'ReactPlanner': ReactPlanner, 
                    'ReactReflectPlanner': ReactReflectPlanner
                }
                
                self.prompts = {
                    'direct': planner_agent_prompt,
                    'cot': cot_planner_agent_prompt,
                    'react': react_planner_agent_prompt,
                    'reflexion': react_reflect_planner_agent_prompt,
                    'reflect': reflect_prompt
                }
                
                if self.verbose:
                    print("[TravelPlannerTool] TravelPlanner模块导入成功")
                    
            except ImportError as e:
                if self.verbose:
                    print(f"[TravelPlannerTool] TravelPlanner模块导入失败: {e}")
                self.planner_classes = None
                self.prompts = None
            
            # 恢复原始工作目录
            os.chdir(original_cwd)
                
        except Exception as e:
            if self.verbose:
                print(f"[TravelPlannerTool] 环境设置失败: {e}")
            self.planner_classes = None
            self.prompts = None
    
    def execute(self, task_description: str, strategy: str = "direct", 
                model_name: str = "gpt-4o", reference_data: Optional[Dict] = None,
                max_retries: int = 3, **kwargs) -> str:
        """
        执行旅游规划任务
        
        Args:
            task_description: 任务描述/查询
            strategy: 规划策略 ("direct", "cot", "react", "reflexion")
            model_name: 使用的模型名称
            reference_data: 参考信息数据
            max_retries: 最大重试次数
        """
        if self.verbose:
            print(f"[TravelPlannerTool] 开始规划: 策略={strategy}, 模型={model_name}")
        
        try:
            # 🎯 首先尝试从本地数据中找到相关的参考信息
            local_reference = self._get_local_reference_data(task_description)
            
            # 如果有本地参考数据，使用它；否则使用传入的reference_data
            if local_reference and not reference_data:
                reference_data = local_reference
                if self.verbose:
                    print("[TravelPlannerTool] 使用本地参考数据")
            
            # 如果有TravelPlanner可用，使用专业规划器
            if self.planner_classes and self.prompts:
                return self._plan_with_travelplanner(task_description, strategy, model_name, 
                                                   reference_data, max_retries)
            else:
                # 否则使用通用LLM规划
                return self._plan_with_llm(task_description, reference_data, **kwargs)
                
        except Exception as e:
            error_msg = f"❌ 旅游规划过程中出现错误: {str(e)}"
            if self.verbose:
                print(error_msg)
            return error_msg
    
    def _get_local_reference_data(self, task_description: str) -> Optional[str]:
        """从本地数据文件中获取相关的参考信息"""
        try:
            if not os.path.exists(self.data_path):
                return None
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 🎯 改进关键词匹配逻辑，适应实际数据结构
            task_lower = task_description.lower()
            
            # 提取任务中的关键词
            task_keywords = set()
            
            # 提取地名
            import re
            location_patterns = [
                r'to\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
                r'from\s+([A-Z][a-zA-Z\s]+?)(?:\s+to|\s+with|\s*,|\s*\?|$)',
                r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, task_description)
                for match in matches:
                    task_keywords.add(match.strip().lower())
            
            # 寻找最佳匹配的数据项
            best_match = None
            best_score = 0
            
            for item in data:
                query = item.get('query', '').lower()
                score = 0
                
                # 计算关键词匹配得分
                for keyword in task_keywords:
                    if keyword in query:
                        score += 2
                
                # 计算通用词汇匹配得分
                task_words = set(task_lower.split())
                query_words = set(query.split())
                common_words = task_words.intersection(query_words)
                
                # 过滤掉常见停用词
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'help', 'plan', 'trip', 'travel'}
                meaningful_words = common_words - stop_words
                score += len(meaningful_words)
                
                if score > best_score:
                    best_score = score
                    best_match = item
            
            if best_match:
                if self.verbose:
                    print(f"[TravelPlannerTool] 找到最佳匹配: idx={best_match.get('idx', 'N/A')}, 得分={best_score}")
                
                return best_match.get('reference_information', '')
            
            # 如果没有找到特定匹配，返回第一个数据项的参考信息
            if data:
                if self.verbose:
                    print("[TravelPlannerTool] 使用第一个数据项作为参考")
                return data[0].get('reference_information', '')
            
        except Exception as e:
            if self.verbose:
                print(f"[TravelPlannerTool] 获取本地参考数据失败: {e}")
        
        return None
    
    def _plan_with_travelplanner(self, task_description: str, strategy: str, 
                               model_name: str, reference_data: Optional[Dict], 
                               max_retries: int) -> str:
        """使用TravelPlanner框架进行规划"""
        try:
            # 🎯 修改：在任务描述前添加中文输出指令
            chinese_instruction = """请用中文回答。请严格按照以下要求用中文输出详细的旅游行程规划：

要求：
1. 所有说明和描述都用中文
2. 地名可以保留英文，但要有中文翻译
3. 时间、预算、行程安排都用中文描述
4. 使用中文的时间格式和货币表达

任务："""
            
            enhanced_task = chinese_instruction + task_description
            
            # 创建规划器实例
            if strategy == 'direct':
                planner = self.planner_classes['Planner'](
                    model_name=model_name, 
                    agent_prompt=self.prompts['direct']
                )
            elif strategy == 'cot':
                planner = self.planner_classes['Planner'](
                    model_name=model_name, 
                    agent_prompt=self.prompts['cot']
                )
            elif strategy == 'react':
                planner = self.planner_classes['ReactPlanner'](
                    model_name=model_name, 
                    agent_prompt=self.prompts['react']
                )
            elif strategy == 'reflexion':
                planner = self.planner_classes['ReactReflectPlanner'](
                    model_name=model_name, 
                    agent_prompt=self.prompts['reflexion'],
                    reflect_prompt=self.prompts['reflect']
                )
            else:
                # 默认使用direct策略
                planner = self.planner_classes['Planner'](
                    model_name=model_name, 
                    agent_prompt=self.prompts['direct']
                )
            
            # 🎯 准备参考信息 - 适应实际数据格式
            reference_information = ""
            if reference_data:
                if isinstance(reference_data, str):
                    reference_information = reference_data
                elif isinstance(reference_data, dict) and 'reference_information' in reference_data:
                    reference_information = reference_data['reference_information']
                else:
                    reference_information = json.dumps(reference_data, ensure_ascii=False, indent=2)
            
            # 🎯 如果reference_information是字符串化的列表，尝试格式化它
            if reference_information and reference_information.startswith('['):
                try:
                    import ast
                    ref_list = ast.literal_eval(reference_information)
                    if isinstance(ref_list, list):
                        # 将列表格式化为更可读的文本
                        formatted_info = []
                        for item in ref_list:
                            if isinstance(item, dict):
                                desc = item.get('Description', 'Information')
                                content = item.get('Content', '')
                                formatted_info.append(f"{desc}:\n{content}\n")
                        reference_information = "\n".join(formatted_info)
                except:
                    pass  # 如果解析失败，保持原样
            
            if self.verbose:
                print(f"[TravelPlannerTool] 使用参考信息长度: {len(reference_information)}")
                print(f"[TravelPlannerTool] 增强任务描述: {enhanced_task[:100]}...")
            
            # 执行规划
            planner_results = None
            scratchpad = None
            
            for retry_count in range(max_retries):
                try:
                    if strategy in ['react', 'reflexion']:
                        planner_results, scratchpad = planner.run(reference_information, enhanced_task)
                    else:
                        planner_results = planner.run(reference_information, enhanced_task)
                    
                    if planner_results is not None:
                        break
                        
                except Exception as e:
                    if self.verbose:
                        print(f"重试 {retry_count + 1}/{max_retries}: {e}")
                    
                    if retry_count < max_retries - 1:
                        time.sleep(2)
            
            if planner_results is None:
                return f"❌ 经过 {max_retries} 次尝试后仍无法生成规划结果"
            
            # 🎯 修改：如果结果仍然是英文，使用LLM翻译为中文
            if self._is_english_result(planner_results):
                planner_results = self._translate_to_chinese(planner_results)
            
            # 格式化结果
            result = f"## 🗺️ 旅游规划结果\n\n"
            # result += f"**规划策略**: {strategy}\n"
            # result += f"**模型**: {model_name}\n"
            # result += f"**使用本地数据**: 是\n\n"
            result += f"### 详细行程\n\n{planner_results}\n"
            
            if scratchpad and self.verbose:
                result += f"\n### 规划过程日志\n\n```\n{scratchpad}\n```"
            
            return result
            
        except Exception as e:
            if self.verbose:
                print(f"TravelPlanner规划失败，回退到LLM规划: {e}")
            return self._plan_with_llm(task_description, reference_data)

    def _is_english_result(self, text: str) -> bool:
        """检测文本是否主要为英文"""
        if not text:
            return False
        
        # 简单检测：如果英文字符占比超过70%，认为是英文
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars == 0:
            return False
        
        english_ratio = english_chars / total_chars
        return english_ratio > 0.7

    def _translate_to_chinese(self, english_text: str) -> str:
        """将英文结果翻译为中文"""
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            
            translation_prompt = """你是一个专业的旅游文档翻译专家。请将以下英文旅游行程规划完整地翻译为中文，要求：

1. 保持原有的格式和结构
2. 地名保留英文，但添加中文翻译，如：New York (纽约)
3. 时间格式改为中文习惯，如：Day 1 → 第1天
4. 货币符号保留，但添加中文说明
5. 保持专业性和准确性
6. 保留所有的具体信息（时间、地点、价格等）

请翻译以下内容："""

            messages = [
                SystemMessage(content=translation_prompt),
                HumanMessage(content=english_text)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            if self.verbose:
                print(f"翻译失败: {e}")
            return english_text  # 翻译失败时返回原文

    def _plan_with_llm(self, task_description: str, reference_data: Optional[Dict], **kwargs) -> str:
        """使用通用LLM进行规划（备用方案）"""
        system_prompt = """你是一个专业的旅游行程规划师，具有丰富的全球旅游经验和规划能力。

你的专业技能包括：
1. 深入了解全球各地的旅游资源、文化特色和最佳游览时间
2. 精通行程优化，能够合理安排时间和路线，避免疲劳和重复路程
3. 熟悉不同类型旅行者的需求（家庭、情侣、独行、商务等）
4. 掌握预算控制技巧，能够在有限预算内最大化旅行体验
5. 了解当地交通、住宿、餐饮和娱乐选择

规划要求：
- 按天数安排具体行程，包含时间、地点、交通、用餐、住宿
- 提供预算估算和实用提示
- 考虑实际可行性（物理约束）和舒适度

请使用以下格式输出详细的行程规划：

## 🗺️ 行程概览
- 旅行主题和亮点
- 总体时间安排
- 预算分配建议

## 📅 逐日详细行程
对每一天提供：
- **日期和主题**
- **具体时间安排** (如：09:00-12:00)
- **景点/活动详情** (包括地址、门票、游览时长)，景点一定要在当地！
- **交通方式** (如何到达，用时，费用)
- **用餐建议** (推荐餐厅或美食街)
- **住宿信息** (位置、价格范围、预订建议)，**一定要注意最**小入住天数**和最少入住人数,可以按照住宿的最小天数调整旅行的城市安排**。一定要在当天所在城市住宿！
- **当日预算** (分项估算)


**中文输出，地名、酒店名、餐厅名等注释英文。**，确保所有地点、景点、住宿、早中午餐内容都在reference_data中有对应的内容。
请确保所有建议都具体可行，并包含详细的实用信息。

无需输出规划以外的任何内容。

"""

        user_prompt = f"""请为我制定详细的旅游行程规划：

**规划需求**: {task_description}

"""
        
        # 添加参考数据
        if reference_data:
            if isinstance(reference_data, str):
                user_prompt += f"\n**参考信息**:\n{reference_data}\n"
            else:
                user_prompt += f"\n**参考信息**:\n```json\n{json.dumps(reference_data, ensure_ascii=False, indent=2)}\n```\n"
        
        # 添加其他参数
        for key, value in kwargs.items():
            if value:
                user_prompt += f"**{key}**: {value}\n"
        
        user_prompt += "\n请提供详细的逐日行程安排，包含时间、地点、交通、用餐、住宿和预算信息。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"❌ LLM规划失败: {str(e)}"
    
    def get_available_strategies(self) -> list:
        """获取可用的规划策略"""
        if self.planner_classes:
            return ['direct', 'cot', 'react', 'reflexion']
        else:
            return ['llm_general']
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """验证查询的有效性"""
        if not query or len(query.strip()) < 10:
            return False, "查询内容太短，请提供更详细的旅游需求"
        
        # 检查是否包含基本的旅游要素
        travel_keywords = ['旅游', '旅行', '行程', '规划', '计划', 'travel', 'trip', 'plan', 'itinerary']
        if not any(keyword in query.lower() for keyword in travel_keywords):
            return False, "查询内容似乎与旅游规划无关，请提供旅游相关的需求"
        
        return True, "查询有效"

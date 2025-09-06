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
        # 🎯 调试输出：打印execute方法接收到的参数（始终输出）
        print("\n" + "="*80)
        print("TRAVELPLANNER EXECUTE DEBUG")
        print("="*80)
        print(f"TASK_DESCRIPTION: {task_description}")
        print(f"STRATEGY: {strategy}")
        print(f"MODEL_NAME: {model_name}")
        print(f"REFERENCE_DATA: {reference_data}")
        print(f"MAX_RETRIES: {max_retries}")
        print(f"KWARGS: {kwargs}")
        print("="*80 + "\n")
        
        if self.verbose:
            print(f"[TravelPlannerTool] 开始规划: 策略={strategy}, 模型={model_name}")
        
        try:
            # 🎯 首先尝试从本地数据中找到相关的参考信息
            local_reference = self._get_local_reference_data(task_description)
            
            # 🎯 修复：优先使用本地匹配到的参考数据，而不是传入的reference_data
            if local_reference:
                reference_data = local_reference
                print("[TravelPlannerTool] ✅ 使用本地匹配的参考数据")
            elif reference_data:
                print("[TravelPlannerTool] ⚠️ 使用传入的reference_data（本地未找到匹配）")
            else:
                print("[TravelPlannerTool] ❌ 没有可用的参考数据")
            
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
        # 🎯 调试输出：打印方法开始（始终输出）
        print("\n" + "="*80)
        print("_GET_LOCAL_REFERENCE_DATA DEBUG START")
        print("="*80)
        print(f"TASK_DESCRIPTION: {task_description}")
        print(f"DATA_PATH: {self.data_path}")
        print(f"DATA_PATH_EXISTS: {os.path.exists(self.data_path)}")
        print("="*80 + "\n")
        
        try:
            if not os.path.exists(self.data_path):
                print("❌ 数据文件不存在，返回None")
                return None
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ 成功加载数据文件，包含 {len(data)} 个数据项")
            
            # 🎯 改进关键词匹配逻辑，支持中英文地名匹配
            task_lower = task_description.lower()
            print(f"🔍 任务描述（小写）: {task_lower}")
            
            # 中英文地名对照表
            location_mapping = {
                '拉斯维加斯': ['las vegas', 'vegas'],
                '圣玛利亚': ['santa maria'],
                '圣玛丽亚': ['santa maria'],
                '费城': ['philadelphia'],
                '里士满': ['richmond'],
                '彼得斯堡': ['petersburg'],
                '夏洛茨维尔': ['charlottesville'],
                '纽瓦克': ['newark'],
                '伊萨卡': ['ithaca']
            }
            
            # 提取任务中的关键词
            task_keywords = set()
            
            # 提取英文地名
            import re
            location_patterns = [
                r'to\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
                r'from\s+([A-Z][a-zA-Z\s]+?)(?:\s+to|\s+with|\s*,|\s*\?|$)',
                r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
            ]
            
            print("🔍 开始提取地名关键词...")
            for pattern in location_patterns:
                matches = re.findall(pattern, task_description)
                print(f"   模式 '{pattern}' 匹配到: {matches}")
                for match in matches:
                    keyword = match.strip().lower()
                    task_keywords.add(keyword)
                    print(f"   添加关键词: '{keyword}'")
            
            # 提取中文地名并转换为英文
            print("🔍 检查中文地名...")
            for chinese_name, english_names in location_mapping.items():
                if chinese_name in task_description:
                    task_keywords.update(english_names)
                    print(f"   检测到中文地名: {chinese_name} -> {english_names}")
            
            print(f"🎯 最终提取的关键词: {task_keywords}")
            
            # 寻找最佳匹配的数据项
            best_match = None
            best_score = 0
            all_scores = []  # 记录所有得分用于调试
            
            print("\n🔍 开始匹配数据项...")
            for i, item in enumerate(data):
                query = item.get('query', '').lower()
                idx = item.get('idx', 'N/A')
                score = 0
                match_details = []
                
                print(f"\n--- 数据项 {i+1}/{len(data)} (idx={idx}) ---")
                print(f"查询: {query}")
                
                # 计算关键词匹配得分（地名匹配权重更高）
                for keyword in task_keywords:
                    if keyword in query:
                        score += 5  # 提高地名匹配权重
                        match_details.append(f"地名匹配: '{keyword}'")
                        print(f"   ✅ 地名匹配: '{keyword}' (+5分)")
                
                # 计算通用词汇匹配得分
                task_words = set(task_lower.split())
                query_words = set(query.split())
                common_words = task_words.intersection(query_words)
                
                # 过滤掉常见停用词
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'help', 'plan', 'trip', 'travel', '设计', '规划', '旅行', '天', '包括', '自驾', '住宿', '游览', '预算'}
                meaningful_words = common_words - stop_words
                word_score = len(meaningful_words)
                score += word_score
                
                if meaningful_words:
                    match_details.append(f"词汇匹配: {meaningful_words}")
                    print(f"   ✅ 词汇匹配: {meaningful_words} (+{word_score}分)")
                
                print(f"   📊 总得分: {score}")
                if match_details:
                    print(f"   📝 匹配详情: {'; '.join(match_details)}")
                
                all_scores.append((idx, score, query[:50]))
                
                if score > best_score:
                    best_score = score
                    best_match = item
                    print(f"   🎯 新的最佳匹配! (得分: {score})")
            
            print(f"\n📊 所有数据项得分汇总:")
            for idx, score, query_preview in all_scores:
                marker = "👑" if score == best_score and score > 0 else "  "
                print(f"{marker} idx={idx}, 得分={score}, 查询='{query_preview}...'")
            
            if best_match and best_score > 0:
                print(f"\n🎯 最终选择: idx={best_match.get('idx', 'N/A')}, 得分={best_score}")
                
                # 🎯 调试输出：打印选中数据项的详细信息
                print("\n" + "="*80)
                print("SELECTED DATA ITEM DETAILS")
                print("="*80)
                print(f"IDX: {best_match.get('idx', 'N/A')}")
                print(f"QUERY: {best_match.get('query', '')}")
                
                ref_info = best_match.get('reference_information', '')
                if isinstance(ref_info, str):
                    print(f"REFERENCE_INFO (string, length={len(ref_info)}):")
                    print(ref_info[:500] + "..." if len(ref_info) > 500 else ref_info)
                else:
                    print(f"REFERENCE_INFO (type={type(ref_info)}):")
                    print(json.dumps(ref_info, ensure_ascii=False, indent=2)[:500] + "..." if len(str(ref_info)) > 500 else json.dumps(ref_info, ensure_ascii=False, indent=2))
                print("="*80 + "\n")
                
                return best_match.get('reference_information', '')
            
            # 🎯 修改：如果没有找到有意义的匹配（得分>0），返回None而不是第一个数据项
            print(f"\n❌ 未找到匹配的参考数据 (最高得分: {best_score})，将使用通用LLM规划")
            return None
            
        except Exception as e:
            print(f"❌ 获取本地参考数据失败: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def _plan_with_travelplanner(self, task_description: str, strategy: str, 
                               model_name: str, reference_data: Optional[Dict], 
                               max_retries: int) -> str:
        """使用TravelPlanner框架进行规划"""
        try:
            # 🎯 修改：添加完整的格式要求指令
            format_instruction = """请用中文回答。请严格按照以下格式输出详细的旅游行程规划：

## 📅 逐日详细行程
对每一天提供：
- 景点/活动详情，景点一定要在当地！（每天只选择一个景点）
- 交通方式 (用时，费用，必须包含出发地和目的地)；格式：交通方式，出发地和目的地。如果是航班，必须包含航班号。
- 餐厅 (推荐餐厅,一定包含早餐（一定要参考信息，有指定具体地点）、午餐、晚餐！*禁止出现重复餐厅*;不需要安排出发日的早餐和返回日的晚餐！)；
- 住宿信息 (位置)，**一定要注意最**小入住天数**和最少入住人数,可以按照住宿的最小天数调整旅行的城市安排**。一定要在当天所在城市住宿！

最后，给出整体的预算：
- 整体预算 (**分项估算，给出公式**)

**中文输出（必须有中文注释），地名、酒店名、餐厅名等注释英文。**，确保所有地点、景点、住宿、早中午餐内容都在REFERENCE DATA中有对应的内容。
景点、餐厅禁止重复。

无需输出规划以外的任何内容。

---

参考格式（需要换行）：

第1天：
**当前城市**：*从出发城市到目的地城市*
- 交通方式：交通工具，从[出发地]到[目的地]，如有航班号，必须包含航班号。
- 早餐：- (**无需安排**)
- 景点：景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：餐厅名称，城市名
- 住宿：住宿名称（住宿描述），城市名

第2天：
- 当前城市：城市名
- 交通方式：- (**无需安排**)
- 早餐：餐厅名称，城市名
- 景点：景点名称（景点中文名），城市名；景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：餐厅名称，城市名
- 住宿：住宿名称（住宿描述），城市名

第3天：
- 当前城市：*从出发城市到目的地城市*
- 交通方式：交通工具，从[出发地]到[目的地]，如有航班号，必须包含航班号。
- 早餐：餐厅名称，城市名
- 景点：景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：- (**无需安排**)

"""
            
            enhanced_task = format_instruction + task_description
            
            # 🎯 调试输出：打印TravelPlanner使用的参数（始终输出）
            print("\n" + "="*80)
            print("TRAVELPLANNER DEBUG")
            print("="*80)
            print(f"STRATEGY: {strategy}")
            print(f"MODEL: {model_name}")
            print(f"TASK DESCRIPTION: {task_description}")
            print(f"ENHANCED TASK: {enhanced_task}")
            print(f"REFERENCE DATA: {reference_data}")
            print("="*80 + "\n")
            
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
                
                # 🎯 添加数据验证：检查地理信息一致性
                validation_result = self._validate_reference_data(task_description, reference_information)
                if not validation_result['is_valid']:
                    print(f"⚠️ 参考数据验证失败: {validation_result['reason']}")
                    print("🔄 回退到通用LLM规划")
                    return self._plan_with_llm(task_description, None)
            
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
            
            # 🎯 调试输出：打印TravelPlanner原始结果（始终输出）
            print("\n" + "="*80)
            print("TRAVELPLANNER RESULT DEBUG")
            print("="*80)
            print("RAW PLANNER RESULTS:")
            print(planner_results)
            if scratchpad:
                print("\nSCRATCHPAD:")
                print(scratchpad)
            print("="*80 + "\n")
            
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
2. 地名保留英文，但添加中文翻译，如：newark (纽瓦克)
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
        system_prompt = """你是一个专业的旅游行程规划师，按照给出数据进行旅游规划。


## 📅 逐日详细行程
对每一天提供：
- 景点/活动详情，景点一定要在当地！（每天只选择一个景点）
- 交通方式 (用时，费用，必须包含出发地和目的地)；格式：交通方式，出发地和目的地。如果是航班，必须包含航班号。
- 餐厅 (推荐餐厅,一定包含早餐（一定要参考信息，有指定具体地点）、午餐、晚餐！*禁止出现重复餐厅*;不需要安排出发日的早餐和返回日的晚餐！)；
- 住宿信息 (位置)，**一定要注意最**小入住天数**和最少入住人数,可以按照住宿的最小天数调整旅行的城市安排**。一定要在当天所在城市住宿！

最后，给出整体的预算：
- 整体预算 (**分项估算，给出公式**)。注意按人数计算。

**中文输出（必须有中文注释），地名、酒店名、餐厅名等注释英文。**，确保所有地点、景点、住宿、早中午餐内容都在REFERENCE DATA中有对应的内容。
景点、餐厅禁止重复。

无需输出规划以外的任何内容。

---

参考格式（需要换行）：

第1天：
**当前城市**：*从出发城市到目的地城市*
- 交通方式：交通工具，从[出发地]到[目的地]，如有航班号，必须包含航班号。
- 早餐：- (**无需安排**)
- 景点：景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：餐厅名称，城市名
- 住宿：住宿名称（住宿描述），城市名

第2天：
- 当前城市：城市名
- 交通方式：- (**无需安排**)
- 早餐：餐厅名称，城市名
- 景点：景点名称（景点中文名），城市名；景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：餐厅名称，城市名
- 住宿：住宿名称（住宿描述），城市名

第3天：
- 当前城市：*从出发城市到目的地城市*
- 交通方式：交通工具，从[出发地]到[目的地]，如有航班号，必须包含航班号。
- 早餐：餐厅名称，城市名
- 景点：景点名称（景点中文名），城市名
- 午餐：餐厅名称，城市名
- 晚餐：- (**无需安排**)

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
        
        # 🎯 调试输出：打印实际使用的prompt（始终输出）
        print("\n" + "="*80)
        print("TRAVEL PLANNER PROMPT DEBUG")
        print("="*80)
        print("SYSTEM PROMPT:")
        print(system_prompt)
        print("\n" + "-"*80)
        print("USER PROMPT:")
        print(user_prompt)
        print("="*80 + "\n")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            # 🎯 调试输出：打印LLM响应（始终输出）
            print("\n" + "="*80)
            print("LLM RESPONSE DEBUG")
            print("="*80)
            print(response.content)
            print("="*80 + "\n")
            
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
    
    def _validate_reference_data(self, task_description: str, reference_information: str) -> dict:
        """验证参考数据的地理信息一致性"""
        try:
            # 提取任务中的目标城市
            task_lower = task_description.lower()
            target_cities = set()
            
            # 地名映射
            location_mapping = {
                'newark': ['newark', 'nj', 'new jersey'],
                'ithaca': ['ithaca', 'ny', 'new york state'],
                'philadelphia': ['philadelphia', 'philly', 'pa'],
                'richmond': ['richmond', 'va', 'virginia'],
                'petersburg': ['petersburg', 'va', 'virginia'],
                'charlottesville': ['charlottesville', 'va', 'virginia'],
                'las vegas': ['las vegas', 'vegas', 'nv', 'nevada'],
                'santa maria': ['santa maria', 'ca', 'california']
            }
            
            # 提取目标城市
            import re
            patterns = [
                r'to\s+([a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
                r'heading\s+to\s+([a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
                r'visit\s+([a-zA-Z\s]+?)(?:\s+from|\s+with|\s*,|\s*\?|$)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, task_description, re.IGNORECASE)
                for match in matches:
                    city = match.strip().lower()
                    target_cities.add(city)
            
            # 检查中文地名
            chinese_mapping = {
                '纽瓦克': 'newark',
                '伊萨卡': 'ithaca',
                '费城': 'philadelphia',
                '里士满': 'richmond',
                '彼得斯堡': 'petersburg',
                '夏洛茨维尔': 'charlottesville',
                '拉斯维加斯': 'las vegas',
                '圣玛利亚': 'santa maria'
            }
            
            for chinese, english in chinese_mapping.items():
                if chinese in task_description:
                    target_cities.add(english)
            
            print(f"🔍 验证目标城市: {target_cities}")
            
            if not target_cities:
                return {'is_valid': True, 'reason': '未检测到明确的目标城市'}
            
            # 检查参考信息中是否包含错误的地理信息
            ref_lower = reference_information.lower()
            
            # 检查是否包含纽约相关信息（当目标不是纽约时）
            nyc_indicators = [
                'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island',
                'times square', 'central park', 'wall street', 'broadway',
                'west village', 'east village', 'soho', 'tribeca',
                'upper west side', 'uws', 'upper east side', 'ues',
                'williamsburg', 'park slope', 'dumbo', 'chelsea',
                'gramercy', 'midtown', 'downtown manhattan'
            ]
            
            # 如果目标城市不包含纽约相关城市，但参考信息包含纽约信息，则验证失败
            is_nyc_target = any(city in ['new york', 'nyc', 'manhattan', 'brooklyn'] for city in target_cities)
            
            if not is_nyc_target:
                nyc_found = []
                for indicator in nyc_indicators:
                    if indicator in ref_lower:
                        nyc_found.append(indicator)
                
                if nyc_found:
                    return {
                        'is_valid': False,
                        'reason': f'目标城市为{target_cities}，但参考数据包含纽约信息: {nyc_found[:3]}'
                    }
            
            # 验证目标城市是否在参考信息中
            city_found = False
            for target_city in target_cities:
                if target_city in location_mapping:
                    city_keywords = location_mapping[target_city]
                    if any(keyword in ref_lower for keyword in city_keywords):
                        city_found = True
                        break
                elif target_city in ref_lower:
                    city_found = True
                    break
            
            if not city_found:
                return {
                    'is_valid': False,
                    'reason': f'参考数据中未找到目标城市{target_cities}的相关信息'
                }
            
            return {'is_valid': True, 'reason': '数据验证通过'}
            
        except Exception as e:
            print(f"❌ 数据验证过程中出现错误: {e}")
            return {'is_valid': True, 'reason': f'验证过程出错，跳过验证: {e}'}

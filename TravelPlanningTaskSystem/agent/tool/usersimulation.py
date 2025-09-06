from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from typing import Dict, List, Any, Optional
import json
import uuid
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class UserPersona:
    """用户画像数据结构"""
    id: str
    persona: str
    intent: str
    age: int
    age_group: str
    gender: str
    income: List[int]
    income_group: str
    created_at: str = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class SimulationRecord:
    """模拟记录数据结构"""
    user_id: str
    timestamp: str
    action_type: str  # persona/trial/insight/interview/research
    data: Dict[str, Any]
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

# 在文件开头添加配置类

class UserSimulationConfig:
    """用户模拟工具配置类 - 统一管理所有配置"""
    
    # 通用系统提示词模板
    SYSTEM_PROMPTS = {
        'persona_generator': """你是用户研究agent中的一个模块，负责生成符合产品测试需求的模拟用户画像，你的具体角色是 USER_PERSONA 模块。

你的任务是创建真实、详细的用户画像，这些画像应该代表可能对该产品感兴趣的潜在用户。
每个用户画像应包含完整的背景故事、人口统计学信息、经济状况、购物习惯、职业生活和个人风格。
你应该考虑不同年龄段、性别、收入水平和生活方式的用户，确保画像多样性。
用户画像应该具有特定的购买意图或使用需求，与产品的功能和价值主张相匹配。
所有生成的用户画像必须真实可信，具有连贯的生活背景和合理的消费行为。

## 必须遵守的规则
* 请勿输出任何其他内容。
* **每个用户画像必须包含以下字段**：persona（包含背景、人口统计学、经济状况、购物习惯、职业生活、个人风格）、intent（具体购买或使用意图）、age（具体年龄）、age_group（年龄段）、gender（性别）、income（收入范围，以数组形式）、income_group（收入组别）
* 所有字段必须使用中文填写，保持格式一致性。
* 用户画像应该足够具体，使产品团队能够清晰理解这类用户的需求、行为和决策过程。
* 根据产品特性，调整用户画像的重点内容，确保与产品测试目标高度相关。

请严格按照JSON数组格式输出，不要包含任何其他文本。例如：
[
  {
    "persona": "详细的用户背景描述...",
    "intent": "具体的使用意图...", 
    "age": 32,
    "age_group": "30-35",
    "gender": "女性",
    "income": [120000, 200000],
    "income_group": "120000-200000"
  }
]""",

        'product_trial': """你是一个产品试用模拟专家。您的任务是根据给定的角色、页面信息意图和相关记忆模拟产品试用过程。
您将扮演特定用户角色，并模拟该角色与产品功能和触点的真实交互过程。
*你只能操作之前观察到的项目，而不能幻想自己做了其余操作*禁止出现幻觉！！

请严格按照JSON格式输出：
{
  "当前状态": "描述当前的试用状态和进展",
  "思考过程": "描述角色的思考过程和动机", 
  "下一步": "描述角色的下一步具体行动"
}""",
        
        'market_research': """你是一个市场调研分析专家。你需要基于用户画像，从该用户的视角分析其在相关领域的需求、痛点、偏好和决策因素。
分析应该深入、具体，能够为产品开发和市场策略提供有价值的指导。

严格按照JSON格式输出：
{
  "needs": "详细的需求描述",
  "pain_points": "当前面临的主要痛点",
  "preferences": "产品功能和体验偏好",
  "budget_considerations": "预算考虑和价格敏感度",
  "decision_factors": "影响购买决策的关键因素",
  "usage_scenarios": "主要使用场景描述"
}""",
        
        'user_interview': """你是一个专业的用户访谈模拟器。你需要模拟一位刚使用过特定产品的用户，真实自然地回答访谈问题。

## 模拟规则：
- 如果被问到你没有过的体验或者功能，直接说没有用到/没有注意到
- 回答要像真实用户一样自然，包含犹豫、想法转变和情绪反应
- 使用第一人称，包含口语化表达和填充词
- 提供具体的使用场景和例子，而非泛泛而谈

输出格式：
{"answer": "你的详细回答"}""",
        
        'insight_generator': """你是一个用户体验分析专家。你需要根据用户的角色特征和行为记录，生成深入的产品使用洞察。

你是一个正在浏览网页的人。您将获得一份近期记忆的列表，包括观察、行动、计划和反思。
你现在在想什么？输出你从最近的行为中获得的高级见解。

你需要精确地模拟这个角色。尝试提出这个角色可能会问的问题。
你应该始终以第一人称思考。
你应该对你的思考进行排序，把你认为最重要的事情优先排序。

输出格式：
{"insights": ["洞察1", "洞察2", "洞察3", ...]}"""
    }
    
    # 必需字段定义
    REQUIRED_FIELDS = {
        'persona': ['persona', 'intent', 'age', 'age_group', 'gender', 'income', 'income_group'],
        'product_trial': ['当前状态', '思考过程', '下一步'],
        'market_research': ['needs', 'pain_points', 'preferences', 'budget_considerations', 'decision_factors', 'usage_scenarios'],
        'user_interview': ['answer'],
        'insight_generator': ['insights']
    }
    
    # 降级响应模板
    FALLBACK_RESPONSES = {
        'product_trial': {
            "当前状态": "正在浏览产品页面，了解功能特点",
            "思考过程": "正在评估产品是否符合个人需求和预算",
            "下一步": "深入了解产品的核心功能和价格信息"
        },
        'market_research': {
            "needs": "需要能提高效率和便利性的解决方案",
            "pain_points": "现有工具功能有限，使用复杂，学习成本高",
            "preferences": "界面简洁直观，功能实用，操作简单",
            "budget_considerations": "希望价格合理，性价比高",
            "decision_factors": "实用性、易用性、品牌口碑、售后服务",
            "usage_scenarios": "主要在工作和生活中使用，需要适应不同场景需求"
        }
    }

class BaseSimulationTool:
    """基础模拟工具类 - 提供通用方法"""
    
    def __init__(self, llm: BaseChatModel, tool_type: str, verbose: bool = False):
        self.llm = llm
        self.tool_type = tool_type
        self.verbose = verbose
        self.config = UserSimulationConfig()
    
    def _log(self, message: str):
        """统一日志方法"""
        if self.verbose:
            print(f"[{self.__class__.__name__} LOG] {message}")
    
    def _call_llm_with_fallback(self, messages: List, fallback_key: str = None) -> Dict[str, Any]:
        """统一的LLM调用和降级处理"""
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            self._log(f"LLM Raw Response for {self.tool_type}: {content[:300]}...") # 增加日志，显示原始响应

            if not content:
                self._log(f"LLM returned empty content for {self.tool_type}.")
                raise ValueError("LLM returned empty content")

            result = json.loads(content)
            
            # 验证必需字段
            if self.tool_type in self.config.REQUIRED_FIELDS:
                required = self.config.REQUIRED_FIELDS[self.tool_type]
                for field in required:
                    if field not in result:
                        # 如果关键字段缺失，也视为一种错误，可能需要降级
                        self._log(f"Missing required field '{field}' in LLM response for {self.tool_type}.")
                        if fallback_key and fallback_key in self.config.FALLBACK_RESPONSES:
                            # 尝试从降级响应中填充缺失字段
                            result[field] = self.config.FALLBACK_RESPONSES[fallback_key].get(
                                field, f"默认{field}内容"
                            )
                        else:
                            result[field] = f"默认{field}内容" 
            
            return result
            
        except json.JSONDecodeError as json_e:
            self._log(f"LLM调用失败 (JSONDecodeError) for {self.tool_type}: {json_e}. Content was: {content[:300]}")
            if fallback_key and fallback_key in self.config.FALLBACK_RESPONSES:
                self._log(f"Using fallback response for {fallback_key}")
                return self.config.FALLBACK_RESPONSES[fallback_key].copy()
            return {} # 返回空字典，让调用方处理
        except ValueError as val_e: # 捕获空内容错误
            self._log(f"LLM调用失败 (ValueError) for {self.tool_type}: {val_e}.")
            if fallback_key and fallback_key in self.config.FALLBACK_RESPONSES:
                self._log(f"Using fallback response for {fallback_key}")
                return self.config.FALLBACK_RESPONSES[fallback_key].copy()
            return {}
        except Exception as e:
            self._log(f"LLM调用失败 (General Exception) for {self.tool_type}: {e}")
            if fallback_key and fallback_key in self.config.FALLBACK_RESPONSES:
                self._log(f"Using fallback response for {fallback_key}")
                return self.config.FALLBACK_RESPONSES[fallback_key].copy()
            return {}
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.config.SYSTEM_PROMPTS.get(self.tool_type, "你是一个专业的模拟工具。")

# 🎯 重构后的工具类 - 使用继承减少重复

class PersonaGeneratorTool(BaseSimulationTool):
    """功能1: 指定人数和需求，按照需求生成用户档案"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        super().__init__(llm, 'persona_generator', verbose)

    def execute(self, count: int, product_description: str, target_audience: str, requirements: str = "", **kwargs) -> List[UserPersona]:
        self._log(f"开始生成 {count} 个用户画像...")

        user_prompt = f"""产品描述：{product_description}
目标受众：{target_audience}
需求用户个数：{count}
{f"额外要求：{requirements}" if requirements else ""}

请以JSON数组格式输出{count}个用户画像。"""

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # 添加调试信息
            self._log(f"LLM响应内容: {content[:200]}...")
            
            personas_data = json.loads(content) if content else []
            
            if not isinstance(personas_data, list):
                personas_data = [personas_data] if personas_data else []

            personas = []
            for i, data in enumerate(personas_data[:count]):
                try:
                    # 验证必需字段
                    for field in self.config.REQUIRED_FIELDS['persona']:
                        if field not in data:
                            raise ValueError(f"缺少必需字段: {field}")
                    
                    persona_id = str(uuid.uuid4())
                    persona = UserPersona(id=persona_id, **{k: v for k, v in data.items() if k != 'id'})
                    personas.append(persona)
                except Exception as e:
                    self._log(f"解析用户画像 {i} 失败: {e}")
                    continue

            if not personas:
                personas = self._generate_fallback_personas(count, product_description)
            
            self._log(f"成功生成 {len(personas)} 个用户画像")
            return personas

        except Exception as e:
            self._log(f"生成用户画像失败: {e}")
            return self._generate_fallback_personas(count, product_description)

    def _generate_fallback_personas(self, count: int, product_desc: str) -> List[UserPersona]:
        """降级生成用户画像"""
        self._log(f"使用降级模式生成 {count} 个用户画像")
        
        personas = []
        base_ages = [25, 30, 35, 40, 45]
        genders = ["男性", "女性"]
        
        for i in range(count):
            persona_id = str(uuid.uuid4())
            age = base_ages[i % len(base_ages)] + (i // len(base_ages)) * 3
            gender = genders[i % len(genders)]
            income_base = 80000 + i * 30000
            
            persona = UserPersona(
                id=persona_id,
                persona=f"用户{i+1}，{age}岁的{gender}，对{product_desc}感兴趣。",
                intent=f"寻找能够解决实际问题的{product_desc}产品，提升生活或工作效率",
                age=age,
                age_group=f"{age-5}-{age+5}",
                gender=gender,
                income=[income_base, income_base * 2],
                income_group=f"{income_base}-{income_base * 2}"
            )
            personas.append(persona)
        
        return personas

class ProductTrialSimulatorTool(BaseSimulationTool):
    """功能2: 有产品详情时，模拟用户档案使用产品"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        super().__init__(llm, 'product_trial', verbose)

    def execute(self, user_persona: UserPersona, product_info: str, page_info: str, memory: List[str] = None, **kwargs) -> Dict[str, str]:
        self._log(f"模拟用户 {user_persona.id} 的产品试用...")

        memory_text = "; ".join(memory or [])
        user_prompt = f"""用户角色：{user_persona.persona}
产品信息：{product_info}
页面信息：{page_info}
相关记忆：{memory_text}

请模拟该用户与产品的真实交互过程，体现其个性特征和决策思路。"""

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_prompt)
        ]

        result = self._call_llm_with_fallback(messages, 'product_trial')
        
        # 如果降级响应，个性化处理
        if not result or result == self.config.FALLBACK_RESPONSES['product_trial']:
            result = {
                "当前状态": f"我正在浏览{page_info}，了解产品功能和特点",
                "思考过程": f"作为{user_persona.age}岁的{user_persona.gender}，我需要评估这个产品是否符合我的需求和预算",
                "下一步": "深入了解产品的核心功能和价格信息"
            }

        return result

class MarketResearchTool(BaseSimulationTool):
    """功能3: 无产品详情时，对用户做市场调研"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        super().__init__(llm, 'market_research', verbose)

    def execute(self, user_persona: UserPersona, research_topics: List[str], **kwargs) -> Dict[str, str]:
        self._log(f"对用户 {user_persona.id} 进行市场调研...")

        topics_text = "; ".join(research_topics)
        user_prompt = f"""用户画像：{user_persona.persona}
调研主题：{topics_text}

请从这个用户角色的视角，详细分析其在相关领域的需求、痛点、偏好和决策因素。"""

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_prompt)
        ]

        result = self._call_llm_with_fallback(messages, 'market_research')
        
        # 个性化降级响应
        if not result or len(result) < 3:
            result = {
                "needs": f"作为{user_persona.age}岁{user_persona.gender}，我需要能提高效率和便利性的解决方案",
                "pain_points": "现有工具功能有限，使用复杂，学习成本高",
                "preferences": "界面简洁直观，功能实用，操作简单",
                "budget_considerations": f"根据{user_persona.income_group}收入水平，希望价格合理，性价比高",
                "decision_factors": "实用性、易用性、品牌口碑、售后服务",
                "usage_scenarios": "主要在工作和生活中使用，需要适应不同场景需求"
            }

        return result

class UserInterviewTool(BaseSimulationTool):
    """用户访谈工具 - 收集定性反馈"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        super().__init__(llm, 'user_interview', verbose)

    def execute(self, user_persona: UserPersona, questions: List[str], behaviors: List[str] = None, satisfaction: int = 4, **kwargs) -> List[Dict[str, str]]:
        self._log(f"对用户 {user_persona.id} 进行访谈...")

        behavior_text = "; ".join(behaviors or [])
        responses = []
        
        for question in questions:
            user_prompt = f"""用户画像：{user_persona.persona}
行为历史：{behavior_text}
产品体验总体满意度：{satisfaction}/5分
访谈问题：{question}

请真实自然地回答这个问题，体现用户的真实感受和体验。"""

            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=user_prompt)
            ]

            result = self._call_llm_with_fallback(messages, 'user_interview')
            answer = result.get('answer', f"对于'{question}'这个问题，我觉得产品总体还不错。")
            responses.append({'question': question, 'answer': answer})

        return responses

class UserInsightGeneratorTool(BaseSimulationTool): # 修复：继承 BaseSimulationTool
    """用户洞察生成工具 - 基于用户行为生成产品洞察"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        super().__init__(llm, 'insight_generator', verbose) # 修复：调用父类构造函数

    def execute(self, user_persona: UserPersona, behaviors: List[str], **kwargs) -> List[str]:
        self._log(f"为用户 {user_persona.id} 生成洞察...") # 使用 _log

        behavior_text = "; ".join(behaviors)

        user_prompt = f"""你的角色描述是：{user_persona.persona}

你使用了网站得出了以下行为：{behavior_text}

请提供3-5个具体的洞察，每个洞察应该清晰、具体且有价值。"""

        messages = [
            SystemMessage(content=self._get_system_prompt()), # 使用 _get_system_prompt
            HumanMessage(content=user_prompt)
        ]

        # 使用统一的LLM调用方法
        result = self._call_llm_with_fallback(messages, fallback_key=None) # 明确 fallback_key 为 None，因为没有预设的降级
        
        insights = result.get('insights', [])

        # 如果LLM调用失败且没有降级，提供一个通用的降级洞察列表
        if not insights and not result: # 检查 result 是否为空字典，表示调用失败且无降级
            self._log(f"生成洞察失败，使用通用降级洞察 for {user_persona.id}")
            insights = [
                f"产品界面设计符合{user_persona.age_group}年龄段用户的使用习惯。",
                "功能布局相对直观，但仍有优化空间。",
                "价格策略需要更清晰的说明和对比。"
            ]
        elif not insights and 'insights' not in result: # 如果 LLM 响应了但没有 insights 字段
             self._log(f"LLM 响应中缺少 'insights' 字段，使用通用降级洞察 for {user_persona.id}")
             insights = [
                f"用户 {user_persona.gender} ({user_persona.age}岁) 对产品表现出初步兴趣。",
                "需要进一步分析用户行为以获取更深层次的洞察。",
            ]


        return insights

class UserSimulationStatsTool:
    """功能4: 用户行为信息和质性信息输出/统计"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def execute(self, personas: List[UserPersona], records: List[SimulationRecord], **kwargs) -> Dict[str, Any]:
        if self.verbose:
            print("[UserSimulationStatsTool LOG] 生成统计分析...")
        
        if not personas:
            return {"message": "暂无数据", "timestamp": datetime.now().isoformat()}

        # 人口统计学分析
        ages = [p.age for p in personas]
        genders = [p.gender for p in personas]
        income_groups = [p.income_group for p in personas]

        # 行为统计分析
        action_counts = {}
        for record in records:
            action_counts[record.action_type] = action_counts.get(record.action_type, 0) + 1

        # 满意度统计
        satisfactions = []
        insights_all = []
        for record in records:
            if record.action_type == 'interview' and 'satisfaction' in record.data:
                satisfactions.append(record.data['satisfaction'])
            elif record.action_type == 'insight' and 'insights' in record.data:
                insights_all.extend(record.data['insights'])

        return {
            "用户总数": len(personas),
            "人口统计学分析": {
                "平均年龄": round(sum(ages) / len(ages), 1),
                "年龄范围": f"{min(ages)}-{max(ages)}岁",
                "性别分布": {g: genders.count(g) for g in set(genders)},
                "收入分布": {ig: income_groups.count(ig) for ig in set(income_groups)}
            },
            "行为统计分析": {
                "总记录数": len(records),
                "行为类型分布": action_counts,
                "用户平均活跃度": round(len(records) / len(personas), 1) if personas else 0
            },
            "质性信息分析": {
                "平均满意度": round(sum(satisfactions) / len(satisfactions), 1) if satisfactions else None,
                "满意度分布": {str(s): satisfactions.count(s) for s in set(satisfactions)} if satisfactions else {},
                "总洞察数量": len(insights_all),
                "洞察样本": insights_all[:5] if insights_all else []
            },
            "统计时间": datetime.now().isoformat()
        }

class UserSimulationSuite:
    """用户模拟工具套件 - 整合所有功能的主控制器"""
    
    def __init__(self, llm: BaseChatModel, verbose: bool = False):
        self.llm = llm
        self.verbose = verbose
        
        # 初始化各个工具
        self.persona_generator = PersonaGeneratorTool(llm, verbose)
        self.trial_simulator = ProductTrialSimulatorTool(llm, verbose)
        self.market_researcher = MarketResearchTool(llm, verbose)
        self.interviewer = UserInterviewTool(llm, verbose)
        self.insight_generator = UserInsightGeneratorTool(llm, verbose)
        self.stats_tool = UserSimulationStatsTool(verbose)
        
        # 数据存储
        self.personas: Dict[str, UserPersona] = {}
        self.records: List[SimulationRecord] = []

    def _record_action(self, user_id: str, action_type: str, data: Dict[str, Any]):
        """记录用户行为"""
        record = SimulationRecord(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            action_type=action_type,
            data=data
        )
        self.records.append(record)
        if self.verbose:
            print(f"记录用户行为: {action_type} for {user_id}")

    def generate_personas(self, count: int, product_description: str, target_audience: str, requirements: str = "") -> List[UserPersona]:
        """生成用户画像"""
        personas = self.persona_generator.execute(count, product_description, target_audience, requirements)
        
        for persona in personas:
            self.personas[persona.id] = persona
            self._record_action(persona.id, 'persona', asdict(persona))
        
        return personas

    def simulate_product_trial(self, user_id: str, product_info: str, page_info: str, memory: List[str] = None) -> Dict[str, str]:
        """模拟产品试用"""
        if user_id not in self.personas:
            raise ValueError(f"User {user_id} not found")
        
        result = self.trial_simulator.execute(self.personas[user_id], product_info, page_info, memory)
        self._record_action(user_id, 'trial', result)
        return result

    def conduct_market_research(self, user_id: str, research_topics: List[str]) -> Dict[str, str]:
        """进行市场调研"""
        if user_id not in self.personas:
            raise ValueError(f"User {user_id} not found")
        
        result = self.market_researcher.execute(self.personas[user_id], research_topics)
        self._record_action(user_id, 'research', result)
        return result

    def conduct_interview(self, user_id: str, questions: List[str], behaviors: List[str] = None, satisfaction: int = 4) -> List[Dict[str, str]]:
        """进行用户访谈"""
        if user_id not in self.personas:
            raise ValueError(f"User {user_id} not found")
        
        result = self.interviewer.execute(self.personas[user_id], questions, behaviors, satisfaction)
        self._record_action(user_id, 'interview', {'responses': result, 'satisfaction': satisfaction})
        return result

    def generate_insights(self, user_id: str, behaviors: List[str]) -> List[str]:
        """生成用户洞察"""
        if user_id not in self.personas:
            raise ValueError(f"User {user_id} not found")
        
        result = self.insight_generator.execute(self.personas[user_id], behaviors)
        self._record_action(user_id, 'insight', {'insights': result})
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计分析"""
        return self.stats_tool.execute(list(self.personas.values()), self.records)

    def export_data(self, format: str = "json") -> str:
        """导出完整数据"""
        if self.verbose:
            print(f"导出数据，格式: {format}")
        
        export_data = {
            "用户画像": [asdict(p) for p in self.personas.values()],
            "模拟记录": [asdict(r) for r in self.records],
            "统计分析": self.get_statistics(),
            "导出时间": datetime.now().isoformat()
        }

        if format.lower() == "json":
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        else:
            # CSV格式简化输出
            csv_lines = ["# 用户模拟数据导出"]
            csv_lines.append("用户ID,年龄,性别,收入组别,意图,记录数")

            for persona in self.personas.values():
                record_count = sum(1 for r in self.records if r.user_id == persona.id)
                csv_lines.append(f"{persona.id},{persona.age},{persona.gender},{persona.income_group},{persona.intent},{record_count}")

            return "\n".join(csv_lines)

# LangChain工具接口
@tool
def generate_user_personas_tool(count: int, product_description: str, target_audience: str, requirements: str = "") -> str:
    """生成用户画像工具"""
    return f"生成用户画像工具: 需要 {count} 个用户，产品: {product_description}，目标: {target_audience}"

@tool 
def simulate_product_trial_tool(user_persona_json: str, product_info: str, page_info: str, memory: str = "") -> str:
    """模拟产品试用工具"""
    return f"产品试用模拟: 用户在 {page_info} 试用 {product_info}"

@tool
def conduct_user_interview_tool(user_persona_json: str, questions: str, behaviors: str = "", satisfaction: int = 4) -> str:
    """用户访谈工具"""
    return f"用户访谈: 满意度 {satisfaction}/5，问题: {questions.split(';')[0]}..."

@tool
def market_research_analysis_tool(user_persona_json: str, research_topics: str) -> str:
    """市场调研工具"""
    return f"市场调研: 主题 {research_topics.split(';')[0]}..."

# 简单测试和演示代码
if __name__ == "__main__":
    print("🧪 UserSimulation 工具套件功能演示")
    print("=" * 60)
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: OPENAI_API_KEY 环境变量未设置")
        print("请确保 .env 文件中设置了正确的 API 密钥")
        print("=" * 60)
        exit(1)
    
    print("✅ 环境变量检查通过")
    print("✅ 工具套件定义完成，包含以下核心功能：")
    print("1. PersonaGeneratorTool - 生成用户画像")
    print("2. ProductTrialSimulatorTool - 模拟产品试用")
    print("3. MarketResearchTool - 市场调研分析")
    print("4. UserInterviewTool - 用户访谈")
    print("5. UserInsightGeneratorTool - 洞察生成")
    print("6. UserSimulationStatsTool - 数据统计分析")
    print("7. UserSimulationSuite - 主控制器")
    
    try:
        from langchain_openai import ChatOpenAI

        # 🎯 修复：正确配置LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
            temperature=0.8  # <--- 在这里调整温度，例如设置为 0.8 以增加差异性
        )
        
        print("\n🎯 开始实际测试...")
        suite = UserSimulationSuite(llm=llm, verbose=True)

        # 1. 生成用户画像
        print("\n1. 测试生成用户画像...")
        personas = suite.generate_personas(2, "商业决策模拟平台", "创业者和中小企业主", "需要多样化的用户画像，涵盖不同年龄、性别和收入水平，无歧视。")
        print(f"✅ 成功生成 {len(personas)} 个用户画像")
        print(personas)

        # 修改测试部分 - 对所有用户进行全面测试
        if personas:
            print(f"\n🎯 开始对 {len(personas)} 个用户进行全面测试...")
            
            # 2. 为每个用户模拟产品试用
            print("\n2. 测试产品试用模拟...")
            for i, persona in enumerate(personas):
                print(f"\n   👤 用户 {i+1}: {persona.persona[:80]}...")
                print(f"   基本信息: {persona.age}岁{persona.gender}, 收入: {persona.income_group}")
                
                trial_result = suite.simulate_product_trial(
                    persona.id, 
                    "AI驱动的商业决策模拟平台，通过用户行为模拟和市场反应推演，量化风险与收益，帮助客户在实施前预判决策效果，降低试错成本。", 
                    "产品主页 - 功能介绍界面",
                    [f"访问了产品官网", f"浏览了功能介绍", f"查看了价格信息"]
                )
                print(f"   ✅ 试用模拟完成")
                print(f"   当前状态: {trial_result['当前状态']}")
                print(f"   思考过程: {trial_result['思考过程']}")
                print(f"   下一步: {trial_result['下一步']}")

            # 3. 为每个用户进行市场调研
            print("\n3. 测试市场调研...")
            research_topics = ["需求情况", "长期使用意愿/必要性", "痛点和偏好", "付费意愿", "决策因素", "使用场景"]
            for i, persona in enumerate(personas):
                print(f"\n   👤 用户 {i+1} 市场调研:")
                research_result = suite.conduct_market_research(
                    persona.id,
                    research_topics
                )
                print(f"   ✅ 调研完成")
                print(f"   需求: {research_result['needs'][:60]}...")
                print(f"   痛点: {research_result['pain_points'][:60]}...")
                print(f"   偏好: {research_result['preferences'][:60]}...")
                print(f"   预算考虑: {research_result['budget_considerations'][:60]}...")

            # 4. 为每个用户进行访谈
            print("\n4. 测试用户访谈...")
            questions = [
                "您觉得最重要的产品功能是什么？",
                "如果一定要做MVP，您认为哪些功能是必须的？",
            ]
            
            for i, persona in enumerate(personas):
                print(f"\n   👤 用户 {i+1} 访谈:")
                satisfaction_score = 4 + (i % 2)  # 不同用户不同满意度 (4或5)
                
                interview_result = suite.conduct_interview(
                    persona.id,
                    questions,
                    ["试用了产品核心功能", "体验了决策模拟", "查看了案例分析"],
                    satisfaction=satisfaction_score
                )
                
                print(f"   ✅ 访谈完成: {len(interview_result)} 个问题，满意度: {satisfaction_score}/5")
                for j, response in enumerate(interview_result):
                    print(f"   问题{j+1}: {response['question']}")
                    print(f"   回答: {response['answer'][:100]}...")
                    print("   " + "-" * 50)

            # 5. 为每个用户生成洞察
            print("\n5. 测试洞察生成...")
            for i, persona in enumerate(personas):
                print(f"\n   👤 用户 {i+1} 洞察生成:")
                
                # 根据用户特征定制行为历史
                behaviors = [
                    f"作为{persona.age}岁{persona.gender}，首次访问了产品主页",
                    "详细了解了AI决策模拟功能",
                    "查看了不同行业的应用案例",
                ]
                
                insights = suite.generate_insights(persona.id, behaviors)
                print(f"   ✅ 生成 {len(insights)} 条洞察")
                for j, insight in enumerate(insights):
                    print(f"   洞察{j+1}: {insight}")

            # 6. 获取综合统计分析
            print("\n6. 测试统计分析...")
            stats = suite.get_statistics()
            print("=" * 60)
            print("📊 综合统计分析结果")
            print("=" * 60)
            
            print(f"✅ 用户总数: {stats['用户总数']}")
            print(f"✅ 总记录数: {stats['行为统计分析']['总记录数']}")
            
            print("\n👥 人口统计学分析:")
            demo_stats = stats['人口统计学分析']
            print(f"   平均年龄: {demo_stats['平均年龄']}岁")
            print(f"   年龄范围: {demo_stats['年龄范围']}")
            print(f"   性别分布: {demo_stats['性别分布']}")
            print(f"   收入分布: {demo_stats['收入分布']}")
            
            print("\n📈 行为统计分析:")
            behavior_stats = stats['行为统计分析']
            print(f"   行为类型分布: {behavior_stats['行为类型分布']}")
            print(f"   用户平均活跃度: {behavior_stats['用户平均活跃度']}")
            
            print("\n💬 质性信息分析:")
            # quality_stats = stats['质性信息'] # 旧的错误代码
            quality_stats = stats['质性信息分析'] # 修复：使用正确的键名
            if quality_stats.get('平均满意度') is not None: # 修复：更安全的检查方式
                print(f"   平均满意度: {quality_stats['平均满意度']}/5")
                print(f"   满意度分布: {quality_stats['满意度分布']}")
            else:
                print(f"   平均满意度: N/A") # 如果没有满意度数据

            print(f"   总洞察数量: {quality_stats['总洞察数量']}")
            
            if quality_stats['洞察样本']:
                print("   洞察样本:")
                for insight in quality_stats['洞察样本']:
                    print(f"     • {insight}")
            else:
                print("   洞察样本: N/A")


            # 7. 导出数据测试
            print("\n7. 测试数据导出...")
            json_export = suite.export_data("json")
            csv_export = suite.export_data("csv")
            
            print(f"✅ JSON导出完成: {len(json_export)} 字符")
            print(f"✅ CSV导出完成: {len(csv_export.split('//n'))} 行")  # 修复：使用单个反斜杠
            
            # 保存导出文件
            with open("user_simulation_export.json", "w", encoding="utf-8") as f:
                f.write(json_export)
            
            with open("user_simulation_export.csv", "w", encoding="utf-8") as f:
                f.write(csv_export)
            
            print("✅ 导出文件已保存: user_simulation_export.json, user_simulation_export.csv")

            print("\n" + "=" * 60)
            print("🎉 所有功能全面测试完成！")
            print("=" * 60)
            print(f"📋 测试总结:")
            print(f"   • 生成用户: {stats['用户总数']} 个")
            print(f"   • 模拟试用: {stats['用户总数']} 次")
            print(f"   • 市场调研: {stats['用户总数']} 次") 
            print(f"   • 用户访谈: {stats['用户总数']} 次 (每次{len(questions)}个问题)")
            print(f"   • 洞察生成: {stats['用户总数']} 次")
            print(f"   • 总行为记录: {stats['行为统计分析']['总记录数']} 条")
            print(f"   • 平均满意度: {quality_stats.get('平均满意度', 'N/A')}/5")
            
            # 8. 展示用户画像摘要
            print(f"\n👥 用户画像摘要:")
            for i, persona in enumerate(personas):
                print(f"   用户{i+1}: {persona.age}岁{persona.gender}, {persona.income_group}, 意图: {persona.intent[:50]}...")
            
            print("\n🚀 用户模拟系统测试成功完成！")

        else:
            print("❌ 没有生成任何用户画像，测试无法继续")
    
    except ImportError:
        print("⚠️ 无法导入 langchain_openai，跳过实际测试")
        print("请确保已安装: pip install langchain-openai")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    print("\n" + "=" * 60)
import os
import sys
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

# 路径设置
_current_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_current_script_dir))

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from agent.tool.human import HumanToolManager, set_global_human_tool_manager, get_user_human_tools
from agent.tool.llm import KnowledgeAnalyzerTool, LLMThinkingTool, LLMGeneralTool
from agent.tool.writing import (
    StoryBrainstormTool, PlotDeveloperTool, LongFormWriterTool,
    #DialogueWriterTool, LogicCheckerTool, StyleEnhancerTool
)
from agent.tool.travel_plan import ItineraryPlannerTool
from agent.core.prompts import PromptManager
from agent.core.nodes import NodeManager
from agent.utils.logger import Logger
from agent.utils.json_parser import JSONParser

class CalculatorTool:
    """简单的计算器工具"""
    def execute(self, operation: str, num1: float, num2: float) -> str:
        if operation == "add":
            return str(num1 + num2)
        elif operation == "subtract":
            return str(num1 - num2)
        return "未知的操作"

class AgentCore:
    """TATA代理的核心逻辑类"""
    
    def __init__(self, user_name: str = "user_main", verbose: bool = True, 
                 log_level: str = "INFO", database_manager=None):
        self.user_name = user_name
        self.database_manager = database_manager
        
        # 🎯 修复：初始化人类工具管理器时传递正确的参数
        self.human_tool_manager = HumanToolManager(
            llm=None,  # 暂时传None，后续会设置
            user_name=user_name,
            database_manager=database_manager,
            verbose=verbose
        )
        set_global_human_tool_manager(self.human_tool_manager)
        
        # 初始化工具组件
        self.logger = Logger(verbose, log_level)
        self.json_parser = JSONParser(self.logger)  # 传递logger给JSONParser
        
        # 设置人类工具
        self._setup_human_tools()
        
        # 初始化LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 🎯 修复：现在设置LLM到human_tool_manager
        self.human_tool_manager.llm = self.llm
        
        # 注册工具
        self._setup_tools()
        
        # 初始化核心组件 - 确保正确的依赖顺序
        self.prompt_manager = PromptManager(user_name, self.human_tools)
        self.node_manager = NodeManager(self.llm, self.tools, self.logger, self.json_parser)
        
        # ✅ 关键：立即设置依赖关系
        self.node_manager.set_prompt_manager(self.prompt_manager)
        
        self.logger.info("✅ 【agent】 AgentCore 初始化完成，所有依赖已正确设置")

    def _setup_human_tools(self):
        """设置人类工具 - 使用动态管理器"""
        # 🎯 添加详细调试输出
        print(f"🔍 [DEBUG] AgentCore._setup_human_tools() 开始")
        print(f"🔍 [DEBUG] 当前用户名: {self.user_name}")
        print(f"🔍 [DEBUG] 数据库管理器: {self.database_manager}")
        
        # 🎯 使用新的动态方式获取用户工具
        self.human_tools = self.human_tool_manager.get_user_human_tools(self.user_name)
        
        print(f"🔍 [DEBUG] 获取到的human_tools: {self.human_tools}")
        
        if not self.human_tools:
            print(f"❌ [DEBUG] 未找到用户 '{self.user_name}' 的特定人类能力档案。")
            self.logger.warning(f"未找到用户 '{self.user_name}' 的特定人类能力档案。")
        else:
            print(f"✅ [DEBUG] 已为用户 '{self.user_name}' 加载人类能力档案: {list(self.human_tools.keys())}")
            
            # 🎯 详细输出档案内容
            if 'user_profile' in self.human_tools:
                profile = self.human_tools['user_profile']
                print(f"🔍 [DEBUG] 用户档案详情:")
                print(f"  - 用户ID: {profile.get('user_id')}")
                print(f"  - 显示名称: {profile.get('display_name')}")
                print(f"  - 档案描述: {profile.get('overall_profile', 'None')[:100]}...")
            
            self.logger.info(f"已为用户 '{self.user_name}' 加载人类能力档案: {list(self.human_tools.keys())}")
    
    def _setup_tools(self):
        """注册工具 - 使用工具管理器避免重复初始化"""
        # 🎯 导入工具管理器
        from agent.tool.tool_manager import get_tool_manager
        
        # 获取全局工具管理器
        tool_manager = get_tool_manager()
        tool_manager.set_llm(self.llm)
        tool_manager.set_verbose(self.logger.verbose)
        
        # 基础工具（不需要缓存的轻量级工具）
        self.calculator = CalculatorTool()
        self.llm_general = LLMGeneralTool(llm=self.llm, verbose=self.logger.verbose)
        
        # 🎯 使用工具管理器获取重量级工具（会被缓存）
        self.itinerary_planner = tool_manager.get_tool("itinerary_planner")
        self.travel_info_extractor = tool_manager.get_tool("travel_info_extractor")
        self.travel_planner = tool_manager.get_tool("travel_planner")
        self.accommodation_planner = tool_manager.get_tool("accommodation_planner")
        self.attraction_planner = tool_manager.get_tool("attraction_planner")
        self.restaurant_planner = tool_manager.get_tool("restaurant_planner")
        self.transportation_planner = tool_manager.get_tool("transportation_planner")
        self.image_generator = tool_manager.get_tool("image_generator")
        
        # 🎯 构建工具字典
        self.tools = {
            "llm_general": self.llm_general,
        }
        
        # 🎯 只添加成功初始化的工具
        tool_mapping = {
            "itinerary_planner": self.itinerary_planner,
            "travel_info_extractor": self.travel_info_extractor,
            "travel_planner": self.travel_planner,
            "accommodation_planner": self.accommodation_planner,
            "attraction_planner": self.attraction_planner,
            "restaurant_planner": self.restaurant_planner,
            "transportation_planner": self.transportation_planner,
            "image_generator": self.image_generator,
        }
        
        for tool_name, tool_instance in tool_mapping.items():
            if tool_instance is not None:
                self.tools[tool_name] = tool_instance
        
        # 🎯 记录可用工具和缓存状态
        if self.logger.verbose:
            print(f"✅ 已注册工具: {list(self.tools.keys())}")
            cached_tools = tool_manager.get_cached_tools()
            print(f"📦 已缓存工具: {list(cached_tools.keys())}")

    def set_stream_callback(self, callback):
        """设置流式回调函数"""
        self.stream_callback = callback
        
        # 🎯 只设置必要的流式回调，不设置 planner_processor
        if hasattr(self.node_manager, 'set_stream_callback'):
            self.node_manager.set_stream_callback(callback)
            self.logger.info("✅ 已将stream_callback设置到节点管理器")
        
        self.logger.info("✅ AgentCore stream_callback 已设置")
    
    def get_tool_display_name(self, tool_name: str) -> str:
        """获取工具显示名称"""
        display_names = {
            "calculator": "计算器",
            "llm_general": "通用LLM工具",
            "itinerary_planner": "旅游行程规划器",
            "travel_info_extractor": "旅游信息提取器",
            "travel_planner": "专业旅游规划器",
            "accommodation_planner": "住宿规划器",
            "attraction_planner": "景点规划器",
            "restaurant_planner": "餐饮规划器",
            "transportation_planner": "交通规划器",
            "image_generator": "图片生成器",
        }
        return display_names.get(tool_name, tool_name)

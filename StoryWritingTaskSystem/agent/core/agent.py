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
from agent.tool.creative_guide import CreativeGuideTool
from agent.tool.material_collector import MaterialCollectorTool
from agent.tool.theme_focuser import ThemeFocuserTool
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
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2,max_retries=3,request_timeout=40)
        
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
                overall_profile = profile.get('overall_profile', 'None') or '暂无档案描述'
                print(f"  - 档案描述: {overall_profile[:100]}...")
            
            self.logger.info(f"已为用户 '{self.user_name}' 加载人类能力档案: {list(self.human_tools.keys())}")
    
    def _setup_tools(self):
        """注册工具 - 包含通用工具和专业创意写作工具"""
        self.calculator = CalculatorTool()
        self.llm_general = LLMGeneralTool(llm=self.llm, verbose=self.logger.verbose)
        
        # 🎯 添加专业化创意写作工具（按阶段分工）
        
        # 阶段1: 故事规划器
        try:
            from agent.tool.story_planner import StoryPlannerTool
            self.story_planner = StoryPlannerTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 故事规划器初始化成功")
        except Exception as e:
            print(f"⚠️ 故事规划器初始化失败: {e}")
            self.story_planner = None
        
        # 阶段2: 内容写作器
        try:
            from agent.tool.content_writer import ContentWriterTool
            self.content_writer = ContentWriterTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 内容写作器初始化成功")
        except Exception as e:
            print(f"⚠️ 内容写作器初始化失败: {e}")
            self.content_writer = None
        
        # 阶段3: 故事精炼器
        try:
            from agent.tool.story_refiner import StoryRefinerTool
            self.story_refiner = StoryRefinerTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 故事精炼器初始化成功")
        except Exception as e:
            print(f"⚠️ 故事精炼器初始化失败: {e}")
            self.story_refiner = None
        
        # 辅助工具: 角色构建器
        try:
            from agent.tool.character_builder import CharacterBuilderTool
            self.character_builder = CharacterBuilderTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 角色构建器初始化成功")
        except Exception as e:
            print(f"⚠️ 角色构建器初始化失败: {e}")
            self.character_builder = None
        
        # 辅助工具: 场景构建器
        try:
            from agent.tool.scene_builder import SceneBuilderTool
            self.scene_builder = SceneBuilderTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 场景构建器初始化成功")
        except Exception as e:
            print(f"⚠️ 场景构建器初始化失败: {e}")
            self.scene_builder = None
        
        # 辅助工具: 情节推进器
        try:
            from agent.tool.plot_developer import PlotDeveloperTool
            self.plot_developer = PlotDeveloperTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 情节推进器初始化成功")
        except Exception as e:
            print(f"⚠️ 情节推进器初始化失败: {e}")
            self.plot_developer = None
        
        # 辅助工具: 规划分析器
        try:
            from agent.tool.plan_analyzer import PlanAnalyzerTool
            self.plan_analyzer = PlanAnalyzerTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 规划分析器初始化成功")
        except Exception as e:
            print(f"⚠️ 规划分析器初始化失败: {e}")
            self.plan_analyzer = None
        
        # 🎯 添加CPS创作流程工具
        try:
            self.creative_guide = CreativeGuideTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 创意引导工具初始化成功")
        except Exception as e:
            print(f"⚠️ 创意引导工具初始化失败: {e}")
            self.creative_guide = None
        
        try:
            self.material_collector = MaterialCollectorTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 素材收集工具初始化成功")
        except Exception as e:
            print(f"⚠️ 素材收集工具初始化失败: {e}")
            self.material_collector = None
            
        try:
            self.theme_focuser = ThemeFocuserTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 主题聚焦工具初始化成功")
        except Exception as e:
            print(f"⚠️ 主题聚焦工具初始化失败: {e}")
            self.theme_focuser = None
        
        # 🎯 新增：头脑风暴工具
        try:
            from agent.tool.brainstorm_tool import BrainstormTool
            self.brainstorm_tool = BrainstormTool(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 头脑风暴工具初始化成功")
        except Exception as e:
            print(f"⚠️ 头脑风暴工具初始化失败: {e}")
            self.brainstorm_tool = None
        
        # 🎯 新增：多角度分析工具
        try:
            from agent.tool.perspective_analyzer import PerspectiveAnalyzer
            self.perspective_analyzer = PerspectiveAnalyzer(llm=self.llm, verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 多角度分析工具初始化成功")
        except Exception as e:
            print(f"⚠️ 多角度分析工具初始化失败: {e}")
            self.perspective_analyzer = None
        
        # 🎯 添加图片生成工具
        try:
            from agent.tool.image import ImageGeneratorTool
            self.image_generator = ImageGeneratorTool(verbose=self.logger.verbose)
            if self.logger.verbose:
                print("✅ 图片生成工具初始化成功")
        except Exception as e:
            print(f"⚠️ 图片生成工具初始化失败: {e}")
            self.image_generator = None
        
        # 🎯 更新工具字典 - 确保所有工具都被注册
        self.tools = {
            "llm_general": self.llm_general,
        }
        
        # 🎯 添加专业化创意写作工具
        if self.story_planner:
            self.tools["story_planner"] = self.story_planner
        
        if self.content_writer:
            self.tools["content_writer"] = self.content_writer
            
        if self.story_refiner:
            self.tools["story_refiner"] = self.story_refiner
        
        # 🎯 添加辅助创意写作工具
        if self.character_builder:
            self.tools["character_builder"] = self.character_builder
        
        if self.scene_builder:
            self.tools["scene_builder"] = self.scene_builder
            
        if self.plot_developer:
            self.tools["plot_developer"] = self.plot_developer
        
        if self.plan_analyzer:
            self.tools["plan_analyzer"] = self.plan_analyzer
        
        # 🎯 添加CPS创作流程工具
        if self.creative_guide:
            self.tools["creative_guide"] = self.creative_guide
        
        if self.material_collector:
            self.tools["material_collector"] = self.material_collector
            
        if self.theme_focuser:
            self.tools["theme_focuser"] = self.theme_focuser
        
        # 🎯 添加新的第一阶段工具
        if self.brainstorm_tool:
            self.tools["brainstorm_tool"] = self.brainstorm_tool
            
        if self.perspective_analyzer:
            self.tools["perspective_analyzer"] = self.perspective_analyzer
        
        # 🎯 只有在图片工具可用时才添加
        if self.image_generator:
            self.tools["image_generator"] = self.image_generator
        
        # 🎯 新增：记录可用工具
        if self.logger.verbose:
            print(f"✅ 已注册工具: {list(self.tools.keys())}")

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
            "story_writer": "故事写作工具",
            "character_creator": "角色创建工具",
            "scene_generator": "场景生成工具",
            "image_generator": "图片生成器",
        }
        return display_names.get(tool_name, tool_name)

"""
工具管理器 - 实现单例模式和懒加载，避免重复初始化
"""
import os
import sys
from typing import Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel


class ToolManager:
    """工具管理器 - 单例模式，避免重复初始化工具"""
    
    _instance = None
    _tools_cache = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.verbose = False
            self.llm = None
            ToolManager._initialized = True
    
    def set_llm(self, llm: BaseChatModel):
        """设置LLM实例"""
        self.llm = llm
    
    def set_verbose(self, verbose: bool):
        """设置详细输出模式"""
        self.verbose = verbose
    
    def get_tool(self, tool_name: str, **kwargs):
        """
        获取工具实例 - 使用缓存避免重复初始化
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具初始化参数
        """
        # 如果工具已经在缓存中，直接返回
        if tool_name in self._tools_cache:
            if self.verbose:
                print(f"✅ [ToolManager] 从缓存获取工具: {tool_name}")
            return self._tools_cache[tool_name]
        
        # 否则创建新的工具实例
        if self.verbose:
            print(f"🔄 [ToolManager] 初始化新工具: {tool_name}")
        
        tool_instance = self._create_tool(tool_name, **kwargs)
        
        if tool_instance is not None:
            # 缓存工具实例
            self._tools_cache[tool_name] = tool_instance
            if self.verbose:
                print(f"✅ [ToolManager] 工具已缓存: {tool_name}")
        
        return tool_instance
    
    def _create_tool(self, tool_name: str, **kwargs):
        """创建工具实例"""
        try:
            if tool_name == "itinerary_planner":
                from agent.tool.travel_plan import ItineraryPlannerTool
                return ItineraryPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "travel_info_extractor":
                from agent.tool.travel_info_extractor import TravelInfoExtractorTool
                return TravelInfoExtractorTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "travel_planner":
                from agent.tool.travel_planner import TravelPlannerTool
                return TravelPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "accommodation_planner":
                from agent.tool.accommodation_planner import AccommodationPlannerTool
                return AccommodationPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "attraction_planner":
                from agent.tool.attraction_planner import AttractionPlannerTool
                return AttractionPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "restaurant_planner":
                from agent.tool.restaurant_planner import RestaurantPlannerTool
                return RestaurantPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "transportation_planner":
                from agent.tool.transportation_planner import TransportationPlannerTool
                return TransportationPlannerTool(llm=self.llm, verbose=self.verbose)
            
            elif tool_name == "image_generator":
                from agent.tool.image import ImageGeneratorTool
                return ImageGeneratorTool(verbose=self.verbose)
            
            else:
                if self.verbose:
                    print(f"⚠️ [ToolManager] 未知工具类型: {tool_name}")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"❌ [ToolManager] 创建工具失败 {tool_name}: {e}")
            return None
    
    def clear_cache(self):
        """清空工具缓存 - 用于测试或重置"""
        if self.verbose:
            print("🗑️ [ToolManager] 清空工具缓存")
        self._tools_cache.clear()
    
    def get_cached_tools(self) -> Dict[str, Any]:
        """获取已缓存的工具列表"""
        return dict(self._tools_cache)
    
    def is_tool_cached(self, tool_name: str) -> bool:
        """检查工具是否已缓存"""
        return tool_name in self._tools_cache


# 全局工具管理器实例
_global_tool_manager = None

def get_tool_manager() -> ToolManager:
    """获取全局工具管理器实例"""
    global _global_tool_manager
    if _global_tool_manager is None:
        _global_tool_manager = ToolManager()
    return _global_tool_manager

def clear_tool_cache():
    """清空全局工具缓存"""
    global _global_tool_manager
    if _global_tool_manager is not None:
        _global_tool_manager.clear_cache()
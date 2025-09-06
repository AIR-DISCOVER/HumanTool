"""
性能测试脚本 - 测试工具初始化优化效果
"""
import time
import sys
import os
from typing import Dict, Any

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_old_initialization():
    """测试旧的初始化方式（直接创建工具）"""
    print("🔄 测试旧的初始化方式...")
    start_time = time.time()
    
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 直接创建工具（模拟旧方式）
        from agent.tool.accommodation_planner import AccommodationPlannerTool
        from agent.tool.attraction_planner import AttractionPlannerTool
        from agent.tool.restaurant_planner import RestaurantPlannerTool
        
        tools = []
        tools.append(AccommodationPlannerTool(llm=llm, verbose=False))
        tools.append(AttractionPlannerTool(llm=llm, verbose=False))
        tools.append(RestaurantPlannerTool(llm=llm, verbose=False))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 旧方式初始化完成: {duration:.3f}秒")
        return duration, len(tools)
        
    except Exception as e:
        print(f"❌ 旧方式初始化失败: {e}")
        return None, 0

def test_new_initialization():
    """测试新的初始化方式（使用工具管理器）"""
    print("🔄 测试新的初始化方式...")
    start_time = time.time()
    
    try:
        from langchain_openai import ChatOpenAI
        from agent.tool.tool_manager import get_tool_manager
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 使用工具管理器
        tool_manager = get_tool_manager()
        tool_manager.set_llm(llm)
        tool_manager.set_verbose(False)
        
        tools = []
        tools.append(tool_manager.get_tool("accommodation_planner"))
        tools.append(tool_manager.get_tool("attraction_planner"))
        tools.append(tool_manager.get_tool("restaurant_planner"))
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 新方式初始化完成: {duration:.3f}秒")
        return duration, len(tools)
        
    except Exception as e:
        print(f"❌ 新方式初始化失败: {e}")
        return None, 0

def test_repeated_initialization():
    """测试重复初始化的性能差异"""
    print("\n🔄 测试重复初始化性能...")
    
    # 测试新方式的重复初始化
    print("测试新方式重复初始化（应该使用缓存）...")
    times = []
    
    for i in range(3):
        start_time = time.time()
        
        try:
            from langchain_openai import ChatOpenAI
            from agent.tool.tool_manager import get_tool_manager
            
            llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
            tool_manager = get_tool_manager()
            tool_manager.set_llm(llm)
            tool_manager.set_verbose(True)  # 显示缓存信息
            
            # 重复获取工具
            tool_manager.get_tool("accommodation_planner")
            tool_manager.get_tool("attraction_planner")
            tool_manager.get_tool("restaurant_planner")
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"  第{i+1}次: {duration:.3f}秒")
            
        except Exception as e:
            print(f"❌ 第{i+1}次初始化失败: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"✅ 平均时间: {avg_time:.3f}秒")
        return avg_time
    
    return None

def test_data_loading():
    """测试数据加载性能"""
    print("\n🔄 测试数据加载性能...")
    
    try:
        from agent.tool.data_manager import get_data_manager
        
        data_manager = get_data_manager()
        data_manager.set_verbose(True)
        
        # 测试首次加载
        print("首次数据加载:")
        start_time = time.time()
        
        accommodations = data_manager.get_data('accommodations')
        attractions = data_manager.get_data('attractions')
        restaurants = data_manager.get_data('restaurants')
        
        end_time = time.time()
        first_load_time = end_time - start_time
        
        print(f"✅ 首次加载时间: {first_load_time:.3f}秒")
        
        # 测试缓存加载
        print("\n缓存数据加载:")
        start_time = time.time()
        
        accommodations = data_manager.get_data('accommodations')
        attractions = data_manager.get_data('attractions')
        restaurants = data_manager.get_data('restaurants')
        
        end_time = time.time()
        cached_load_time = end_time - start_time
        
        print(f"✅ 缓存加载时间: {cached_load_time:.3f}秒")
        
        # 显示缓存信息
        cached_info = data_manager.get_cached_data_info()
        print(f"📦 缓存数据信息: {cached_info}")
        
        return first_load_time, cached_load_time
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")
        return None, None

def main():
    """主测试函数"""
    print("🚀 开始性能测试...")
    print("=" * 50)
    
    # 测试初始化性能
    old_time, old_count = test_old_initialization()
    print()
    new_time, new_count = test_new_initialization()
    
    if old_time and new_time:
        improvement = ((old_time - new_time) / old_time) * 100
        print(f"\n📊 初始化性能对比:")
        print(f"  旧方式: {old_time:.3f}秒")
        print(f"  新方式: {new_time:.3f}秒")
        print(f"  性能提升: {improvement:.1f}%")
    
    # 测试重复初始化
    repeat_time = test_repeated_initialization()
    
    # 测试数据加载
    first_load, cached_load = test_data_loading()
    
    if first_load and cached_load:
        cache_improvement = ((first_load - cached_load) / first_load) * 100
        print(f"\n📊 数据加载性能对比:")
        print(f"  首次加载: {first_load:.3f}秒")
        print(f"  缓存加载: {cached_load:.3f}秒")
        print(f"  缓存提升: {cache_improvement:.1f}%")
    
    print("\n✅ 性能测试完成!")

if __name__ == "__main__":
    main()
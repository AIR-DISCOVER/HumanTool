#!/usr/bin/env python3
"""
旅游规划工具测试脚本
"""

import os
import sys
import json
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# 🎯 加载环境变量 - 从TravelPlanner目录
from dotenv import load_dotenv

# 尝试多个可能的.env文件位置
possible_env_paths = [
    os.path.join(project_root, 'agent', 'TravelPlanner', '.env'),
    os.path.join(project_root, 'TravelPlanner', '.env'),
    os.path.join(project_root, '.env'),
    os.path.join(current_dir, '.env')
]

env_loaded = False
for env_path in possible_env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 加载环境变量从: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("⚠️ 未找到.env文件，使用默认环境变量加载")
    load_dotenv()

from langchain_openai import ChatOpenAI
from agent.tool.travel_info_extractor import TravelInfoExtractorTool
from agent.tool.travel_planner import TravelPlannerTool
from agent.tool.travel_plan import ItineraryPlannerTool

def test_travel_info_extractor():
    """测试旅游信息提取工具"""
    print("=" * 80)
    print("测试旅游信息提取工具")
    print("=" * 80)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2,max_retries=3,request_timeout=40)
        
        # 创建信息提取工具
        extractor = TravelInfoExtractorTool(llm=llm, verbose=True)
        
        # 测试用例1：获取数据摘要
        print("\n【测试1】获取数据集摘要")
        result1 = extractor.execute(
            query_type="summary",
            analysis_focus="提供旅游数据的整体概览"
        )
        print("结果:", result1[:300] + "..." if len(result1) > 300 else result1)
        
        # 测试用例2：按目的地筛选
        print("\n【测试2】按目的地筛选信息")
        result2 = extractor.execute(
            query_type="by_destination",
            max_items=3,
            filter_criteria={"destination": "Virginia"},
            analysis_focus="为Virginia旅行提供整体概览"
        )
        print("结果:", result2[:300] + "..." if len(result2) > 300 else result2)
        
        # 测试用例3：按预算筛选
        print("\n【测试3】按预算筛选信息")
        result3 = extractor.execute(
            query_type="by_budget",
            max_items=3,
            filter_criteria={"budget_range": [1000, 2000]},
            analysis_focus="中等预算旅行规划参考"
        )
        print("结果:", result3[:300] + "..." if len(result3) > 300 else result3)
        
        print("✅ 旅游信息提取工具测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 旅游信息提取工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_travel_planner():
    """测试旅游规划工具"""
    print("=" * 80)
    print("测试旅游规划工具")
    print("=" * 80)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 创建旅游规划工具
        planner = TravelPlannerTool(llm=llm, verbose=True)
        
        # 测试用例1：使用LLM通用规划
        print("\n【测试1】LLM通用规划")
        result1 = planner.execute(
            task_description="计划一个7天的Virginia旅行，预算$1800，从Philadelphia出发",
            strategy="direct",
            destination="Virginia",
            trip_duration="7天",
            budget_range="$1800"
        )
        print("结果:", result1[:500] + "..." if len(result1) > 500 else result1)
        
        # 测试用例2：验证查询
        print("\n【测试2】查询验证")
        valid, msg = planner.validate_query("计划一个旅行")
        print(f"查询验证结果: {valid}, 消息: {msg}")
        
        # 测试用例3：获取可用策略
        print("\n【测试3】获取可用策略")
        strategies = planner.get_available_strategies()
        print(f"可用策略: {strategies}")
        
        print("✅ 旅游规划工具测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 旅游规划工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_itinerary_planner():
    """测试高级行程规划工具"""
    print("=" * 80)
    print("测试高级行程规划工具")
    print("=" * 80)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 创建高级行程规划工具
        planner = ItineraryPlannerTool(llm=llm, verbose=True)
        
        # 测试用例1：综合规划（包含数据提取）
        print("\n【测试1】综合旅游规划")
        result1 = planner.execute(
            task_description="我想计划一个从Philadelphia到Virginia的7天旅行，预算$1800",
            destination="Virginia",
            trip_duration="7天",
            budget_range="$1800",
            planning_style="balanced",
            use_reference_data=True,
            planning_strategy="direct"
        )
        print("结果:", result1[:500] + "..." if len(result1) > 500 else result1)
        
        # 测试用例2：不使用参考数据的规划
        print("\n【测试2】基础规划（无参考数据）")
        result2 = planner.execute(
            task_description="计划一个3天的纽约之旅",
            destination="New York",
            trip_duration="3天",
            budget_range="$1000",
            planning_style="packed",
            use_reference_data=False
        )
        print("结果:", result2[:300] + "..." if len(result2) > 300 else result2)
        
        print("✅ 高级行程规划工具测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 高级行程规划工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """集成测试：测试工具的协同工作"""
    print("=" * 80)
    print("集成测试：工具协同工作")
    print("=" * 80)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 创建所有工具
        extractor = TravelInfoExtractorTool(llm=llm, verbose=True)
        planner = TravelPlannerTool(llm=llm, verbose=True)
        itinerary_planner = ItineraryPlannerTool(llm=llm, verbose=True)
        
        # 步骤1：提取参考信息
        print("\n【步骤1】提取参考信息")
        ref_info = extractor.execute(
            query_type="by_destination",
            max_items=2,
            filter_criteria={"destination": "Texas"},
            analysis_focus="为Texas旅行提供参考信息"
        )
        
        # 步骤2：使用参考信息进行规划
        print("\n【步骤2】基于参考信息进行规划")
        plan_result = planner.execute(
            task_description="计划一个5天的Texas旅行，预算$1500",
            strategy="direct",
            reference_data=ref_info
        )
        
        # 步骤3：使用高级规划器
        print("\n【步骤3】使用高级规划器进行综合规划")
        final_result = itinerary_planner.execute(
            task_description="我想要一个详细的Texas旅行计划",
            destination="Texas",
            trip_duration="5天",
            budget_range="$1500",
            use_reference_data=True
        )
        
        print(f"最终规划结果长度: {len(final_result)} 字符")
        print("✅ 集成测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """检查现有数据文件，不创建新的示例数据"""
    print("=" * 80)
    print("检查现有数据文件")
    print("=" * 80)
    
    # 🎯 使用实际的数据文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_file = os.path.join(project_root, 'agent', 'TravelPlanner', 'TravelPlan', 'local_validation_data.json')
    
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 找到现有数据文件: {data_file}")
            print(f"✅ 包含 {len(data)} 条旅游查询数据")
            
            # 显示数据示例
            if data:
                first_item = data[0]
                print(f"✅ 数据结构示例:")
                print(f"   - idx: {first_item.get('idx', 'N/A')}")
                print(f"   - query: {first_item.get('query', '')[:100]}...")
                print(f"   - reference_information: {'是' if first_item.get('reference_information') else '否'}")
            
            return data_file
            
        except Exception as e:
            print(f"❌ 读取数据文件失败: {e}")
            return None
    else:
        print(f"❌ 数据文件不存在: {data_file}")
        print("请确保 TravelPlanner 目录结构正确")
        return None

def test_with_real_data():
    """使用真实数据进行测试"""
    print("=" * 80)
    print("使用真实数据测试")
    print("=" * 80)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # 创建信息提取工具
        extractor = TravelInfoExtractorTool(llm=llm, verbose=True)
        
        # 加载实际数据
        data = extractor._load_local_data()
        if not data:
            print("❌ 无法加载实际数据")
            return False
        
        print(f"✅ 加载了 {len(data)} 条真实数据")
        
        # 测试第一个查询的规划
        if data:
            first_query = data[0]
            print(f"\n【使用第一个真实查询进行测试】")
            print(f"Query: {first_query.get('query', '')}")
            
            # 创建旅游规划工具
            planner = TravelPlannerTool(llm=llm, verbose=True)
            
            # 执行规划
            result = planner.execute(
                task_description=first_query.get('query', ''),
                strategy="direct"
            )
            
            print(f"规划结果长度: {len(result)} 字符")
            print("✅ 真实数据测试完成")
            
        return True
        
    except Exception as e:
        print(f"❌ 真实数据测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """检查环境配置"""
    print("=" * 80)
    print("检查环境配置")
    print("=" * 80)
    
    # 检查OpenAI API Key
    openai_key = os.getenv('OPENAI_API_KEY')
    openai_base = os.getenv('OPENAI_API_BASE')
    
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-10:] if len(openai_key) > 20 else openai_key}")
    else:
        print("❌ OPENAI_API_KEY 未设置")
        return False
        
    if openai_base:
        print(f"✅ OPENAI_API_BASE: {openai_base}")
    else:
        print("⚠️ OPENAI_API_BASE 未设置，将使用默认值")
    
    # 检查Google API Key (可选)
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"✅ GOOGLE_API_KEY: {google_key}")
    else:
        print("⚠️ GOOGLE_API_KEY 未设置")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始旅游规划工具测试")
    print("=" * 80)
    
    # 检查环境变量
    if not check_environment():
        print("\n❌ 环境配置检查失败，请检查.env文件设置")
        print("\n可能的解决方案:")
        print("1. 确保.env文件存在于以下位置之一:")
        for env_path in possible_env_paths:
            print(f"   - {env_path}")
        print("2. 确保.env文件包含以下内容:")
        print("   OPENAI_API_KEY=your_openai_api_key")
        print("   OPENAI_API_BASE=your_openai_api_base (可选)")
        print("   GOOGLE_API_KEY=your_google_api_key (可选)")
        return
    
    # 🎯 检查现有数据而不是创建示例数据
    data_file = create_sample_data()
    if not data_file:
        print("❌ 无法找到数据文件，测试终止")
        return
    
    # 运行测试
    tests = [
        # ("信息提取工具测试", test_travel_info_extractor),
        ("旅游规划工具测试", test_travel_planner),
        # ("高级行程规划工具测试", test_itinerary_planner),
        # ("真实数据测试", test_with_real_data),  # 🎯 新增真实数据测试
        # ("集成测试", test_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 开始测试: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results[test_name] = False
    
    # 输出测试总结
    print("\n" + "=" * 80)
    print("🏁 测试总结")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️ 某些测试失败，请检查错误信息")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
调试TravelPlanner检索过程的脚本
用于追踪"纽约"问题的根本原因
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from agent.tool.travel_planner import TravelPlannerTool

class MockLLM:
    """模拟LLM用于测试"""
    def invoke(self, messages):
        class MockResponse:
            def __init__(self):
                self.content = "Mock LLM response for testing"
        return MockResponse()

def test_travel_planner_retrieval():
    """测试TravelPlanner的检索过程"""
    print("🚀 开始调试TravelPlanner检索过程")
    print("="*80)
    
    # 创建TravelPlanner实例（启用详细输出）
    mock_llm = MockLLM()
    planner = TravelPlannerTool(llm=mock_llm, verbose=True)
    
    # 测试查询：伊萨卡到纽瓦克
    test_query = "Can you design a 3-day travel itinerary for 2 people, departing from Ithaca and heading to Newark from March 18th to March 20th, 2022? Our budget is set at $1,200, and we require our accommodations to be entire rooms and visitor-friendly. Please note that we prefer not to drive ourselves during this trip."
    
    print(f"🎯 测试查询: {test_query}")
    print("="*80)
    
    # 调用检索方法（这会触发详细的调试输出）
    reference_data = planner._get_local_reference_data(test_query)
    
    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80)
    if reference_data:
        print(f"✅ 返回了参考数据 (长度: {len(reference_data)})")
        print("前500字符预览:")
        print(reference_data[:500] + "..." if len(reference_data) > 500 else reference_data)
    else:
        print("❌ 未返回参考数据")
    print("="*80)

def analyze_data_structure():
    """分析数据文件结构"""
    print("\n🔍 分析数据文件结构")
    print("="*80)
    
    # 数据文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    data_path = os.path.join(project_root, 'agent', 'TravelPlanner', 'TravelPlan', 'local_validation_data.json')
    
    print(f"数据文件路径: {data_path}")
    print(f"文件存在: {os.path.exists(data_path)}")
    
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"数据项总数: {len(data)}")
        
        # 分析前几个数据项
        for i, item in enumerate(data[:5]):  # 只看前5个
            idx = item.get('idx', 'N/A')
            query = item.get('query', '')
            print(f"\n--- 数据项 {i+1} (idx={idx}) ---")
            print(f"查询: {query[:100]}...")
            
            # 检查reference_information
            ref_info = item.get('reference_information', '')
            if isinstance(ref_info, str):
                print(f"参考信息类型: string (长度: {len(ref_info)})")
                # 检查是否包含纽约相关信息
                if 'new york' in ref_info.lower() or 'manhattan' in ref_info.lower() or 'brooklyn' in ref_info.lower():
                    print("⚠️  包含纽约相关信息!")
            else:
                print(f"参考信息类型: {type(ref_info)}")
                # 如果是列表，检查每个项目
                if isinstance(ref_info, list):
                    for j, ref_item in enumerate(ref_info):
                        if isinstance(ref_item, dict):
                            content = ref_item.get('Content', '')
                            if 'new york' in content.lower() or 'manhattan' in content.lower() or 'brooklyn' in content.lower():
                                print(f"⚠️  参考项 {j+1} 包含纽约相关信息!")
                                print(f"    描述: {ref_item.get('Description', 'N/A')}")

if __name__ == "__main__":
    print("🔧 TravelPlanner调试工具")
    print("="*80)
    
    # 首先分析数据结构
    analyze_data_structure()
    
    # 然后测试检索过程
    test_travel_planner_retrieval()
    
    print("\n✅ 调试完成")
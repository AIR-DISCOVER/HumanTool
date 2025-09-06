# 创建文件: c:\AIRelief\HUMANTOOL\TATA\agent\TravelPlanner\tools\planner\env.py

import os
import json
import re
from typing import Dict, Any, List

class ReactEnv:
    """ReAct环境类 - 用于处理旅行规划的成本计算和验证"""
    
    def __init__(self):
        self.state = "initialized"
        self.step_count = 0
        self.max_steps = 30
        self.terminated = False
        
    def run(self, plan_dict: Dict[str, Any]) -> str:
        """
        执行旅行计划的成本计算
        
        Args:
            plan_dict: 包含旅行计划的字典
            
        Returns:
            str: 计算出的成本信息
        """
        try:
            self.step_count += 1
            
            # 基础成本计算逻辑
            total_cost = 0.0
            
            # 解析计划中的各项费用
            if isinstance(plan_dict, dict):
                # 交通费用
                if 'transportation' in plan_dict:
                    total_cost += self._calculate_transportation_cost(plan_dict['transportation'])
                
                # 住宿费用
                if 'accommodation' in plan_dict:
                    total_cost += self._calculate_accommodation_cost(plan_dict['accommodation'])
                
                # 餐饮费用
                if 'dining' in plan_dict:
                    total_cost += self._calculate_dining_cost(plan_dict['dining'])
                
                # 景点门票费用
                if 'attractions' in plan_dict:
                    total_cost += self._calculate_attraction_cost(plan_dict['attractions'])
                
                # 如果没有具体分类，尝试解析整体计划
                if not any(key in plan_dict for key in ['transportation', 'accommodation', 'dining', 'attractions']):
                    total_cost = self._estimate_general_cost(plan_dict)
            
            # 检查是否达到终止条件
            if self.step_count >= self.max_steps:
                self.terminated = True
            
            return f"The total cost is approximately ${total_cost:.2f}."
            
        except Exception as e:
            print(f"Error in ReactEnv.run: {e}")
            return "Unable to calculate cost due to an error."
    
    def _calculate_transportation_cost(self, transport_info) -> float:
        """计算交通费用"""
        if isinstance(transport_info, (int, float)):
            return float(transport_info)
        elif isinstance(transport_info, str):
            # 尝试从字符串中提取数字
            numbers = re.findall(r'\d+\.?\d*', transport_info)
            return sum(float(n) for n in numbers) if numbers else 200.0
        return 200.0  # 默认交通费用
    
    def _calculate_accommodation_cost(self, accommodation_info) -> float:
        """计算住宿费用"""
        if isinstance(accommodation_info, (int, float)):
            return float(accommodation_info)
        elif isinstance(accommodation_info, str):
            numbers = re.findall(r'\d+\.?\d*', accommodation_info)
            return sum(float(n) for n in numbers) if numbers else 300.0
        return 300.0  # 默认住宿费用
    
    def _calculate_dining_cost(self, dining_info) -> float:
        """计算餐饮费用"""
        if isinstance(dining_info, (int, float)):
            return float(dining_info)
        elif isinstance(dining_info, str):
            numbers = re.findall(r'\d+\.?\d*', dining_info)
            return sum(float(n) for n in numbers) if numbers else 150.0
        return 150.0  # 默认餐饮费用
    
    def _calculate_attraction_cost(self, attraction_info) -> float:
        """计算景点费用"""
        if isinstance(attraction_info, (int, float)):
            return float(attraction_info)
        elif isinstance(attraction_info, str):
            numbers = re.findall(r'\d+\.?\d*', attraction_info)
            return sum(float(n) for n in numbers) if numbers else 100.0
        return 100.0  # 默认景点费用
    
    def _estimate_general_cost(self, plan_dict: Dict) -> float:
        """对一般计划进行成本估算"""
        # 基于计划的复杂度估算成本
        plan_str = str(plan_dict)
        base_cost = 500.0  # 基础成本
        
        # 根据计划长度调整成本
        length_factor = len(plan_str) / 200.0
        estimated_cost = base_cost + (length_factor * 20.0)
        
        return min(estimated_cost, 2000.0)  # 设置上限
    
    def reset(self):
        """重置环境状态"""
        self.state = "initialized"
        self.step_count = 0
        self.terminated = False
        return self.state
    
    @property
    def is_terminated(self) -> bool:
        """检查是否达到终止条件"""
        return self.terminated or self.step_count >= self.max_steps


class ReactReflectEnv(ReactEnv):
    """ReAct+Reflection环境类 - 支持反思机制的旅行规划环境"""
    
    def __init__(self):
        super().__init__()
        self.reflection_history: List[str] = []
        self.cost_history: List[float] = []
        
    def run(self, plan_dict: Dict[str, Any]) -> str:
        """
        执行旅行计划的成本计算，并记录历史用于反思
        """
        # 先调用父类方法获取基础结果
        result = super().run(plan_dict)
        
        # 尝试从结果中提取成本数字进行反思分析
        try:
            cost_match = re.search(r'\$(\d+\.?\d*)', result)
            if cost_match:
                current_cost = float(cost_match.group(1))
                self.cost_history.append(current_cost)
                
                # 如果成本历史足够，进行反思
                if len(self.cost_history) > 1:
                    if self._should_reflect():
                        reflection = self._generate_reflection(plan_dict, current_cost)
                        self.reflection_history.append(reflection)
                        result += f"\n\nReflection: {reflection}"
        except (ValueError, AttributeError):
            # 如果无法提取成本，跳过反思
            pass
        
        return result
    
    def _should_reflect(self) -> bool:
        """判断是否需要反思"""
        if len(self.cost_history) < 2:
            return False
        
        # 如果成本变化过大，触发反思
        recent_costs = self.cost_history[-2:]
        if recent_costs[0] > 0:  # 避免除零错误
            cost_change = abs(recent_costs[1] - recent_costs[0]) / recent_costs[0]
            return cost_change > 0.3  # 成本变化超过30%时反思
        
        return False
    
    def _generate_reflection(self, plan_dict: Dict, cost: float) -> str:
        """生成反思内容"""
        if len(self.cost_history) > 1:
            avg_cost = sum(self.cost_history) / len(self.cost_history)
            
            if cost > avg_cost * 1.2:
                return f"This plan's cost (${cost:.2f}) is significantly higher than the average (${avg_cost:.2f}). Consider reducing expensive components like luxury accommodations or premium transportation."
            elif cost < avg_cost * 0.8:
                return f"This plan's cost (${cost:.2f}) is lower than average (${avg_cost:.2f}). Verify that all necessary components are included and consider if the quality meets expectations."
            else:
                return f"This plan's cost (${cost:.2f}) appears reasonable compared to previous plans (average: ${avg_cost:.2f})."
        
        return f"Initial cost assessment: ${cost:.2f}. This will serve as a baseline for future comparisons."
    
    def get_reflections(self) -> List[str]:
        """获取所有反思记录"""
        return self.reflection_history.copy()
    
    def reset(self):
        """重置环境，清除反思历史"""
        super().reset()
        self.reflection_history = []
        self.cost_history = []
        return self.state


"""
城市名称验证和修正工具
"""
import re
from typing import List, Dict, Any, Union

class CityValidator:
    """城市名称验证器 - 修正LLM输出的错误城市名称"""
    
    def __init__(self):
        # 城市名称映射表 - 将错误的城市名称映射到正确的名称
        self.city_corrections = {
            # Santa Maria 相关的错误拼写
            'santamaria': 'Santa Maria',
            'santa maria': 'Santa Maria',  # 确保大小写正确
            'santamaría': 'Santa Maria',
            'santa maría': 'Santa Maria',
            
            # 其他常见的城市名称错误拼写可以在这里添加
            'newyork': 'Newark',
            'new york': 'Newark',
           
            # 中文城市名称到英文的映射
            '圣玛丽亚': 'Santa Maria',
            '圣玛利亚': 'Santa Maria',
            '纽瓦克': 'Newark',
        }
    
    def validate_and_correct_city(self, city_name: str) -> str:
        """
        验证并修正单个城市名称
        
        Args:
            city_name: 原始城市名称
            
        Returns:
            修正后的城市名称
        """
        if not city_name or not isinstance(city_name, str):
            return city_name
        
        # 去除前后空格
        city_name = city_name.strip()
        
        # 检查是否需要修正
        city_lower = city_name.lower()
        
        # 直接查找映射表
        if city_lower in self.city_corrections:
            corrected_name = self.city_corrections[city_lower]
            print(f"[CityValidator] 修正城市名称: '{city_name}' -> '{corrected_name}'")
            return corrected_name
        
        # 如果没有找到直接映射，尝试模糊匹配
        for incorrect_name, correct_name in self.city_corrections.items():
            if self._fuzzy_match(city_lower, incorrect_name):
                print(f"[CityValidator] 模糊匹配修正城市名称: '{city_name}' -> '{correct_name}'")
                return correct_name
        
        # 如果没有找到匹配，返回原始名称（但确保首字母大写）
        return self._capitalize_city_name(city_name)
    
    def _fuzzy_match(self, city1: str, city2: str) -> bool:
        """
        模糊匹配两个城市名称
        
        Args:
            city1: 城市名称1
            city2: 城市名称2
            
        Returns:
            是否匹配
        """
        # 移除空格和特殊字符进行比较
        clean_city1 = re.sub(r'[^a-zA-Z]', '', city1.lower())
        clean_city2 = re.sub(r'[^a-zA-Z]', '', city2.lower())
        
        # 如果清理后的名称相同，认为匹配
        if clean_city1 == clean_city2:
            return True
        
        # 计算编辑距离，如果距离很小，也认为匹配
        return self._edit_distance(clean_city1, clean_city2) <= 2
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """
        计算两个字符串的编辑距离
        
        Args:
            s1: 字符串1
            s2: 字符串2
            
        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _capitalize_city_name(self, city_name: str) -> str:
        """
        正确地大写城市名称
        
        Args:
            city_name: 原始城市名称
            
        Returns:
            正确大写的城市名称
        """
        # 分割单词并正确大写
        words = city_name.split()
        capitalized_words = []
        
        for word in words:
            if word.lower() in ['of', 'the', 'and', 'in', 'on', 'at', 'to', 'for', 'with']:
                # 介词保持小写（除非是第一个单词）
                if len(capitalized_words) == 0:
                    capitalized_words.append(word.capitalize())
                else:
                    capitalized_words.append(word.lower())
            else:
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def validate_and_correct_cities_list(self, cities: List[str]) -> List[str]:
        """
        验证并修正城市列表
        
        Args:
            cities: 原始城市列表
            
        Returns:
            修正后的城市列表
        """
        if not cities or not isinstance(cities, list):
            return cities
        
        corrected_cities = []
        for city in cities:
            corrected_city = self.validate_and_correct_city(city)
            corrected_cities.append(corrected_city)
        
        return corrected_cities
    
    def validate_and_correct_tool_params(self, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并修正工具参数中的城市名称
        
        Args:
            tool_params: 原始工具参数
            
        Returns:
            修正后的工具参数
        """
        if not tool_params or not isinstance(tool_params, dict):
            return tool_params
        
        # 创建参数副本以避免修改原始参数
        corrected_params = tool_params.copy()
        
        # 检查常见的城市参数字段
        city_fields = ['cities', 'city', 'destination', 'destinations', 'location', 'locations']
        
        for field in city_fields:
            if field in corrected_params:
                value = corrected_params[field]
                
                if isinstance(value, str):
                    # 单个城市名称
                    corrected_params[field] = self.validate_and_correct_city(value)
                elif isinstance(value, list):
                    # 城市列表
                    corrected_params[field] = self.validate_and_correct_cities_list(value)
        
        return corrected_params


# 全局城市验证器实例
_global_city_validator = None

def get_city_validator() -> CityValidator:
    """获取全局城市验证器实例"""
    global _global_city_validator
    if _global_city_validator is None:
        _global_city_validator = CityValidator()
    return _global_city_validator

def validate_and_correct_cities(cities: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    便捷函数：验证并修正城市名称
    
    Args:
        cities: 城市名称或城市列表
        
    Returns:
        修正后的城市名称或城市列表
    """
    validator = get_city_validator()
    
    if isinstance(cities, str):
        return validator.validate_and_correct_city(cities)
    elif isinstance(cities, list):
        return validator.validate_and_correct_cities_list(cities)
    else:
        return cities

def validate_and_correct_tool_params(tool_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：验证并修正工具参数中的城市名称
    
    Args:
        tool_params: 工具参数
        
    Returns:
        修正后的工具参数
    """
    validator = get_city_validator()
    return validator.validate_and_correct_tool_params(tool_params)
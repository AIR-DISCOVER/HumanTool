"""
数据管理器 - 实现数据懒加载和缓存机制
"""
import os
import pandas as pd
from typing import Dict, Any, Optional
from functools import lru_cache


class DataManager:
    """数据管理器 - 单例模式，实现数据懒加载和缓存"""
    
    _instance = None
    _data_cache = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.verbose = False
            self._setup_paths()
            DataManager._initialized = True
    
    def _setup_paths(self):
        """设置数据文件路径"""
        # 基于TATA项目结构设置路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        self.travelplanner_root = os.path.join(project_root, 'agent', 'TravelPlanner')
        
        # 数据文件路径
        self.data_paths = {
            'accommodations': os.path.join(self.travelplanner_root, 'database', 'accommodations', 'clean_accommodations_2022.csv'),
            'attractions': os.path.join(self.travelplanner_root, 'database', 'attractions', 'attractions.csv'),
            'restaurants': os.path.join(self.travelplanner_root, 'database', 'restaurants', 'clean_restaurant_2022.csv'),
        }
    
    def set_verbose(self, verbose: bool):
        """设置详细输出模式"""
        self.verbose = verbose
    
    def get_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        获取数据 - 使用懒加载和缓存
        
        Args:
            data_type: 数据类型 ('accommodations', 'attractions', 'restaurants')
        """
        # 如果数据已经在缓存中，直接返回
        if data_type in self._data_cache:
            if self.verbose:
                print(f"✅ [DataManager] 从缓存获取数据: {data_type}")
            return self._data_cache[data_type]
        
        # 否则加载数据
        if self.verbose:
            print(f"🔄 [DataManager] 加载数据: {data_type}")
        
        data = self._load_data(data_type)
        
        if data is not None:
            # 缓存数据
            self._data_cache[data_type] = data
            if self.verbose:
                print(f"✅ [DataManager] 数据已缓存: {data_type} ({len(data)} 条记录)")
        
        return data
    
    def _load_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """加载指定类型的数据"""
        try:
            if data_type not in self.data_paths:
                if self.verbose:
                    print(f"⚠️ [DataManager] 未知数据类型: {data_type}")
                return None
            
            file_path = self.data_paths[data_type]
            
            if not os.path.exists(file_path):
                if self.verbose:
                    print(f"⚠️ [DataManager] 数据文件不存在: {file_path}")
                return None
            
            # 根据数据类型加载不同的字段
            if data_type == 'accommodations':
                data = pd.read_csv(file_path).dropna()
                data = data[['NAME', 'price', 'room type', 'house_rules', 'minimum nights', 'maximum occupancy', 'review rate number', 'city']]
            
            elif data_type == 'attractions':
                data = pd.read_csv(file_path).dropna()
                data = data[['Name', 'Latitude', 'Longitude', 'Address', 'Phone', 'Website', 'City']]
            
            elif data_type == 'restaurants':
                data = pd.read_csv(file_path).dropna()
                data = data[['Name', 'Average Cost', 'Cuisines', 'Aggregate Rating', 'City']]
            
            else:
                data = pd.read_csv(file_path).dropna()
            
            if self.verbose:
                print(f"✅ [DataManager] 成功加载 {len(data)} 条 {data_type} 数据")
            
            return data
            
        except Exception as e:
            if self.verbose:
                print(f"❌ [DataManager] 加载数据失败 {data_type}: {e}")
            return None
    
    def is_data_cached(self, data_type: str) -> bool:
        """检查数据是否已缓存"""
        return data_type in self._data_cache
    
    def get_cached_data_info(self) -> Dict[str, int]:
        """获取已缓存数据的信息"""
        info = {}
        for data_type, data in self._data_cache.items():
            info[data_type] = len(data) if data is not None else 0
        return info
    
    def clear_cache(self, data_type: Optional[str] = None):
        """清空数据缓存"""
        if data_type:
            if data_type in self._data_cache:
                del self._data_cache[data_type]
                if self.verbose:
                    print(f"🗑️ [DataManager] 清空数据缓存: {data_type}")
        else:
            self._data_cache.clear()
            if self.verbose:
                print("🗑️ [DataManager] 清空所有数据缓存")
    
    def preload_data(self, data_types: list = None):
        """预加载数据（可选的性能优化）"""
        if data_types is None:
            data_types = list(self.data_paths.keys())
        
        if self.verbose:
            print(f"🚀 [DataManager] 预加载数据: {data_types}")
        
        for data_type in data_types:
            self.get_data(data_type)


# 全局数据管理器实例
_global_data_manager = None

def get_data_manager() -> DataManager:
    """获取全局数据管理器实例"""
    global _global_data_manager
    if _global_data_manager is None:
        _global_data_manager = DataManager()
    return _global_data_manager

def clear_data_cache(data_type: Optional[str] = None):
    """清空全局数据缓存"""
    global _global_data_manager
    if _global_data_manager is not None:
        _global_data_manager.clear_cache(data_type)
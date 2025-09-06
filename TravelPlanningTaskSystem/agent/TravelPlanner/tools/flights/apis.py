import pandas as pd
from pandas import DataFrame
from typing import Optional, Union
import re
import os
import sys

# 修复导入路径问题
try:
    from TravelPlan.utils.func import extract_before_parenthesis
except ImportError:
    # 如果导入失败，定义本地版本
    def extract_before_parenthesis(s):
        if not s:
            return s
        match = re.search(r'^(.*?)\([^)]*\)', s)
        return match.group(1).strip() if match else s.strip()

class Flights:

    def __init__(self, path="../../database/flights/clean_Flights_2022.csv"):
        self.path = path
        self.data = None
        self._load_data()

    def _load_data(self):
        """加载航班数据并进行预处理"""
        try:
            # 处理相对路径
            if not os.path.isabs(self.path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.path = os.path.join(current_dir, self.path)
            
            print(f"[Flights API] 尝试加载数据文件: {self.path}")
            print(f"[Flights API] 文件存在: {os.path.exists(self.path)}")
            
            self.data = pd.read_csv(self.path).dropna()[['Flight Number', 'Price', 'DepTime', 'ArrTime', 'ActualElapsedTime','FlightDate','OriginCityName','DestCityName','Distance']]
            
            # 数据预处理
            self.data['OriginCityName'] = self.data['OriginCityName'].str.strip()
            self.data['DestCityName'] = self.data['DestCityName'].str.strip()
            self.data['FlightDate'] = self.data['FlightDate'].str.strip()
            
            print(f"[Flights API] 成功加载 {len(self.data)} 条航班记录")
            print(f"[Flights API] 数据列: {list(self.data.columns)}")
            
            # 打印一些样本数据用于调试
            if len(self.data) > 0:
                print(f"[Flights API] 样本数据:")
                print(f"  - 起始城市样本: {self.data['OriginCityName'].unique()[:5]}")
                print(f"  - 目的城市样本: {self.data['DestCityName'].unique()[:5]}")
                print(f"  - 日期样本: {self.data['FlightDate'].unique()[:5]}")
                
        except Exception as e:
            print(f"[Flights API] 数据加载失败: {e}")
            import traceback
            traceback.print_exc()
            self.data = pd.DataFrame()

    def load_db(self):
        """重新加载数据库"""
        self._load_data()

    def run(self,
            origin: str,
            destination: str,
            departure_date: str,
            budget_max: Optional[float] = None,
            ) -> Union[DataFrame, str]:
        """
        搜索航班
        
        Args:
            origin: 起始城市
            destination: 目的城市  
            departure_date: 出发日期
            budget_max: 最大预算（可选）
            
        Returns:
            DataFrame: 匹配的航班数据，如果没有找到则返回错误信息字符串
        """
        print(f"\n[Flights API] 开始搜索航班:")
        print(f"  - 起始城市: '{origin}'")
        print(f"  - 目的城市: '{destination}'")
        print(f"  - 出发日期: '{departure_date}'")
        print(f"  - 预算上限: {budget_max}")
        
        if self.data is None or len(self.data) == 0:
            error_msg = "航班数据未加载或为空"
            print(f"[Flights API] X {error_msg}")
            return error_msg
        
        # 🎯 改进的匹配逻辑：支持模糊匹配和大小写不敏感
        try:
            # 清理输入参数
            origin_clean = extract_before_parenthesis(origin.strip()) if origin else ""
            destination_clean = extract_before_parenthesis(destination.strip()) if destination else ""
            date_clean = departure_date.strip() if departure_date else ""
            
            print(f"[Flights API] 清理后的参数:")
            print(f"  - 起始城市: '{origin_clean}'")
            print(f"  - 目的城市: '{destination_clean}'")
            print(f"  - 出发日期: '{date_clean}'")
            
            # 第一步：精确匹配
            results = self.data[
                (self.data["OriginCityName"].str.lower() == origin_clean.lower()) &
                (self.data["DestCityName"].str.lower() == destination_clean.lower()) &
                (self.data["FlightDate"] == date_clean)
            ]
            
            print(f"[Flights API] 精确匹配结果: {len(results)} 条")
            
            # 第二步：如果精确匹配失败，尝试模糊匹配
            if len(results) == 0:
                print(f"[Flights API] 精确匹配失败，尝试模糊匹配...")
                
                # 模糊匹配起始城市
                origin_matches = self.data[
                    self.data["OriginCityName"].str.contains(origin_clean, case=False, na=False, regex=False)
                ]
                print(f"[Flights API] 起始城市模糊匹配: {len(origin_matches)} 条")
                
                if len(origin_matches) > 0:
                    # 在起始城市匹配的基础上匹配目的城市
                    results = origin_matches[
                        origin_matches["DestCityName"].str.contains(destination_clean, case=False, na=False, regex=False) &
                        (origin_matches["FlightDate"] == date_clean)
                    ]
                    print(f"[Flights API] 起始+目的城市模糊匹配: {len(results)} 条")
                
                # 如果还是没有结果，尝试更宽松的日期匹配
                if len(results) == 0:
                    print(f"[Flights API] 尝试宽松的日期匹配...")
                    results = self.data[
                        (self.data["OriginCityName"].str.contains(origin_clean, case=False, na=False, regex=False)) &
                        (self.data["DestCityName"].str.contains(destination_clean, case=False, na=False, regex=False))
                    ]
                    print(f"[Flights API] 忽略日期的匹配结果: {len(results)} 条")
            
            # 第三步：应用预算过滤
            if budget_max is not None and len(results) > 0:
                original_count = len(results)
                results = results[results["Price"] <= budget_max]
                print(f"[Flights API] 预算过滤: {original_count} -> {len(results)} 条 (预算≤${budget_max})")
            
            # 第四步：排序结果（按价格升序）
            if len(results) > 0:
                results = results.sort_values(by=["Price", "DepTime"], ascending=[True, True])
                print(f"[Flights API] √ 找到 {len(results)} 条航班，已按价格排序")
                
                # 打印前几条结果用于调试
                print(f"[Flights API] 前3条结果:")
                for i, (_, row) in enumerate(results.head(3).iterrows()):
                    print(f"  {i+1}. {row['Flight Number']}: ${row['Price']} - {row['DepTime']} to {row['ArrTime']}")
                
                return results
            else:
                # 提供详细的调试信息
                error_msg = f"没有找到从 {origin} 到 {destination} 在 {departure_date} 的航班"
                if budget_max:
                    error_msg += f"（预算≤${budget_max}）"
                
                print(f"[Flights API] X {error_msg}")
                
                # 提供调试信息
                print(f"[Flights API] 调试信息:")
                print(f"  - 数据库中的起始城市: {sorted(self.data['OriginCityName'].unique())}")
                print(f"  - 数据库中的目的城市: {sorted(self.data['DestCityName'].unique())}")
                print(f"  - 数据库中的日期范围: {self.data['FlightDate'].min()} 到 {self.data['FlightDate'].max()}")
                
                return error_msg
                
        except Exception as e:
            error_msg = f"航班搜索过程中出现错误: {str(e)}"
            print(f"[Flights API] X {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def run_for_annotation(self,
            origin: str,
            destination: str,
            departure_date: str,
            ) -> DataFrame:
        """Search for flights by origin, destination, and departure date."""
        results = self.data[self.data["OriginCityName"] == extract_before_parenthesis(origin)]
        results = results[results["DestCityName"] == extract_before_parenthesis(destination)]
        results = results[results["FlightDate"] == departure_date]
        return results.to_string(index=False)

    def get_city_set(self):
        city_set = set()
        for unit in self.data['data']:
            city_set.add(unit[5])
            city_set.add(unit[6])
        return city_set
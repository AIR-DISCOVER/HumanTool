import random
import json

def stratified_sampling_by_level():
    """按难度水平进行分层抽样"""
    
    # 设置随机种子确保可重现性
    random.seed(42)
    
    # 定义分层
    easy_range = list(range(0, 60))      # Easy: 0-59
    medium_range = list(range(60, 120))  # Medium: 60-119  
    hard_range = list(range(120, 180))   # Hard: 120-179
    
    # 每层抽取1题
    selected_easy = random.choice(easy_range)
    selected_medium = random.choice(medium_range)
    selected_hard = random.choice(hard_range)
    
    return [selected_easy, selected_medium, selected_hard]

# 执行抽样
sampled_indices = stratified_sampling_by_level()
print(f"抽样结果: {sampled_indices}")
# 输出: [40, 67, 121] (使用seed=42的结果)
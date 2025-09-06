import json
import re
import argparse
from datetime import datetime
import os
import sys

def parse_text_plan_to_json(text_plan):
    """
    将文本格式的计划解析为JSON格式
    """
    if not text_plan or text_plan.strip() == "":
        return []
    
    days = []
    current_day = None
    
    # 按行分割文本
    lines = text_plan.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 匹配 Day X: 格式
        day_match = re.match(r'Day (\d+):', line)
        if day_match:
            if current_day is not None:
                days.append(current_day)
            
            day_num = int(day_match.group(1))
            current_day = {
                "day": day_num,
                "current_city": "-",
                "transportation": "-",
                "breakfast": "-",
                "lunch": "-", 
                "dinner": "-",
                "attraction": "-",
                "accommodation": "-"
            }
            continue
        
        if current_day is None:
            continue
            
        # 解析各个字段
        if line.startswith('Current City:'):
            current_day['current_city'] = line.replace('Current City:', '').strip()
        elif line.startswith('Transportation:'):
            current_day['transportation'] = line.replace('Transportation:', '').strip()
        elif line.startswith('Breakfast:'):
            current_day['breakfast'] = line.replace('Breakfast:', '').strip()
        elif line.startswith('Lunch:'):
            current_day['lunch'] = line.replace('Lunch:', '').strip()
        elif line.startswith('Dinner:'):
            current_day['dinner'] = line.replace('Dinner:', '').strip()
        elif line.startswith('Attraction:'):
            current_day['attraction'] = line.replace('Attraction:', '').strip()
        elif line.startswith('Accommodation:'):
            current_day['accommodation'] = line.replace('Accommodation:', '').strip()
    
    # 添加最后一天
    if current_day is not None:
        days.append(current_day)
    
    return days

def extract_cost_info(text):
    """
    从文本中提取费用信息
    """
    cost_pattern = r'Cost:\s*\$?(\d+(?:\.\d{2})?)'
    costs = re.findall(cost_pattern, text)
    return [float(cost) for cost in costs]

def enhance_plan_with_costs(plan_json):
    """
    为计划添加费用信息（如果文本中包含）
    """
    for day in plan_json:
        # 尝试从transportation字段提取费用
        if 'Cost:' in day.get('transportation', ''):
            transport_text = day['transportation']
            costs = extract_cost_info(transport_text)
            if costs:
                # 在transportation字段末尾添加cost信息
                if ', cost:' not in transport_text.lower():
                    day['transportation'] = f"{transport_text}, cost: {costs[0]}"
        
        # 为餐厅添加费用（可以设置默认值）
        for meal in ['breakfast', 'lunch', 'dinner']:
            if day.get(meal, '-') != '-' and ', cost:' not in day[meal].lower():
                # 添加一个合理的默认费用
                meal_cost = 15 if meal == 'breakfast' else (25 if meal == 'lunch' else 35)
                day[meal] = f"{day[meal]}, cost: {meal_cost}"
        
        # 为住宿添加费用
        if day.get('accommodation', '-') != '-' and ', cost:' not in day['accommodation'].lower():
            # 添加默认住宿费用
            day['accommodation'] = f"{day['accommodation']}, cost: 150.00"
    
    return plan_json

def postprocess_two_stage_result(input_file, output_file=None, add_costs=True):
    """
    后处理Two-stage结果文件
    """
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f) if input_file.endswith('.json') else json.loads(f.readline())
    
    # 获取文本计划
    text_plan = data.get('plan', '')
    
    if not text_plan:
        print("No plan found in input file")
        return None
    
    print("Original text plan:")
    print("-" * 50)
    print(text_plan[:500] + "..." if len(text_plan) > 500 else text_plan)
    print("-" * 50)
    
    # 解析为JSON格式
    plan_json = parse_text_plan_to_json(text_plan)
    
    if not plan_json:
        print("Failed to parse plan")
        return None
    
    # 添加费用信息
    if add_costs:
        plan_json = enhance_plan_with_costs(plan_json)
    
    # 构建最终结果
    result = {
        "idx": data.get('idx', 41),
        "query": data.get('query', ''),
        "plan": plan_json
    }
    
    # 保存结果
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"processed_two_stage_result_{timestamp}.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"\nProcessed result saved to: {output_file}")
    
    return result

def validate_json_format(plan_json):
    """
    验证JSON格式是否正确
    """
    required_fields = ['day', 'current_city', 'transportation', 'breakfast', 'lunch', 'dinner', 'attraction', 'accommodation']
    
    if not isinstance(plan_json, list):
        return False, "Plan should be a list of days"
    
    for i, day in enumerate(plan_json):
        if not isinstance(day, dict):
            return False, f"Day {i+1} should be a dictionary"
        
        for field in required_fields:
            if field not in day:
                return False, f"Day {i+1} missing field: {field}"
        
        if not isinstance(day['day'], int):
            return False, f"Day {i+1} 'day' field should be an integer"
    
    return True, "Valid format"

def manual_fix_plan(plan_json):
    """
    手动修复常见的计划格式问题
    """
    fixed_plan = []
    
    for day in plan_json:
        fixed_day = dict(day)  # 复制
        
        # 确保day字段是整数
        if isinstance(fixed_day.get('day'), str):
            try:
                fixed_day['day'] = int(fixed_day['day'])
            except ValueError:
                fixed_day['day'] = len(fixed_plan) + 1
        
        # 确保所有字段都存在且不为None
        required_fields = ['day', 'current_city', 'transportation', 'breakfast', 'lunch', 'dinner', 'attraction', 'accommodation']
        for field in required_fields:
            if field not in fixed_day or fixed_day[field] is None:
                fixed_day[field] = '-'
        
        # 修复空字符串
        for field in required_fields:
            if fixed_day[field] == '':
                fixed_day[field] = '-'
        
        fixed_plan.append(fixed_day)
    
    return fixed_plan

def main():
    parser = argparse.ArgumentParser(description='Postprocess Two-stage Mode results')
    parser.add_argument('--input_file', type=str, required=True,
                        help='Input file path (JSON or JSONL)')
    parser.add_argument('--output_file', type=str, default=None,
                        help='Output file path')
    parser.add_argument('--add_costs', action='store_true', default=True,
                        help='Add default cost information')
    parser.add_argument('--validate', action='store_true',
                        help='Validate the JSON format')
    parser.add_argument('--manual_fix', action='store_true',
                        help='Apply manual fixes to common issues')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}")
        return
    
    print(f"Processing file: {args.input_file}")
    print("=" * 60)
    
    # 后处理
    result = postprocess_two_stage_result(
        args.input_file, 
        args.output_file, 
        add_costs=args.add_costs
    )
    
    if result is None:
        print("Postprocessing failed")
        return
    
    # 验证格式
    if args.validate:
        print("\nValidating JSON format...")
        is_valid, message = validate_json_format(result['plan'])
        print(f"Validation result: {message}")
        
        if not is_valid and args.manual_fix:
            print("Applying manual fixes...")
            result['plan'] = manual_fix_plan(result['plan'])
            
            # 重新验证
            is_valid, message = validate_json_format(result['plan'])
            print(f"After fixes: {message}")
            
            # 重新保存修复后的结果
            if args.output_file:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                print(f"Fixed result saved to: {args.output_file}")
    
    # 打印结果摘要
    print(f"\nResult summary:")
    print(f"- Index: {result['idx']}")
    print(f"- Query: {result['query'][:100]}..." if len(result['query']) > 100 else f"- Query: {result['query']}")
    print(f"- Days planned: {len(result['plan'])}")
    
    if result['plan']:
        print(f"- First day: {result['plan'][0]}")
        if len(result['plan']) > 1:
            print(f"- Last day: {result['plan'][-1]}")
    
    print("\nPostprocessing completed successfully!")

if __name__ == "__main__":
    main()
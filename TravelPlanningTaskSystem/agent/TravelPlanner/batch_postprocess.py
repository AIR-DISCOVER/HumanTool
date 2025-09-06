import json
import os
import argparse
from datetime import datetime
from tqdm import tqdm
from postprocess_two_stage import parse_text_plan_to_json, enhance_plan_with_costs, validate_json_format, manual_fix_plan

def process_jsonl_file(input_file, output_file=None, add_costs=True, validate=True, manual_fix=True):
    """
    批量处理JSONL文件
    """
    results = []
    failed_indices = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Processing {len(lines)} entries...")
    
    for line_num, line in enumerate(tqdm(lines, desc="Processing")):
        try:
            data = json.loads(line.strip())
            
            # 获取文本计划
            text_plan = data.get('plan', '')
            
            if not text_plan or text_plan.strip() == "":
                print(f"Warning: No plan found for entry {line_num + 1}")
                failed_indices.append(data.get('idx', line_num + 1))
                continue
            
            # 解析为JSON格式
            plan_json = parse_text_plan_to_json(text_plan)
            
            if not plan_json:
                print(f"Warning: Failed to parse plan for entry {line_num + 1}")
                failed_indices.append(data.get('idx', line_num + 1))
                continue
            
            # 添加费用信息
            if add_costs:
                plan_json = enhance_plan_with_costs(plan_json)
            
            # 验证和修复
            if validate:
                is_valid, message = validate_json_format(plan_json)
                if not is_valid and manual_fix:
                    plan_json = manual_fix_plan(plan_json)
                    is_valid, _ = validate_json_format(plan_json)
                
                if not is_valid:
                    print(f"Warning: Invalid format for entry {line_num + 1}: {message}")
                    failed_indices.append(data.get('idx', line_num + 1))
                    continue
            
            # 构建结果
            result = {
                "idx": data.get('idx', line_num + 1),
                "query": data.get('query', ''),
                "plan": plan_json
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"Error processing entry {line_num + 1}: {str(e)}")
            failed_indices.append(line_num + 1)
            continue
    
    # 保存结果
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"processed_{base_name}_{timestamp}.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"\nProcessing completed:")
    print(f"- Total entries: {len(lines)}")
    print(f"- Successfully processed: {len(results)}")
    print(f"- Failed: {len(failed_indices)}")
    print(f"- Output file: {output_file}")
    
    if failed_indices:
        print(f"- Failed indices: {failed_indices}")
    
    return output_file, results, failed_indices

def show_sample_comparison(input_file, output_file, sample_idx=41):
    """
    显示处理前后的对比
    """
    print(f"\n{'='*80}")
    print(f"SAMPLE COMPARISON (idx: {sample_idx})")
    print(f"{'='*80}")
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            if data.get('idx') == sample_idx:
                print("BEFORE (Text format):")
                print("-" * 40)
                plan_text = data.get('plan', '')
                print(plan_text[:500] + "..." if len(plan_text) > 500 else plan_text)
                break
    
    # 读取处理后的文件
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            if data.get('idx') == sample_idx:
                print("\nAFTER (JSON format):")
                print("-" * 40)
                plan_json = data.get('plan', [])
                if plan_json:
                    print(f"First day: {json.dumps(plan_json[0], indent=2, ensure_ascii=False)}")
                    if len(plan_json) > 1:
                        print(f"\nLast day: {json.dumps(plan_json[-1], indent=2, ensure_ascii=False)}")
                break

def main():
    parser = argparse.ArgumentParser(description='Batch postprocess Two-stage Mode JSONL results')
    parser.add_argument('--input_file', type=str, required=True,
                        help='Input JSONL file path')
    parser.add_argument('--output_file', type=str, default=None,
                        help='Output JSONL file path')
    parser.add_argument('--add_costs', action='store_true', default=True,
                        help='Add default cost information')
    parser.add_argument('--validate', action='store_true', default=True,
                        help='Validate the JSON format')
    parser.add_argument('--manual_fix', action='store_true', default=True,
                        help='Apply manual fixes to common issues')
    parser.add_argument('--show_sample', action='store_true',
                        help='Show a sample of processed results')
    parser.add_argument('--sample_idx', type=int, default=41,
                        help='Index for sample comparison')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}")
        return
    
    print(f"Batch processing JSONL file: {args.input_file}")
    print("=" * 60)
    
    # 批量处理
    output_file, results, failed_indices = process_jsonl_file(
        args.input_file,
        args.output_file,
        add_costs=args.add_costs,
        validate=args.validate,
        manual_fix=args.manual_fix
    )
    
    # 显示样本对比
    if args.show_sample and results:
        show_sample_comparison(args.input_file, output_file, args.sample_idx)
    
    print(f"\n✅ Processing completed successfully!")
    print(f"📁 Output file: {output_file}")

if __name__ == "__main__":
    main()
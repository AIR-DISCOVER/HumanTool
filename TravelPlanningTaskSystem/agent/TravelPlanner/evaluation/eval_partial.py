import json
import argparse
from eval import eval_score, statistics, commonsense_eval, hard_eval
from datasets import load_dataset
import sys
import os
from tqdm import tqdm
from difflib import SequenceMatcher

def load_line_json_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"❌ 文件 {filename} 是空的!")
                return data
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if line:
                    try:
                        unit = json.loads(line)
                        data.append(unit)
                        print(f"✓ 成功读取第 {line_num} 行，query: {unit.get('query', '')[:50]}...")
                    except json.JSONDecodeError as e:
                        print(f"❌ 第 {line_num} 行 JSON 解析错误: {e}")
                        print(f"  内容: {line[:100]}...")
                        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {filename}")
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
    
    print(f"总共读取了 {len(data)} 条记录")
    return data

def find_matching_question(target_query, dataset, similarity_threshold=0.8):
    """
    在数据集中找到与目标query最相似的问题
    返回匹配的问题和相似度
    """
    best_match = None
    best_similarity = 0
    best_idx = -1
    
    for i, item in enumerate(dataset):
        # 计算文本相似度
        similarity = SequenceMatcher(None, target_query.lower().strip(), item['query'].lower().strip()).ratio()
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = item
            best_idx = i
    
    return best_match, best_similarity, best_idx

def eval_by_query_matching(set_type, evaluation_file_path, similarity_threshold=0.8):
    """
    使用query文本相似度匹配进行评估
    """
    print(f"正在加载数据集...")
    
    try:
        # 加载验证数据集
        if set_type == 'validation':
            dataset = load_dataset('osunlp/TravelPlanner', 'validation')['validation']
        elif set_type == 'test':
            dataset = load_dataset('osunlp/TravelPlanner', 'test')['test']
        else:
            dataset = load_dataset('osunlp/TravelPlanner', 'train')['train']
        
        dataset = [x for x in dataset]
        print(f"数据集加载完成，共 {len(dataset)} 个问题")
    except Exception as e:
        print(f"❌ 数据集加载失败: {e}")
        return
    
    # 读取答案文件
    print(f"正在读取答案文件: {evaluation_file_path}")
    tested_plans = load_line_json_data(evaluation_file_path)
    
    if not tested_plans:
        print("❌ 没有读取到任何答案!")
        return
    
    # 使用query匹配找到对应的问题
    matched_pairs = []
    unmatched_plans = []
    
    for plan_idx, plan in enumerate(tested_plans):
        target_query = plan.get('query', '').strip()
        plan_content = plan.get('plan')
        
        if not target_query:
            print(f"❌ 跳过第 {plan_idx + 1} 个计划: query字段为空")
            unmatched_plans.append(plan)
            continue
            
        if not plan_content:
            print(f"❌ 跳过第 {plan_idx + 1} 个计划: plan字段为空")
            unmatched_plans.append(plan)
            continue
        
        print(f"\n正在匹配第 {plan_idx + 1} 个计划:")
        print(f"  目标query: {target_query[:80]}...")
        
        # 查找最相似的问题
        matched_question, similarity, matched_dataset_idx = find_matching_question(target_query, dataset, similarity_threshold)
        
        if matched_question and similarity >= similarity_threshold:
            matched_pairs.append((matched_question, plan, similarity))
            print(f"✓ 匹配成功 (相似度: {similarity:.3f})")
            print(f"  匹配的query: {matched_question['query'][:80]}...")
        else:
            unmatched_plans.append(plan)
            print(f"❌ 匹配失败 (最高相似度: {similarity:.3f} < {similarity_threshold})")
            if matched_question:
                print(f"  最接近的query: {matched_question['query'][:80]}...")
    
    if len(matched_pairs) == 0:
        print("\n❌ 没有找到任何匹配的问题!")
        print("可能的原因:")
        print(f"1. query相似度都低于阈值 {similarity_threshold}")
        print("2. plan字段为空或缺失")
        print("3. query字段缺失或为空")
        print(f"\n建议:")
        print(f"1. 降低相似度阈值: --similarity_threshold 0.6")
        print(f"2. 检查输入文件格式")
        return
    
    print(f"\n✓ 成功匹配 {len(matched_pairs)} 个问题")
    if len(unmatched_plans) > 0:
        print(f"⚠️ 未匹配 {len(unmatched_plans)} 个计划")
    
    print(f"开始评估...")
    
    # 评估统计
    delivery_cnt = 0
    commonsense_pass_cnt = 0
    hard_pass_cnt = 0
    final_pass_cnt = 0
    
    commonsense_constraint_pass = 0
    commonsense_constraint_total = 0
    hard_constraint_pass = 0
    hard_constraint_total = 0
    
    plan_results = []
    
    for i, (query_data, tested_plan, similarity) in enumerate(matched_pairs):
        print(f"\n{'='*80}")
        print(f"评估计划 {i+1}/{len(matched_pairs)} (相似度: {similarity:.3f})")
        print(f"目标Query: {tested_plan.get('query', '')[:100]}...")
        print(f"匹配Query: {query_data['query'][:100]}...")
        print(f"{'='*80}")
        
        # 数据类型处理
        if type(query_data) == str:
            query_data = eval(query_data)
        if type(tested_plan) == str:
            tested_plan = eval(tested_plan)
        
        # 处理local_constraint
        if 'local_constraint' not in query_data:
            print(f"❌ 原始数据缺少local_constraint字段，跳过此题")
            continue
            
        if type(query_data['local_constraint']) == str:
            try:
                query_data['local_constraint'] = eval(query_data['local_constraint'])
            except:
                print(f"❌ local_constraint格式错误，跳过此题")
                continue
        
        # 初始化结果
        delivered = bool(tested_plan.get('plan'))
        commonsense_pass = False
        hard_pass = False
        commonsense_info_box = None
        hard_info_box = None
        
        print(f"计划提交状态: {'✓ 已提交' if delivered else '✗ 未提交'}")
        
        if delivered:
            delivery_cnt += 1
            
            try:
                # 常识约束评估
                print(f"\n--- 常识约束评估 ---")
                commonsense_info_box = commonsense_eval(query_data, tested_plan['plan'])
                commonsense_pass = True
                
                if commonsense_info_box:
                    for constraint_name, (passed, details_info) in commonsense_info_box.items():
                        if passed is not None:
                            commonsense_constraint_total += 1
                            status = "✓ 通过" if passed else "✗ 失败"
                            print(f"  {constraint_name}: {status}")
                            
                            if passed:
                                commonsense_constraint_pass += 1
                            else:
                                commonsense_pass = False
                                if details_info:
                                    print(f"    详细错误信息:")
                                    if isinstance(details_info, dict):
                                        for key, value in details_info.items():
                                            print(f"      {key}: {value}")
                                    elif isinstance(details_info, list):
                                        for idx, item in enumerate(details_info):
                                            print(f"      [{idx}]: {item}")
                                    else:
                                        print(f"      {str(details_info)}")
                    
                    print(f"常识约束总体: {'✓ 通过' if commonsense_pass else '✗ 失败'}")
                else:
                    print(f"  无常识约束数据")
                
                # 硬约束评估
                print(f"\n--- 硬约束评估 ---")
                if (commonsense_info_box and 
                    'is_not_absent' in commonsense_info_box and 
                    'is_valid_information_in_sandbox' in commonsense_info_box and
                    commonsense_info_box['is_not_absent'][0] and 
                    commonsense_info_box['is_valid_information_in_sandbox'][0]):
                    
                    hard_info_box = hard_eval(query_data, tested_plan['plan'])
                    hard_pass = True
                    
                    if hard_info_box:
                        for constraint_name, (passed, details_info) in hard_info_box.items():
                            if passed is not None:
                                hard_constraint_total += 1
                                status = "✓ 通过" if passed else "✗ 失败"
                                print(f"  {constraint_name}: {status}")
                                
                                if passed:
                                    hard_constraint_pass += 1
                                else:
                                    hard_pass = False
                                    if details_info:
                                        print(f"    详细错误信息:")
                                        if isinstance(details_info, dict):
                                            for key, value in details_info.items():
                                                print(f"      {key}: {value}")
                                        elif isinstance(details_info, list):
                                            for idx, item in enumerate(details_info):
                                                print(f"      [{idx}]: {item}")
                                        else:
                                            print(f"      {str(details_info)}")
                        
                        print(f"硬约束总体: {'✓ 通过' if hard_pass else '✗ 失败'}")
                    else:
                        print(f"  无硬约束数据")
                        hard_pass = False
                else:
                    hard_pass = False
                    print(f"  硬约束跳过 (常识约束未通过)")
                
            except Exception as e:
                print(f"❌ 评估过程中出错: {e}")
                import traceback
                traceback.print_exc()
                commonsense_pass = False
                hard_pass = False
            
            # 统计结果
            if commonsense_pass:
                commonsense_pass_cnt += 1
            if hard_pass:
                hard_pass_cnt += 1
            if commonsense_pass and hard_pass:
                final_pass_cnt += 1
        
        # 总结本题结果
        final_status = commonsense_pass and hard_pass
        print(f"\n--- 本题总结 ---")
        print(f"  相似度: {similarity:.3f}")
        print(f"  提交状态: {'✓' if delivered else '✗'}")
        print(f"  常识约束: {'✓' if commonsense_pass else '✗'}")
        print(f"  硬约束: {'✓' if hard_pass else '✗'}")
        print(f"  最终结果: {'✓ 通过' if final_status else '✗ 失败'}")
        
        plan_results.append({
            'plan_idx': i + 1,
            'similarity': similarity,
            'target_query': tested_plan.get('query', '')[:100] + '...',
            'matched_query': query_data['query'][:100] + '...',
            'delivered': delivered,
            'commonsense_pass': commonsense_pass,
            'hard_pass': hard_pass,
            'final_pass': final_status,
            'commonsense_details': commonsense_info_box,
            'hard_details': hard_info_box
        })
    
    # 计算总体结果
    total_evaluated = len(matched_pairs)
    
    print(f"\n{'='*80}")
    print(f"=== Query匹配评估结果 ===")
    print(f"{'='*80}")
    print(f"输入文件中的计划数: {len(tested_plans)}")
    print(f"成功匹配并评估的计划数: {total_evaluated}")
    print(f"未匹配的计划数: {len(unmatched_plans)}")
    print(f"相似度阈值: {similarity_threshold}")
    print(f"")
    
    if total_evaluated > 0:
        print(f"Delivery Rate: {delivery_cnt/total_evaluated*100:.2f}% ({delivery_cnt}/{total_evaluated})")
        
        if commonsense_constraint_total > 0:
            print(f"Commonsense Constraint Micro Pass Rate: {commonsense_constraint_pass/commonsense_constraint_total*100:.2f}% ({commonsense_constraint_pass}/{commonsense_constraint_total})")
        else:
            print(f"Commonsense Constraint Micro Pass Rate: N/A (0/0)")
        
        print(f"Commonsense Constraint Macro Pass Rate: {commonsense_pass_cnt/total_evaluated*100:.2f}% ({commonsense_pass_cnt}/{total_evaluated})")
        
        if hard_constraint_total > 0:
            print(f"Hard Constraint Micro Pass Rate: {hard_constraint_pass/hard_constraint_total*100:.2f}% ({hard_constraint_pass}/{hard_constraint_total})")
        else:
            print(f"Hard Constraint Micro Pass Rate: N/A (0/0)")
        
        print(f"Hard Constraint Macro Pass Rate: {hard_pass_cnt/total_evaluated*100:.2f}% ({hard_pass_cnt}/{total_evaluated})")
        print(f"Final Pass Rate: {final_pass_cnt/total_evaluated*100:.2f}% ({final_pass_cnt}/{total_evaluated})")
        
        print(f"\n{'='*80}")
        print(f"=== 每题详细结果汇总 ===")
        print(f"{'='*80}")
        for result in plan_results:
            status = "✓ PASS" if result['final_pass'] else "✗ FAIL"
            print(f"计划 {result['plan_idx']}: {status} (相似度: {result['similarity']:.3f})")
            print(f"  提交: {'✓' if result['delivered'] else '✗'}")
            print(f"  常识约束: {'✓' if result['commonsense_pass'] else '✗'}")
            print(f"  硬约束: {'✓' if result['hard_pass'] else '✗'}")
            print(f"  目标Query: {result['target_query']}")
            print(f"  匹配Query: {result['matched_query']}")
            print()
        
        # 显示相似度分布
        similarities = [result['similarity'] for result in plan_results]
        print(f"相似度分布:")
        print(f"  平均相似度: {sum(similarities)/len(similarities):.3f}")
        print(f"  最高相似度: {max(similarities):.3f}")
        print(f"  最低相似度: {min(similarities):.3f}")
        
        return {
            'total_plans': len(tested_plans),
            'evaluated_plans': total_evaluated,
            'unmatched_plans': len(unmatched_plans),
            'similarity_threshold': similarity_threshold,
            'Delivery Rate': delivery_cnt/total_evaluated,
            'Commonsense Constraint Micro Pass Rate': commonsense_constraint_pass/commonsense_constraint_total if commonsense_constraint_total > 0 else 0,
            'Commonsense Constraint Macro Pass Rate': commonsense_pass_cnt/total_evaluated,
            'Hard Constraint Micro Pass Rate': hard_constraint_pass/hard_constraint_total if hard_constraint_total > 0 else 0,
            'Hard Constraint Macro Pass Rate': hard_pass_cnt/total_evaluated,
            'Final Pass Rate': final_pass_cnt/total_evaluated
        }
    else:
        print("❌ 没有任何计划被成功评估!")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--set_type', type=str, default='validation', 
                       choices=['validation', 'test', 'train'])
    parser.add_argument('--evaluation_file_path', type=str, required=True)
    parser.add_argument('--similarity_threshold', type=float, default=0.8, 
                       help='Query相似度阈值 (0.0-1.0)')
    
    args = parser.parse_args()
    eval_by_query_matching(args.set_type, args.evaluation_file_path, args.similarity_threshold)
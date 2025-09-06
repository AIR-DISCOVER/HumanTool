from datasets import load_dataset
import json

def get_travelplanner_questions(set_type='validation', save_to_file=True):
    """获取TravelPlanner的题目和参考信息"""
    
    # 加载数据集
    data = load_dataset('osunlp/TravelPlanner', set_type)[set_type]
    
    questions = []
    for i, item in enumerate(data):
        question = {
            'idx': i,  # 修复：使用原始索引 i，而不是 i + 1
            'query': item['query'],  # 自然语言题目
            'org': item['org'],
            'dest': item['dest'],
            'days': item['days'],
            'people_number': item['people_number'],
            'budget': item['budget'],
            'local_constraint': item['local_constraint'],
            'date': item['date'],
            'reference_information': item['reference_information'],  # 这里包含所有参考信息
            'level': item.get('level', 'unknown')
        }
        questions.append(question)
    
    if save_to_file:
        # 保存完整题目信息
        with open(f'{set_type}_questions.jsonl', 'w', encoding='utf-8') as f:
            for q in questions:
                f.write(json.dumps(q, ensure_ascii=False) + '\n')
        
        # 保存简化版题目（不含参考信息，减少文件大小）
        with open(f'{set_type}_questions_simple.jsonl', 'w', encoding='utf-8') as f:
            for q in questions:
                simple_q = {k: v for k, v in q.items() if k != 'reference_information'}
                f.write(json.dumps(simple_q, ensure_ascii=False) + '\n')
        
        print(f"已保存 {len(questions)} 个题目到文件")
        print(f"完整版: {set_type}_questions.jsonl")
        print(f"简化版: {set_type}_questions_simple.jsonl")
        print(f"索引范围: 0 到 {len(questions)-1}")  # 添加索引范围提示
    
    return questions

def show_question_example(questions, idx=0):
    """展示题目示例"""
    q = questions[idx]
    print(f"=== 题目 {q['idx']} ===")
    print(f"查询: {q['query']}")
    print(f"路线: {q['org']} -> {q['dest']}")
    print(f"天数: {q['days']}, 人数: {q['people_number']}, 预算: ${q['budget']}")
    print(f"约束条件: {q['local_constraint']}")
    print(f"日期: {q['date']}")
    print(f"难度: {q['level']}")
    
    # 展示参考信息的结构
    ref_info = q['reference_information']
    print(f"\n参考信息包含:")
    if isinstance(ref_info, dict):
        for key, value in ref_info.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} 条记录")
            else:
                print(f"  {key}: {type(value)}")

def verify_index_consistency():
    """验证索引一致性"""
    print("验证索引一致性...")
    
    # 加载官方数据集
    official_data = load_dataset('osunlp/TravelPlanner', 'validation')['validation']
    
    # 加载我们生成的文件
    with open('validation_questions_simple.jsonl', 'r', encoding='utf-8') as f:
        our_data = [json.loads(line) for line in f]
    
    # 检查前5个问题
    for i in range(min(5, len(official_data))):
        official_query = official_data[i]['query']
        our_query = our_data[i]['query']
        our_idx = our_data[i]['idx']
        
        print(f"索引 {i}:")
        print(f"  官方: {official_query[:50]}...")
        print(f"  我们: {our_query[:50]}...")
        print(f"  我们的idx: {our_idx}")
        print(f"  匹配: {'✓' if official_query == our_query and our_idx == i else '✗'}")
        print()

if __name__ == "__main__":
    # 获取验证集题目
    questions = get_travelplanner_questions('validation')
    
    # 展示第一个题目
    show_question_example(questions, 0)
    
    # 验证索引一致性
    verify_index_consistency()
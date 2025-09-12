#!/usr/bin/env python3
"""
执行SQL查询并生成二维数组格式的输出
同时提取样本句子用于验证分类标签的准确性
"""
import MySQLdb
import os
import csv
import json
from typing import List, Tuple

def get_database_config():
    """获取数据库配置 - 使用127.0.0.1修复连接问题"""
    return {
        'host': '127.0.0.1',    # 使用IP而不是localhost修复连接问题
        'port': 3044,           # Docker映射端口
        'user': 'root',
        'password': '123456',   # 根据docker-compose.yml中的配置
        'database': 'tata',
        'charset': 'utf8mb4'
    }

def execute_query(session_id: str = 'session_1755676765762') -> List[Tuple]:
    """执行查询并返回结果"""
    
    # 读取SQL查询文件
    with open('word_frequency_2d_array.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    # 替换session_id
    query = query.replace('session_1755676765762', session_id)
    
    config = get_database_config()
    
    try:
        connection = MySQLdb.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            passwd=config['password'],
            db=config['database'],
            charset=config['charset']
        )
        cursor = connection.cursor()
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
        
    except Exception as e:
        print(f"数据库错误: {e}")
        return []

def format_as_2d_array(results: List[Tuple]) -> List[List]:
    """将结果格式化为真正的二维数组"""
    if not results:
        return []
    
    # 直接返回数据，不包含表头，并转换Decimal为int
    array_2d = []
    for row in results:
        # 转换第三列（数量）为int，以避免JSON序列化问题
        count_value = int(row[2]) if row[2] is not None else 0
        array_2d.append([row[0], row[1], count_value])
    
    return array_2d

def save_as_csv(array_2d: List[List], filename: str = 'word_frequency_results.csv'):
    """保存为CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(array_2d)
    print(f"结果已保存到: {filename}")

def save_as_json(array_2d: List[List], filename: str = 'word_frequency_results.json'):
    """保存为纯二维数组JSON文件"""
    if not array_2d:
        return
    
    # 直接保存二维数组
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(array_2d, jsonfile, ensure_ascii=False, indent=2)
    print(f"二维数组已保存到: {filename}")

def get_sample_sentences(session_id: str = 'session_1755676765762', limit: int = 3) -> dict:
    """获取每个分类的样本句子"""
    
    config = get_database_config()
    samples = {}
    
    # 定义分类和对应的搜索关键词
    categories = {
        'why_need_human': [
            'Cognitive judgment', 'Creativity', 'External world interaction', 
            'Domain expertise knowledge', 'Private domain information', 
            'Preference constraints', 'Responsibility scope', 'User-authorizable content'
        ],
        'when_need_human': [
            'Decision-making needs', 'Innovation needs', 'Execution needs',
            'Professional knowledge needs', 'Private information needs',
            'Personal preference needs', 'Responsibility assumption needs', 'User authorization needs'
        ],
        'interaction_behavior': [
            'Prime', 'Configure', 'Probe', 'Cue', 'Elicit', 'Augment',
            'Guide', 'Critique', 'Explain', 'Correct', 'Reflect', 'Approve'
        ],
        'communication_principle': [
            'Echoing responses', 'Casual language', 'Feedback', 'Using emoji',
            'Encourage', 'Emphatic messages', 'Humor', 'Present capabilities',
            'Acknowledge limitations', 'Repetitive messages', 'Exaggeration'
        ]
    }
    
    try:
        connection = MySQLdb.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            passwd=config['password'],
            db=config['database'],
            charset=config['charset']
        )
        cursor = connection.cursor()
        
        for category, items in categories.items():
            samples[category] = {}
            for item in items:
                query = f"""
                SELECT 
                    content,
                    llm_response_content,
                    id
                FROM messages 
                WHERE session_id = %s 
                AND CONVERT(JSON_EXTRACT(llm_response_content, '$.\"{category}\"'), CHAR) LIKE %s
                LIMIT %s
                """
                
                cursor.execute(query, (session_id, f'%{item}%', limit))
                results = cursor.fetchall()
                
                if results:
                    samples[category][item] = []
                    for row in results:
                        samples[category][item].append({
                            'user_input': row[0],
                            'llm_response': row[1],
                            'message_id': row[2]
                        })
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"获取样本句子时出错: {e}")
        
    return samples

def save_sample_sentences(samples: dict, session_id: str):
    """保存样本句子到JSON文件"""
    if not samples:
        return
    
    # 格式化样本数据用于保存
    formatted_samples = {}
    for category, items in samples.items():
        formatted_samples[category] = {}
        for item_name, messages in items.items():
            if messages:
                formatted_samples[category][item_name] = []
                for msg in messages:
                    # 尝试解析JSON响应
                    try:
                        response_data = json.loads(msg['llm_response'])
                        classification_result = response_data.get(category, "未找到分类")
                    except:
                        classification_result = "JSON解析失败"
                    
                    formatted_samples[category][item_name].append({
                        'message_id': msg['message_id'],
                        'user_input': msg['user_input'],
                        'classification_result': classification_result,
                        'full_response': msg['llm_response']
                    })
    
    # 保存到文件
    filename = f'sample_sentences_{session_id}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(formatted_samples, f, ensure_ascii=False, indent=2)
    
    print(f"样本句子已保存到: {filename}")

def print_sample_sentences(samples: dict):
    """打印样本句子用于验证标签"""
    if not samples:
        print("没有找到样本数据")
        return
    
    print("\n" + "="*80)
    print("样本句子检查 - 用于验证标签准确性")
    print("="*80)
    
    for category, items in samples.items():
        print(f"\n【{category.upper()}】")
        print("-" * 60)
        
        for item_name, messages in items.items():
            if not messages:
                continue
                
            print(f"\n  ➤ {item_name}")
            print("  " + "-" * 40)
            
            for i, msg in enumerate(messages, 1):
                print(f"\n    示例 {i}:")
                print(f"    用户输入: {msg['user_input'][:100]}...")
                
                # 尝试解析JSON响应以显示相关分类
                try:
                    response_data = json.loads(msg['llm_response'])
                    if category in response_data:
                        print(f"    分类结果: {response_data[category]}")
                except:
                    print(f"    原始响应: {msg['llm_response'][:150]}...")
                
                print(f"    消息ID: {msg['message_id']}")

def print_2d_array(array_2d: List[List]):
    """打印真正的二维数组格式"""
    if not array_2d:
        print("没有数据")
        return
    
    print("# 二维数组:")
    print("[")
    for i, row in enumerate(array_2d):
        if i == len(array_2d) - 1:
            print(f"    {row}")
        else:
            print(f"    {row},")
    print("]")

def main():
    """主函数"""
    import sys
    
    # 获取命令行参数
    session_id = sys.argv[1] if len(sys.argv) > 1 else 'session_1756395812371'
    show_samples = '--samples' in sys.argv or '-s' in sys.argv
    
    print(f"正在查询会话: {session_id}")
    
    # 执行查询
    results = execute_query(session_id)
    
    if not results:
        print("没有找到数据")
        return
    
    # 格式化为二维数组
    array_2d = format_as_2d_array(results)
    
    # 打印二维数组
    print("\n=== 查询结果二维数组 ===")
    print_2d_array(array_2d)
    
    # 保存文件
    save_as_csv(array_2d, f'word_frequency_{session_id}.csv')
    save_as_json(array_2d, f'word_frequency_{session_id}.json')
    
    # 打印统计信息
    total_records = len(array_2d)  # 不减去表头，因为没有表头了
    total_count = sum(row[2] for row in array_2d if isinstance(row[2], int))
    
    print(f"\n=== 统计信息 ===")
    print(f"总项目数: {total_records}")
    print(f"总出现次数: {total_count}")
    
    # 按分类统计
    categories = {}
    for row in array_2d:
        category = row[0]
        count = row[2] if isinstance(row[2], int) else 0
        categories[category] = categories.get(category, 0) + count
    
    print("\n=== 按分类统计 ===")
    for category, count in categories.items():
        print(f"{category}: {count}")
    
    # 获取并显示样本句子（默认显示，或通过参数控制）
    if show_samples or True:  # 默认总是显示样本
        print("\n正在获取样本句子...")
        samples = get_sample_sentences(session_id, limit=2)  # 每个分类显示2个样本
        print_sample_sentences(samples)
        save_sample_sentences(samples, session_id)

if __name__ == "__main__":
    main()
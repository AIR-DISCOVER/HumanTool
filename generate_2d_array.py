#!/usr/bin/env python3
"""
执行SQL查询并生成二维数组格式的输出
"""
import MySQLdb
import os
import csv
import json
from typing import List, Tuple

def get_database_config():
    """获取数据库配置"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3307)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '123456'),
        'database': os.getenv('DB_NAME', 'tata'),
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
    
    # 直接返回数据，不包含表头
    array_2d = []
    for row in results:
        array_2d.append([row[0], row[1], row[2]])
    
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
    session_id = sys.argv[1] if len(sys.argv) > 1 else 'session_1756034865766'
    
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

if __name__ == "__main__":
    main()
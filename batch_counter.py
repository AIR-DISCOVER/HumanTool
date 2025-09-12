#!/usr/bin/env python3
"""
批量统计多个session的标签计数并求和
"""
import MySQLdb
from typing import List, Tuple, Dict
from collections import defaultdict

def get_database_config():
    """获取数据库配置"""
    return {
        'host': '127.0.0.1',
        'port': 3044,
        'user': 'root',
        'password': '123456',
        'database': 'tata',
        'charset': 'utf8mb4'
    }

def execute_query(session_id: str) -> List[Tuple]:
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
        print(f"数据库错误 (session {session_id}): {e}")
        return []

def process_session(session_id: str) -> Dict[str, Dict[str, int]]:
    """处理单个session并返回统计结果"""
    results = execute_query(session_id)
    
    if not results:
        print(f"Session {session_id}: 没有找到数据")
        return {}
    
    # 按分类和项目统计
    stats = defaultdict(lambda: defaultdict(int))
    total_count = 0
    
    for row in results:
        category = row[0]
        item = row[1]
        count = int(row[2]) if row[2] is not None else 0
        
        stats[category][item] += count
        total_count += count
    
    print(f"Session {session_id}: {len(results)} 项目, 总计 {total_count} 次")
    
    return dict(stats)

def main():
    """主函数"""
    
    session_ids = [
        'session_1757148427117',
        'session_1757240111261', 
        'session_1757223264274',
        'session_1757210754513',
        'session_1757159269178',
        'session_1757155563871',
        'session_1757055901701',
        'session_1757049167426',
        'session_1757037152938',  # 重复的session
        'session_1756991125108',
        'session_1756968612455',
        'session_1757232535608',
        'session_1757130985558',
        'session_1756981395207',
        'session_1756986741446',
        'session_1757074163220'
    ]
    
    # 去重session列表
    unique_sessions = list(set(session_ids))
    print(f"处理 {len(unique_sessions)} 个唯一session (原列表有 {len(session_ids)} 个)")
    
    # 累积统计
    total_stats = defaultdict(lambda: defaultdict(int))
    total_sessions_processed = 0
    total_items = 0
    grand_total_count = 0
    
    print("\n=== 处理各个session ===")
    for session_id in unique_sessions:
        session_stats = process_session(session_id)
        
        if session_stats:
            total_sessions_processed += 1
            
            # 累加到总统计中
            for category, items in session_stats.items():
                for item, count in items.items():
                    total_stats[category][item] += count
                    grand_total_count += count
                    total_items += 1
    
    print(f"\n=== 最终汇总结果 ===")
    print(f"成功处理的session数: {total_sessions_processed}")
    print(f"总项目数: {total_items}")  
    print(f"总出现次数: {grand_total_count}")
    
    print(f"\n=== 按分类汇总统计 ===")
    category_totals = {}
    for category, items in total_stats.items():
        category_total = sum(items.values())
        category_totals[category] = category_total
        print(f"{category}: {category_total}")
    
    print(f"\n=== 详细项目统计 ===")
    for category in sorted(total_stats.keys()):
        print(f"\n【{category}】")
        for item in sorted(total_stats[category].keys()):
            count = total_stats[category][item]
            print(f"  {item}: {count}")

if __name__ == "__main__":
    main()
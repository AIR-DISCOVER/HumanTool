#!/usr/bin/env python3
"""
测试数据库连接
"""
import MySQLdb
import os

def test_connection():
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3307)),
        'user': os.getenv('DB_USER', 'root'),
        'passwd': os.getenv('DB_PASSWORD', '123456'),
        'db': os.getenv('DB_NAME', 'tata'),
        'charset': 'utf8mb4'
    }
    
    try:
        print(f"尝试连接到: {config['user']}@{config['host']}:{config['port']}/{config['db']}")
        connection = MySQLdb.connect(**config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = 'session_1755676765762'")
        count = cursor.fetchone()[0]
        
        print(f"连接成功！找到 {count} 条记录")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"连接失败: {e}")
        return False

if __name__ == "__main__":
    test_connection()
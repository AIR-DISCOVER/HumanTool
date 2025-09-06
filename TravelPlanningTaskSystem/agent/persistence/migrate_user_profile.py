#!/usr/bin/env python3
"""
数据库迁移脚本：为users表添加overall_profile和last_updated字段
"""

import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

def get_database_url():
    """获取数据库连接URL"""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3307")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "123456")
    db_name = os.getenv("DB_NAME", "tata")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

def migrate_database():
    """执行数据库迁移"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, echo=True)
        
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'overall_profile'"))
            if result.fetchone():
                print("✅ overall_profile字段已存在，跳过添加")
            else:
                print("🔄 添加overall_profile字段...")
                conn.execute(text("ALTER TABLE users ADD COLUMN overall_profile TEXT"))
                print("✅ overall_profile字段添加成功")
            
            result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'last_updated'"))
            if result.fetchone():
                print("✅ last_updated字段已存在，跳过添加")
            else:
                print("🔄 添加last_updated字段...")
                conn.execute(text("ALTER TABLE users ADD COLUMN last_updated DATETIME"))
                print("✅ last_updated字段添加成功")
            
            # 提交更改
            conn.commit()
            
            # 更新现有用户的last_updated字段
            print("🔄 更新现有用户的last_updated字段...")
            conn.execute(text("UPDATE users SET last_updated = NOW() WHERE last_updated IS NULL"))
            conn.commit()
            print("✅ 现有用户的last_updated字段更新完成")
            
        print("🎉 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 开始数据库迁移 ===")
    success = migrate_database()
    if success:
        print("=== 迁移成功完成 ===")
        sys.exit(0)
    else:
        print("=== 迁移失败 ===")
        sys.exit(1)
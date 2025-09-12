"""
删除实验用户脚本
安全删除指定的实验用户数据
"""

import os
import sys
import pymysql
import json
from datetime import datetime
from dotenv import load_dotenv

def load_environment():
    """加载环境变量"""
    env_path = os.path.join(os.path.dirname(__file__), "agent", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ 加载环境变量文件: {env_path}")
        return True
    else:
        print(f"❌ 环境变量文件不存在: {env_path}")
        return False

def get_database_config():
    """获取数据库配置"""
    config = {
        'host': os.getenv("DB_HOST", "localhost"),
        'port': int(os.getenv("DB_PORT", "3307")),
        'user': os.getenv("DB_USER", "root"),
        'password': os.getenv("DB_PASSWORD", "123456"),
        'database': os.getenv("DB_NAME", "tata"),
        'charset': 'utf8mb4'
    }
    
    print(f"📁 数据库配置: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
    return config

def test_connection(config):
    """测试数据库连接"""
    try:
        connection = pymysql.connect(**config, connect_timeout=5)
        print("✅ 数据库连接成功")
        connection.close()
        return True
    except pymysql.Error as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

def backup_users_data(connection, user_ids):
    """备份要删除的用户数据"""
    try:
        with connection.cursor() as cursor:
            backup_table = f"deleted_users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 构建用户ID列表的SQL占位符
            placeholders = ', '.join(['%s'] * len(user_ids))
            
            # 创建备份表并复制数据
            cursor.execute(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM users 
                WHERE id IN ({placeholders})
            """, user_ids)
            
            # 检查备份数据量
            cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
            backup_count = cursor.fetchone()[0]
            
            print(f"✅ 已备份 {backup_count} 个用户到表 {backup_table}")
            return backup_table
            
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def check_user_dependencies(connection, user_ids):
    """检查用户相关的依赖数据"""
    try:
        with connection.cursor() as cursor:
            print(f"🔍 检查用户依赖数据...")
            
            dependencies = {}
            
            for user_id in user_ids:
                user_deps = {}
                
                # 检查会话数据
                cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id = %s", (user_id,))
                session_count = cursor.fetchone()[0]
                user_deps['sessions'] = session_count
                
                # 检查消息数据
                cursor.execute("""
                    SELECT COUNT(*) FROM messages m 
                    JOIN sessions s ON m.session_id = s.id 
                    WHERE s.user_id = %s
                """, (user_id,))
                message_count = cursor.fetchone()[0]
                user_deps['messages'] = message_count
                
                dependencies[user_id] = user_deps
                
                if session_count > 0 or message_count > 0:
                    print(f"⚠️ 用户 {user_id} 有关联数据: {session_count} 个会话, {message_count} 条消息")
                else:
                    print(f"✅ 用户 {user_id} 无关联数据，可安全删除")
            
            return dependencies
            
    except Exception as e:
        print(f"❌ 检查依赖数据失败: {e}")
        return None

def delete_user_dependencies(connection, user_ids):
    """删除用户相关的依赖数据"""
    try:
        with connection.cursor() as cursor:
            print(f"🗑️ 删除用户相关数据...")
            
            for user_id in user_ids:
                # 删除消息数据
                cursor.execute("""
                    DELETE m FROM messages m 
                    JOIN sessions s ON m.session_id = s.id 
                    WHERE s.user_id = %s
                """, (user_id,))
                deleted_messages = cursor.rowcount
                
                # 删除会话数据
                cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
                deleted_sessions = cursor.rowcount
                
                if deleted_messages > 0 or deleted_sessions > 0:
                    print(f"   - {user_id}: 删除 {deleted_sessions} 个会话, {deleted_messages} 条消息")
            
            print(f"✅ 用户关联数据删除完成")
            return True
            
    except Exception as e:
        print(f"❌ 删除关联数据失败: {e}")
        return False

def delete_users(connection, user_ids):
    """删除指定用户"""
    try:
        with connection.cursor() as cursor:
            print(f"🗑️ 删除用户...")
            
            # 先查询要删除的用户信息
            placeholders = ', '.join(['%s'] * len(user_ids))
            cursor.execute(f"""
                SELECT id, display_name, user_type, experiment_group 
                FROM users 
                WHERE id IN ({placeholders})
            """, user_ids)
            
            users_to_delete = cursor.fetchall()
            
            if not users_to_delete:
                print("ℹ️ 没有找到要删除的用户")
                return True
            
            print(f"📋 将要删除的用户:")
            for user in users_to_delete:
                print(f"   - {user[0]}: {user[1]} ({user[2]}, 组别: {user[3]})")
            
            # 执行删除
            cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", user_ids)
            deleted_count = cursor.rowcount
            
            print(f"✅ 成功删除 {deleted_count} 个用户")
            return True
            
    except Exception as e:
        print(f"❌ 删除用户失败: {e}")
        return False

def verify_deletion(connection, user_ids):
    """验证删除结果"""
    try:
        with connection.cursor() as cursor:
            # 检查用户是否还存在
            placeholders = ', '.join(['%s'] * len(user_ids))
            cursor.execute(f"""
                SELECT id, display_name FROM users 
                WHERE id IN ({placeholders})
            """, user_ids)
            
            remaining_users = cursor.fetchall()
            
            if remaining_users:
                print(f"❌ 以下用户删除失败，仍然存在:")
                for user in remaining_users:
                    print(f"   - {user[0]}: {user[1]}")
                return False
            else:
                print(f"✅ 所有指定用户已成功删除")
                
            # 显示剩余用户
            cursor.execute("SELECT id, display_name, user_type FROM users ORDER BY id")
            remaining_all_users = cursor.fetchall()
            
            print(f"\n📋 当前剩余用户 ({len(remaining_all_users)} 个):")
            for user in remaining_all_users:
                print(f"   - {user[0]}: {user[1]} ({user[2]})")
            
            return True
            
    except Exception as e:
        print(f"❌ 验证删除结果失败: {e}")
        return False

def main():
    """主函数"""
    print("🗑️ 删除实验用户脚本")
    print("=" * 50)
    
    # 要删除的用户ID列表
    users_to_delete = [
        'user_1',      # 专业创作者
        'web_user',     # Web用户
        # 'user_intermediate', # 进阶创作者  
        # 'user_novice'       # 新手创作者
    ]
    
    print(f"🎯 目标用户: {users_to_delete}")
    
    # 1. 加载环境变量
    if not load_environment():
        print("⚠️ 使用默认配置继续...")
    
    # 2. 获取数据库配置
    config = get_database_config()
    
    # 3. 测试连接
    if not test_connection(config):
        print("💡 请检查:")
        print("   1. MySQL服务是否启动")
        print("   2. 环境变量配置是否正确")
        print("   3. 端口号是否正确")
        return
    
    # 4. 连接数据库并执行删除
    try:
        connection = pymysql.connect(**config)
        connection.autocommit(False)  # 使用事务
        
        print("\n🔍 检查要删除的用户...")
        
        with connection.cursor() as cursor:
            # 检查用户是否存在
            placeholders = ', '.join(['%s'] * len(users_to_delete))
            cursor.execute(f"""
                SELECT id, display_name, user_type, experiment_group 
                FROM users 
                WHERE id IN ({placeholders})
            """, users_to_delete)
            
            existing_users = cursor.fetchall()
            
            if not existing_users:
                print("ℹ️ 没有找到要删除的用户，可能已经被删除")
                return
            
            print(f"📋 找到 {len(existing_users)} 个用户:")
            for user in existing_users:
                print(f"   - {user[0]}: {user[1]} ({user[2]}, 组别: {user[3]})")
        
        # 5. 确认删除
        print(f"\n⚠️ 警告: 此操作将永久删除用户及其所有相关数据!")
        confirmation = input("确认删除以上用户吗？(输入 'DELETE' 确认): ").strip()
        
        if confirmation != 'DELETE':
            print("❌ 用户取消操作")
            return
        
        print("\n📝 开始删除操作...")
        
        try:
            # 6. 备份用户数据
            backup_table = backup_users_data(connection, users_to_delete)
            if not backup_table:
                print("⚠️ 备份失败，但继续删除...")
            
            # 7. 检查依赖数据
            dependencies = check_user_dependencies(connection, users_to_delete)
            
            # 8. 删除依赖数据
            if not delete_user_dependencies(connection, users_to_delete):
                print("⚠️ 删除关联数据失败，但继续删除用户...")
            
            # 9. 删除用户
            if not delete_users(connection, users_to_delete):
                connection.rollback()
                print("❌ 删除用户失败，已回滚")
                return
            
            # 10. 提交事务
            connection.commit()
            print("✅ 删除操作已提交")
            
            # 11. 验证删除结果
            print("\n🔍 验证删除结果...")
            verify_deletion(connection, users_to_delete)
            
        except Exception as e:
            connection.rollback()
            print(f"❌ 删除过程中出错，已回滚: {e}")
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
    finally:
        if 'connection' in locals():
            connection.close()
            print("\n📊 数据库连接已关闭")
    
    print("\n" + "=" * 50)
    print("🎉 删除操作完成！")

if __name__ == "__main__":
    main()
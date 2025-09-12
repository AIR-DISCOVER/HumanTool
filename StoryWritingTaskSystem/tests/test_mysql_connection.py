import os
import sys
import pymysql
from dotenv import load_dotenv

def test_mysql_connection():
    """测试MySQL连接"""
    
    # 加载环境变量
    env_path = os.path.join("agent", ".env")
    load_dotenv(env_path)
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "tata")
    
    print(f"🔧 测试MySQL连接...")
    print(f"   主机: {db_host}:{db_port}")
    print(f"   用户: {db_user}")
    print(f"   密码: {'*' * len(db_password) if db_password else '(空)'}")
    print(f"   数据库: {db_name}")
    
    if not db_user or not db_password:
        print("❌ 请先在 agent/.env 中设置 DB_USER 和 DB_PASSWORD")
        return False
    
    try:
        # 首先尝试连接MySQL服务器（不指定数据库）
        connection = pymysql.connect( 
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            charset='utf8mb4'
        )
        
        print("✅ MySQL服务器连接成功！")
        
        with connection.cursor() as cursor:
            # 获取MySQL版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"   MySQL版本: {version[0]}")
            
            # 检查数据库是否存在
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            print(f"   现有数据库: {databases}")
            
            # 创建数据库如果不存在
            if db_name not in databases:
                cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ 创建数据库 '{db_name}' 成功")
            else:
                print(f"✅ 数据库 '{db_name}' 已存在")
        
        connection.close()
        
        # 测试连接到指定数据库
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        print(f"✅ 数据库 '{db_name}' 连接成功！")
        connection.close()
        
        return True
        
    except pymysql.err.OperationalError as e:
        if "Access denied" in str(e):
            print(f"❌ 认证失败: 用户名或密码错误")
            print("💡 请检查 DB_USER 和 DB_PASSWORD 设置")
        elif "Can't connect to MySQL server" in str(e):
            print(f"❌ 无法连接到MySQL服务器")
            print("💡 请确认MySQL服务已启动，或使用Docker运行MySQL：")
            print("   docker run --name mysql-tata -e MYSQL_ROOT_PASSWORD=123456 -e MYSQL_DATABASE=tata -p 3306:3306 -d mysql:8.0")
        else:
            print(f"❌ 连接错误: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    
    if success:
        print("\n🎉 MySQL配置成功！现在可以运行：")
        print("   python db_setup.py")
        print("   python -m server.main")
    else:
        print("\n❌ MySQL配置失败，请按照提示修复问题")
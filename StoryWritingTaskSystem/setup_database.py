"""
生产环境数据库部署脚本
包含完整的环境检查和错误处理
"""

import os
import sys
import pymysql
import json
from datetime import datetime
from dotenv import load_dotenv

class DatabaseDeployer:
    def __init__(self):
        self.config = None
        self.verbose = True
    
    def load_environment(self):
        """加载环境变量"""
        env_path = os.path.join(os.path.dirname(__file__), "agent", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ 加载环境变量: {env_path}")
            return True
        else:
            print(f"❌ 环境变量文件不存在: {env_path}")
            return False
    
    def get_database_config(self):
        """获取数据库配置"""
        self.config = {
            'host': os.getenv("DB_HOST", "localhost"),
            'port': int(os.getenv("DB_PORT", "3307")),
            'user': os.getenv("DB_USER", "root"),
            'password': os.getenv("DB_PASSWORD", "123456"),
            'database': os.getenv("DB_NAME", "tata"),
            'charset': 'utf8mb4'
        }
        print(f"📋 数据库配置: {self.config['user']}@{self.config['host']}:{self.config['port']}/{self.config['database']}")
        return self.config
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            test_config = self.config.copy()
            del test_config['database']
            
            connection = pymysql.connect(**test_config, connect_timeout=10)
            print("✅ MySQL 服务器连接成功")
            connection.close()
            return True
        except Exception as e:
            print(f"❌ MySQL 连接失败: {e}")
            return False
    
    def check_database_exists(self):
        """检查数据库是否存在"""
        try:
            test_config = self.config.copy()
            del test_config['database']
            
            connection = pymysql.connect(**test_config)
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW DATABASES LIKE '{self.config['database']}'")
                exists = cursor.fetchone() is not None
            connection.close()
            
            if exists:
                print(f"📁 数据库 '{self.config['database']}' 已存在")
            else:
                print(f"📁 数据库 '{self.config['database']}' 不存在，将创建")
            return exists
        except Exception as e:
            print(f"❌ 检查数据库失败: {e}")
            return False
    
    def deploy_fresh_database(self):
        """部署全新数据库"""
        print("\n🚀 开始全新数据库部署...")
        
        sql_file = os.path.join(os.path.dirname(__file__), "database", "init.sql")
        if not os.path.exists(sql_file):
            print(f"❌ 生产环境SQL文件不存在: {sql_file}")
            return False
        
        return self.execute_sql_file(sql_file)
    
    def upgrade_existing_database(self):
        """升级现有数据库"""
        print("\n📈 开始数据库升级...")
        
        try:
            connection = pymysql.connect(**self.config)
            connection.autocommit(False)
            
            with connection.cursor() as cursor:
                # 检查表结构
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'users' not in tables:
                    print("❌ 用户表不存在，需要全新部署")
                    connection.close()
                    return False
                
                # 检查新字段
                cursor.execute("DESCRIBE users")
                columns = [row[0] for row in cursor.fetchall()]
                
                needed_fields = ['overall_profile', 'information_capabilities', 'reasoning_capabilities', 'last_updated']
                missing_fields = [field for field in needed_fields if field not in columns]
                
                if missing_fields:
                    print(f"📝 需要添加字段: {missing_fields}")
                    # 执行升级脚本
                    upgrade_file = os.path.join(os.path.dirname(__file__), "upgrade_user_profile_v2.py")
                    if os.path.exists(upgrade_file):
                        print("🔧 执行升级脚本...")
                        import subprocess
                        result = subprocess.run([sys.executable, upgrade_file], capture_output=True, text=True)
                        if result.returncode == 0:
                            print("✅ 升级完成")
                            return True
                        else:
                            print(f"❌ 升级失败: {result.stderr}")
                            return False
                    else:
                        print("❌ 升级脚本不存在")
                        return False
                else:
                    print("✅ 数据库结构已是最新")
                    return True
            
            connection.close()
            
        except Exception as e:
            print(f"❌ 升级过程失败: {e}")
            return False
    
    def execute_sql_file(self, sql_file_path):
        """执行SQL文件"""
        try:
            test_config = self.config.copy()
            del test_config['database']
            
            connection = pymysql.connect(**test_config)
            
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割并执行SQL语句
            statements = []
            current_statement = ""
            
            for line in sql_content.split('\n'):
                line = line.strip()
                if line.startswith('--') or not line:
                    continue
                
                current_statement += line + " "
                if line.endswith(';'):
                    statements.append(current_statement.strip())
                    current_statement = ""
            
            with connection.cursor() as cursor:
                success_count = 0
                for statement in statements:
                    try:
                        if statement.strip():
                            cursor.execute(statement)
                            success_count += 1
                            
                            if "CREATE DATABASE" in statement.upper():
                                print(f"   ✅ 创建数据库")
                            elif "CREATE TABLE" in statement.upper():
                                table_match = statement.upper().split('TABLE')[1].split('(')[0].strip()
                                if 'IF NOT EXISTS' in table_match:
                                    table_name = table_match.replace('IF NOT EXISTS', '').strip()
                                else:
                                    table_name = table_match
                                print(f"   ✅ 创建表: {table_name}")
                            elif "INSERT INTO" in statement.upper():
                                print(f"   ✅ 插入数据")
                    except Exception as e:
                        if 'already exists' not in str(e).lower():
                            print(f"   ⚠️ SQL执行警告: {str(e)[:100]}")
            
            connection.commit()
            connection.close()
            print(f"✅ 成功执行 {success_count} 条SQL语句")
            return True
            
        except Exception as e:
            print(f"❌ SQL执行失败: {e}")
            return False
    
    def verify_deployment(self):
        """验证部署结果"""
        print("\n🔍 验证部署结果...")
        
        try:
            connection = pymysql.connect(**self.config)
            
            with connection.cursor() as cursor:
                # 检查表
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['users', 'sessions', 'messages', 'drafts']
                print(f"📋 表结构检查:")
                for table in expected_tables:
                    if table in tables:
                        print(f"   ✅ {table}")
                    else:
                        print(f"   ❌ {table} - 缺失")
                
                # 检查用户数据
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT id, display_name, user_type,
                           CASE WHEN overall_profile IS NOT NULL THEN '✅' ELSE '❌' END as has_profile,
                           JSON_LENGTH(information_capabilities) as info_count,
                           JSON_LENGTH(reasoning_capabilities) as reasoning_count
                    FROM users
                    ORDER BY user_type, id
                """)
                
                users = cursor.fetchall()
                print(f"\n👥 用户数据检查 ({user_count} 个用户):")
                for user in users:
                    info_count = user[4] if user[4] is not None else 0
                    reasoning_count = user[5] if user[5] is not None else 0
                    print(f"   {user[3]} {user[0]} - {user[1]} ({user[2]}) | 能力: {info_count}+{reasoning_count}")
                
                # 检查视图
                cursor.execute("SHOW TABLES LIKE 'v_%'")
                views = [row[0] for row in cursor.fetchall()]
                print(f"\n📊 视图检查:")
                for view in views:
                    print(f"   ✅ {view}")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False
    
    def deploy(self):
        """主部署流程"""
        print("🚀 TATA 生产环境数据库部署")
        print("=" * 60)
        
        # 1. 环境检查
        if not self.load_environment():
            print("⚠️ 使用默认配置继续...")
        
        self.get_database_config()
        
        # 2. 连接测试
        if not self.test_connection():
            print("❌ 部署终止：无法连接MySQL服务器")
            return False
        
        # 3. 检查数据库状态
        db_exists = self.check_database_exists()
        
        # 4. 选择部署策略
        if not db_exists:
            success = self.deploy_fresh_database()
        else:
            print("\n💡 检测到已有数据库，选择操作:")
            print("   1. 全新部署（删除所有数据）")
            print("   2. 增量升级（保留现有数据）")
            
            choice = input("请选择 (1/2): ").strip()
            
            if choice == '1':
                confirm = input("⚠️ 警告：这将删除所有现有数据！确认吗？(输入 'DELETE' 确认): ").strip()
                if confirm == 'DELETE':
                    success = self.deploy_fresh_database()
                else:
                    print("❌ 用户取消操作")
                    return False
            elif choice == '2':
                success = self.upgrade_existing_database()
            else:
                print("❌ 无效选择")
                return False
        
        # 5. 验证结果
        if success:
            if self.verify_deployment():
                print("\n🎉 数据库部署成功！")
                print("💡 现在可以启动服务器了")
                return True
            else:
                print("\n⚠️ 部署完成但验证发现问题")
                return False
        else:
            print("\n❌ 数据库部署失败")
            return False

def main():
    deployer = DatabaseDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n📋 下一步:")
        print("   1. 启动服务器: cd server && python main.py")
        print("   2. 访问: http://localhost:8000")
        print("   3. 检查日志确认所有功能正常")
    else:
        print("\n💡 部署失败，请检查:")
        print("   1. MySQL服务是否正常运行")
        print("   2. 环境变量配置是否正确")
        print("   3. 数据库权限是否充足")

if __name__ == "__main__":
    main()
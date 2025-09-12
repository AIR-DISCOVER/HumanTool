"""
用户档案结构升级脚本 v2.0
将用户能力字段升级为更详细的专业档案结构
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
    return config

def backup_existing_data(connection):
    """备份现有用户数据"""
    try:
        with connection.cursor() as cursor:
            backup_table = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM users")
            cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
            backup_count = cursor.fetchone()[0]
            
            print(f"✅ 已备份 {backup_count} 个用户到表 {backup_table}")
            return backup_table
            
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def add_new_profile_fields(connection):
    """添加新的用户档案字段"""
    try:
        with connection.cursor() as cursor:
            print("📝 添加新的用户档案字段...")
            
            # 检查现有字段
            cursor.execute("DESCRIBE users")
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # 新字段定义
            new_fields = {
                'overall_profile': 'TEXT COMMENT "用户总体档案描述"',
                'information_capabilities': 'JSON COMMENT "信息能力列表"',
                'reasoning_capabilities': 'JSON COMMENT "推理能力列表"',
                'last_updated': 'DATE COMMENT "档案最后更新时间"'
            }
            
            # 添加缺失字段
            for field_name, field_definition in new_fields.items():
                if field_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_definition}"
                        cursor.execute(sql)
                        print(f"   ✅ 添加字段: {field_name}")
                    except Exception as e:
                        print(f"   ❌ 添加字段 {field_name} 失败: {e}")
                else:
                    print(f"   ⚠️ 字段 {field_name} 已存在")
            
            return True
            
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        return False

def migrate_user_profiles(connection):
    """迁移和更新用户档案数据"""
    try:
        with connection.cursor() as cursor:
            print("📝 迁移用户档案数据...")
            
            # 🎯 新的专业用户档案数据
            enhanced_user_profiles = {
                'user_tyr1': {
                    'name': '唐旋',
                    'display_name': '唐旋',
                    'user_type': 'admin',
                    'experiment_group': 'admin',
                    "overall_profile": "具有3年视觉设计经验的海报设计师，擅长品牌视觉表达和创意概念呈现，对平面设计和视觉传达有深度理解",
                    
                    "information_capabilities": [
                        "品牌视觉策略制定：基于3年实践经验，能够提供品牌调性分析、视觉风格定位、色彩搭配建议等专业意见，适用于海报概念设计和视觉风格确认场景",
                        "目标受众洞察表达：深度了解不同受众群体的视觉偏好和审美趋势，能够在设计评审和风格选择中提供精准的受众匹配建议和视觉传达策略"
                    ],
                    
                    "reasoning_capabilities": [
                        "视觉层次价值评估：基于设计原则评估版面布局的视觉冲击力，在构图设计和信息层级中提供专业的视觉优化建议",
                        "创意表达平衡决策：在多重设计约束下平衡创意表达与信息传达，为设计元素选择和视觉重点提供合理的创意决策和优先级排序"
                    ],
                    
                    "last_updated": "2025-06-19"
                },
                
                'user_main': {
                    'name': '默认用户',
                    'display_name': '通用协作者',
                    'user_type': 'general',
                    'experiment_group': 'Control',
                    'overall_profile': '通用创作协作者，具备多元化背景和灵活适应能力，能够在不同领域提供支持和反馈',
                    'information_capabilities': [
                        "通用知识整合：具备跨领域知识背景，能够整合不同来源的信息，适用于初步研究和信息收集场景",
                        "多角度分析：能够从不同视角分析问题，在头脑风暴和创意讨论中提供多元化观点和建议"
                    ],
                    'reasoning_capabilities': [
                        "逻辑梳理：具备基础的逻辑分析能力，能够梳理问题结构和关系，适用于思路整理和方案对比",
                        "实用性评估：从使用者角度评估方案的可行性和实用性，为决策提供接地气的反馈和建议"
                    ],
                    'last_updated': '2025-06-19'
                },
            }
            
            # 更新每个用户的档案
            updated_count = 0
            for user_id, profile in enhanced_user_profiles.items():
                try:
                    # 检查用户是否存在
                    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                    user_exists = cursor.fetchone()
                    
                    if not user_exists:
                        # 创建新用户
                        sql = """
                            INSERT INTO users (
                                id, name, display_name, user_type, experiment_group,
                                overall_profile, information_capabilities, reasoning_capabilities, 
                                last_updated, `accessible`, created_at, updated_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                            )
                        """
                        values = (
                            user_id,
                            profile['name'],
                            profile['display_name'],
                            profile['user_type'],
                            profile['experiment_group'],
                            profile['overall_profile'],
                            json.dumps(profile['information_capabilities'], ensure_ascii=False),
                            json.dumps(profile['reasoning_capabilities'], ensure_ascii=False),
                            profile['last_updated'],
                            True
                        )
                        cursor.execute(sql, values)
                        print(f"✅ 创建用户: {user_id} - {profile['display_name']}")
                    else:
                        # 更新现有用户
                        sql = """
                            UPDATE users SET 
                                name = %s,
                                display_name = %s,
                                user_type = %s,
                                experiment_group = %s,
                                overall_profile = %s,
                                information_capabilities = %s,
                                reasoning_capabilities = %s,
                                last_updated = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """
                        values = (
                            profile['name'],
                            profile['display_name'],
                            profile['user_type'],
                            profile['experiment_group'],
                            profile['overall_profile'],
                            json.dumps(profile['information_capabilities'], ensure_ascii=False),
                            json.dumps(profile['reasoning_capabilities'], ensure_ascii=False),
                            profile['last_updated'],
                            user_id
                        )
                        cursor.execute(sql, values)
                        print(f"✅ 更新用户: {user_id} - {profile['display_name']}")
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"❌ 处理用户 {user_id} 失败: {e}")
                    continue
            
            print(f"✅ 成功处理 {updated_count} 个用户档案")
            return True
            
    except Exception as e:
        print(f"❌ 迁移用户档案失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration(connection):
    """验证迁移结果"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, display_name, user_type, experiment_group,
                       overall_profile, last_updated
                FROM users 
                ORDER BY id
            """)
            
            users = cursor.fetchall()
            print(f"\n📋 迁移验证结果 - 共 {len(users)} 个用户:")
            
            for user in users:
                print(f"\n👤 {user[0]} - {user[1]}")
                print(f"   类型: {user[2]} | 组别: {user[3]}")
                profile_preview = user[4][:80] + "..." if user[4] and len(user[4]) > 80 else user[4]
                print(f"   档案: {profile_preview}")
                print(f"   更新: {user[5]}")
            
            # 验证新字段的数据完整性
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN overall_profile IS NOT NULL THEN 1 ELSE 0 END) as has_profile,
                       SUM(CASE WHEN information_capabilities IS NOT NULL THEN 1 ELSE 0 END) as has_info,
                       SUM(CASE WHEN reasoning_capabilities IS NOT NULL THEN 1 ELSE 0 END) as has_reasoning
                FROM users
            """)
            
            stats = cursor.fetchone()
            print(f"\n📊 数据完整性统计:")
            print(f"   总用户数: {stats[0]}")
            print(f"   有档案描述: {stats[1]}")
            print(f"   有信息能力: {stats[2]}")
            print(f"   有推理能力: {stats[3]}")
            
            return True
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 用户档案结构升级脚本 v2.0")
    print("=" * 60)
    
    # 1. 加载环境变量
    if not load_environment():
        print("⚠️ 使用默认配置继续...")
    
    # 2. 获取数据库配置
    config = get_database_config()
    
    # 3. 连接数据库并执行升级
    try:
        connection = pymysql.connect(**config)
        connection.autocommit(False)  # 使用事务
        
        print("\n📝 开始用户档案结构升级...")
        
        try:
            # 备份现有数据
            backup_table = backup_existing_data(connection)
            if not backup_table:
                print("⚠️ 备份失败，但继续升级...")
            
            # 添加新字段
            if not add_new_profile_fields(connection):
                print("⚠️ 字段添加失败，但继续数据迁移...")
            
            # 迁移用户档案数据
            if not migrate_user_profiles(connection):
                connection.rollback()
                print("❌ 用户档案迁移失败，已回滚")
                return
            
            # 提交事务
            connection.commit()
            print("✅ 用户档案升级完成！")
            
            # 验证结果
            print("\n🔍 验证升级结果...")
            verify_migration(connection)
            
        except Exception as e:
            connection.rollback()
            print(f"❌ 升级过程中出错，已回滚: {e}")
            
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
    finally:
        if 'connection' in locals():
            connection.close()
            print("\n📊 数据库连接已关闭")
    
    print("\n" + "=" * 60)
    print("🎉 用户档案结构升级完成！")
    print("💡 建议重启服务器以加载新的档案结构")

if __name__ == "__main__":
    main()
"""
TATA 数据库设置工具 v2.0
用于初始化MySQL数据库和Metabase集成
修复了环境变量加载、端口配置、字段引用、编码等问题
"""

import os
import pymysql
import subprocess
import time
import webbrowser
import sys
from dotenv import load_dotenv

# 修复Windows编码问题
if sys.platform.startswith('win'):
    import locale
    # 设置控制台编码为UTF-8
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Chinese (Simplified)_China.UTF-8')
        except:
            pass

def run_command_safe(cmd, cwd=None, capture_output=True):
    """安全执行命令，处理编码问题"""
    try:
        # Windows下明确指定编码
        if sys.platform.startswith('win'):
            result = subprocess.run(
                cmd, 
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace',  # 替换无法解码的字符
                shell=True  # Windows下使用shell
            )
        else:
            result = subprocess.run(
                cmd,
                cwd=cwd, 
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        return result
    except Exception as e:
        print(f"⚠️ 命令执行出错: {e}")
        # 返回一个模拟的结果对象
        class MockResult:
            def __init__(self):
                self.returncode = 1
                self.stdout = ""
                self.stderr = str(e)
        return MockResult()

def check_environment():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置...")
    
    env_path = os.path.join(os.path.dirname(__file__), "agent", ".env")
    
    if not os.path.exists(env_path):
        print(f"❌ 环境变量文件不存在: {env_path}")
        print("💡 正在创建默认环境变量文件...")
        
        # 创建默认.env文件
        default_env_content = """# OpenAI配置
OPENAI_API_KEY=sk-quBjWaFrfCyP8NFp75Bd90C46e96425a8756545dC5Ee386f
OPENAI_API_BASE=https://api.gptplus5.com/v1
LANGSMITH_API_KEY=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
TAVILY_API_KEY=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

# 数据库配置
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=123456
DB_NAME=tata
"""
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(default_env_content)
        print(f"✅ 创建默认环境变量文件: {env_path}")
    
    load_dotenv(env_path)
    
    required_vars = {
        'DB_HOST': os.getenv("DB_HOST"),
        'DB_PORT': os.getenv("DB_PORT"),
        'DB_USER': os.getenv("DB_USER"),
        'DB_PASSWORD': os.getenv("DB_PASSWORD"),
        'DB_NAME': os.getenv("DB_NAME")
    }
    
    print(f"📁 环境变量文件: {env_path}")
    print("📋 环境变量状态:")
    
    missing_vars = []
    for var, value in required_vars.items():
        if value:
            if var == 'DB_PASSWORD':
                print(f"   {var}: {'*' * len(value)}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ 未设置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 缺少环境变量: {', '.join(missing_vars)}")
        return False
    
    print("✅ 环境变量配置完整")
    return True

def check_docker():
    """检查Docker是否安装并运行"""
    try:
        result = run_command_safe(['docker', '--version'])
        if result.returncode == 0:
            print(f"✅ Docker已安装: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker未安装或未启动")
            return False
    except FileNotFoundError:
        print("❌ 未找到Docker命令，请先安装Docker Desktop")
        return False
    except Exception as e:
        print(f"❌ 检查Docker时出错: {e}")
        return False

def start_docker_services():
    """启动Docker服务"""
    print("🚀 启动Docker服务...")
    
    try:
        # 检查docker-compose.yml是否存在
        compose_file = os.path.join(os.path.dirname(__file__), 'docker-compose.yml')
        if not os.path.exists(compose_file):
            print(f"❌ 找不到docker-compose.yml文件: {compose_file}")
            print("💡 请确保docker-compose.yml文件存在于项目根目录")
            return False
        
        print(f"📁 找到配置文件: {compose_file}")
        
        # 先停止可能存在的容器
        print("🛑 清理现有容器...")
        result = run_command_safe(['docker-compose', 'down'], cwd=os.path.dirname(__file__))
        
        # 启动服务
        print("🔄 启动新容器...")
        result = run_command_safe(['docker-compose', 'up', '-d'], cwd=os.path.dirname(__file__))
        
        # 显示详细输出
        if result.stdout:
            # 过滤掉可能包含特殊字符的行
            safe_output = result.stdout.replace('\x00', '').encode('ascii', 'ignore').decode('ascii')
            print(f"📋 Docker输出:\n{safe_output}")
        if result.stderr and "warning" not in result.stderr.lower():
            safe_error = result.stderr.replace('\x00', '').encode('ascii', 'ignore').decode('ascii')
            print(f"⚠️ Docker信息:\n{safe_error}")
        
        if result.returncode == 0:
            print("✅ Docker服务启动成功")
            
            # 检查容器状态
            print("🔍 检查容器状态...")
            status_result = run_command_safe(['docker-compose', 'ps'], cwd=os.path.dirname(__file__))
            if status_result.stdout:
                safe_status = status_result.stdout.replace('\x00', '').encode('ascii', 'ignore').decode('ascii')
                print(safe_status)
            
            print("🕐 等待MySQL和Metabase服务启动...")
            time.sleep(20)  # 增加等待时间
            return True
        else:
            print(f"❌ Docker服务启动失败")
            if result.stderr:
                safe_error = result.stderr.replace('\x00', '').encode('ascii', 'ignore').decode('ascii')
                print(f"错误信息: {safe_error}")
            return False
            
    except FileNotFoundError:
        print("❌ 未找到docker-compose命令")
        print("💡 请确保Docker Desktop已正确安装并启动")
        return False
    except Exception as e:
        print(f"❌ 启动Docker服务时出错: {e}")
        return False

def setup_database():
    """设置数据库 - 修复版本"""
    # 加载agent目录下的.env文件
    env_path = os.path.join(os.path.dirname(__file__), "agent", ".env")
    load_dotenv(env_path)
    
    print(f"📁 数据库加载环境变量文件: {env_path}")
    
    # 数据库配置 - 修复端口号
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3307"))  # 修正默认端口
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "tata")
    
    print(f"🔧 数据库配置: {db_user}@{db_host}:{db_port}/{db_name}")
    
    if not db_user or not db_password:
        print("❌ 请在 agent/.env 文件中设置 DB_USER 和 DB_PASSWORD")
        print(f"当前 DB_USER: {db_user}")
        print(f"当前 DB_PASSWORD: {'***' if db_password else 'None'}")
        return False
    
    # 等待MySQL完全启动
    max_retries = 30
    connection = None
    for i in range(max_retries):
        try:
            connection = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=5
            )
            print("✅ MySQL连接成功")
            break
        except pymysql.Error as e:
            if i < max_retries - 1:
                print(f"⏳ 等待MySQL启动... ({i+1}/{max_retries}) - Error: {e.args[0]}")
                time.sleep(2)
            else:
                print(f"❌ MySQL连接失败: {e}")
                print("💡 请检查:")
                print("   1. Docker容器是否在运行")
                print("   2. 环境变量是否正确设置")
                print("   3. 端口号是否正确 (应该是3307)")
                return False
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ 等待MySQL启动... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ MySQL连接失败: {e}")
                return False
    
    if not connection:
        print("❌ 无法建立数据库连接")
        return False
    
    try:
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ 数据库 '{db_name}' 创建成功")
            
            # 选择数据库
            cursor.execute(f"USE {db_name}")
            
            # 执行完整的数据库初始化
            print("🔧 初始化数据库表结构...")
            
            # 删除现有表（如果存在）
            tables_to_drop = ['drafts', 'messages', 'sessions', 'users']
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"🗑️ 删除旧表: {table}")
                except:
                    pass
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE users (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    preferences JSON,
                    
                    -- 用户统计字段
                    total_sessions_count INT DEFAULT 0,
                    total_words_generated INT DEFAULT 0,
                    avg_session_duration_minutes DECIMAL(10,2) DEFAULT 0,
                    last_active_at TIMESTAMP NULL,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_email (email),
                    INDEX idx_last_active (last_active_at),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ 创建用户表")
            
            # 创建会话表
            cursor.execute("""
                CREATE TABLE sessions (
                    id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    title VARCHAR(200),
                    status ENUM('active', 'paused', 'completed') DEFAULT 'active',
                    
                    -- 议程和内容
                    agenda_doc LONGTEXT,
                    core_goal TEXT,
                    session_summary TEXT,
                    
                    -- 统计信息
                    message_count INT DEFAULT 0,
                    draft_count INT DEFAULT 0,
                    word_count INT DEFAULT 0,
                    tool_usage_count INT DEFAULT 0,
                    tools_used JSON,
                    
                    -- 时间维度
                    session_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_ai_response_at TIMESTAMP NULL,
                    last_activity_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    duration_minutes DECIMAL(10,2) DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    INDEX idx_last_activity (last_activity_at),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ 创建会话表")
            
            # 创建消息表
            cursor.execute("""
                CREATE TABLE messages (
                    id VARCHAR(50) PRIMARY KEY,
                    session_id VARCHAR(50) NOT NULL,
                    
                    -- 角色分类
                    message_role ENUM('user', 'assistant', 'system', 'tool') DEFAULT 'user',
                    type ENUM('user', 'ai', 'ai_pause', 'system', 'tool') DEFAULT 'user',
                    content LONGTEXT,
                    
                    -- 消息属性
                    word_count INT DEFAULT 0,
                    tool_name VARCHAR(50),
                    parent_message_id VARCHAR(50),
                    
                    -- 元数据
                    message_metadata JSON,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL,
                    INDEX idx_session_id (session_id),
                    INDEX idx_message_role (message_role),
                    INDEX idx_type (type),
                    INDEX idx_tool_name (tool_name),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ 创建消息表")
            
            # 创建草稿表
            cursor.execute("""
                CREATE TABLE drafts (
                    id VARCHAR(50) PRIMARY KEY,
                    session_id VARCHAR(50) NOT NULL,
                    draft_id VARCHAR(100) NOT NULL,
                    content LONGTEXT,
                    
                    -- 草稿分类和版本
                    draft_type ENUM('story', 'character', 'plot', 'dialogue', 'outline', 'setting', 'other') DEFAULT 'other',
                    version INT DEFAULT 1,
                    is_final BOOLEAN DEFAULT FALSE,
                    
                    -- 统计信息
                    word_count INT DEFAULT 0,
                    
                    created_by ENUM('user', 'ai') DEFAULT 'ai',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_session_draft_version (session_id, draft_id, version),
                    INDEX idx_session_id (session_id),
                    INDEX idx_draft_type (draft_type),
                    INDEX idx_is_final (is_final),
                    INDEX idx_created_by (created_by),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✅ 创建草稿表")
            
            # 插入默认用户
            cursor.execute("""
                INSERT INTO users (id, name, preferences, created_at, updated_at) 
                VALUES ('user_main', '默认用户', '{"theme": "default", "language": "zh-CN"}', NOW(), NOW())
                ON DUPLICATE KEY UPDATE updated_at = NOW()
            """)
            print("✅ 创建默认用户")
            
            print("✅ 数据库初始化完成")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库设置失败: {e}")
        if connection:
            connection.close()
        return False

def recreate_database():
    """强制重新创建数据库（删除所有数据）"""
    print("⚠️  警告：此操作将删除所有现有数据！")
    confirm = input("确认要重新创建数据库吗？(输入 'YES' 确认): ")
    
    if confirm != 'YES':
        print("❌ 操作已取消")
        return False
    
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(__file__), "agent", ".env")
    load_dotenv(env_path)
    print(f"📁 加载环境变量文件: {env_path}")
    
    # 获取数据库配置
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3307"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "tata")
    
    print(f"🔧 数据库配置: {db_user}@{db_host}:{db_port}/{db_name}")
    
    # 检查必要的环境变量
    if not db_user or not db_password:
        print("❌ 数据库用户名或密码未设置")
        print(f"DB_USER: {db_user}")
        print(f"DB_PASSWORD: {'***' if db_password else 'None'}")
        print("请检查 agent/.env 文件中的 DB_USER 和 DB_PASSWORD 设置")
        return False
    
    try:
        # 连接数据库
        print("🔗 连接到MySQL服务器...")
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            charset='utf8mb4',
            autocommit=True,
            connect_timeout=10
        )
        print("✅ MySQL连接成功")
        
        with connection.cursor() as cursor:
            # 删除数据库
            print(f"🗑️ 删除数据库: {db_name}")
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            print(f"✅ 删除旧数据库: {db_name}")
        
        connection.close()
        
        # 重新创建数据库
        print("🔄 重新创建数据库...")
        return setup_database()
        
    except pymysql.Error as e:
        print(f"❌ MySQL错误 ({e.args[0]}): {e.args[1]}")
        if e.args[0] == 1045:  # Access denied
            print("💡 可能的解决方案:")
            print("   1. 检查 DB_USER 和 DB_PASSWORD 是否正确")
            print("   2. 确保MySQL容器正在运行")
            print("   3. 检查端口号是否正确 (应该是3307)")
        elif e.args[0] == 2003:  # Can't connect
            print("💡 MySQL服务器无法连接，请检查:")
            print("   1. Docker容器是否正在运行")
            print("   2. 端口映射是否正确")
        return False
    except Exception as e:
        print(f"❌ 重新创建数据库失败: {e}")
        return False

def create_metabase_views():
    """为Metabase创建便于分析的视图 - v2.0版本"""
    load_dotenv(os.path.join(os.path.dirname(__file__), "agent", ".env"))
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3307"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "tata")
    
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            print("📊 创建Metabase分析视图 v2.0...")
            
            # 先检查表结构，确保字段存在
            cursor.execute("DESCRIBE users")
            user_columns = [row[0] for row in cursor.fetchall()]
            print(f"🔍 用户表字段: {user_columns}")
            
            cursor.execute("DESCRIBE sessions")
            session_columns = [row[0] for row in cursor.fetchall()]
            print(f"🔍 会话表字段: {session_columns}")
            
            # 检查关键字段是否存在
            required_user_fields = ['total_sessions_count', 'total_words_generated', 'last_active_at']
            required_session_fields = ['word_count', 'message_count', 'duration_minutes']
            
            has_user_stats = all(col in user_columns for col in required_user_fields)
            has_session_stats = all(col in session_columns for col in required_session_fields)
            
            if not has_user_stats or not has_session_stats:
                print("⚠️ 数据库表结构不完整，缺少必要字段")
                print(f"用户表缺少字段: {[f for f in required_user_fields if f not in user_columns]}")
                print(f"会话表缺少字段: {[f for f in required_session_fields if f not in session_columns]}")
                print("请先重新创建数据库（选择选项6）")
                return
            
            # 用户生命周期分析视图
            cursor.execute("""
                CREATE OR REPLACE VIEW v_user_lifecycle AS
                SELECT 
                    u.id as user_id,
                    u.name,
                    u.email,
                    u.created_at as registration_date,
                    u.total_sessions_count,
                    u.total_words_generated,
                    u.avg_session_duration_minutes,
                    u.last_active_at,
                    
                    -- 活跃度分析
                    CASE 
                        WHEN u.last_active_at IS NOT NULL AND u.last_active_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 'Daily Active'
                        WHEN u.last_active_at IS NOT NULL AND u.last_active_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Weekly Active'
                        WHEN u.last_active_at IS NOT NULL AND u.last_active_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'Monthly Active'
                        ELSE 'Inactive'
                    END as user_segment,
                    
                    -- 用户价值分析
                    CASE 
                        WHEN u.total_words_generated > 10000 THEN 'High Value'
                        WHEN u.total_words_generated > 2000 THEN 'Medium Value'
                        WHEN u.total_words_generated > 0 THEN 'Low Value'
                        ELSE 'No Value'
                    END as user_value_tier
                FROM users u;
            """)
            print("✅ 创建用户生命周期分析视图")
            
            # 会话效果分析视图
            cursor.execute("""
                CREATE OR REPLACE VIEW v_session_effectiveness AS
                SELECT 
                    s.id as session_id,
                    s.user_id,
                    s.title,
                    s.status,
                    s.word_count,
                    s.message_count,
                    s.draft_count,
                    s.tool_usage_count,
                    s.duration_minutes,
                    s.session_started_at,
                    s.completed_at,
                    s.last_activity_at,
                    
                    -- 效率指标
                    ROUND(s.word_count / GREATEST(s.duration_minutes, 1), 2) as words_per_minute,
                    ROUND(s.word_count / GREATEST(s.message_count, 1), 2) as words_per_message,
                    
                    -- 完成度分析
                    CASE 
                        WHEN s.status = 'completed' THEN 'Completed'
                        WHEN s.duration_minutes > 60 AND s.status = 'active' THEN 'Long Running'
                        WHEN s.last_activity_at IS NOT NULL AND s.last_activity_at < DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 'Abandoned'
                        ELSE 'In Progress'
                    END as session_outcome,
                    
                    -- 工具使用分析
                    CASE 
                        WHEN s.tools_used IS NOT NULL AND JSON_VALID(s.tools_used) THEN JSON_LENGTH(s.tools_used) 
                        ELSE 0 
                    END as unique_tools_count
                FROM sessions s;
            """)
            print("✅ 创建会话效果分析视图")
            
            # 每日活动统计视图
            cursor.execute("""
                CREATE OR REPLACE VIEW v_daily_activity AS
                SELECT 
                    DATE(s.session_started_at) as activity_date,
                    COUNT(*) as session_count,
                    COUNT(DISTINCT s.user_id) as unique_users,
                    SUM(s.word_count) as total_words,
                    AVG(s.duration_minutes) as avg_duration,
                    COUNT(CASE WHEN s.status = 'completed' THEN 1 END) as completed_sessions
                FROM sessions s
                WHERE s.session_started_at IS NOT NULL
                GROUP BY DATE(s.session_started_at)
                ORDER BY activity_date DESC;
            """)
            print("✅ 创建每日活动统计视图")
            
            # 消息流分析视图
            cursor.execute("""
                CREATE OR REPLACE VIEW v_message_flow AS
                SELECT 
                    m.id,
                    m.session_id,
                    s.title as session_title,
                    m.message_role,
                    m.type,
                    LENGTH(m.content) as content_length,
                    m.word_count,
                    m.tool_name,
                    m.created_at,
                    DATE(m.created_at) as message_date,
                    HOUR(m.created_at) as message_hour,
                    
                    -- 消息分类
                    CASE 
                        WHEN m.content LIKE '%sorry, I can%t assist%' THEN 'LLM_REJECTION'
                        WHEN m.content LIKE '%JSON%解析%失败%' THEN 'JSON_ERROR'
                        WHEN m.content LIKE '%无法协助%' THEN 'LLM_REJECTION_CN'
                        WHEN m.tool_name IS NOT NULL THEN 'TOOL_USAGE'
                        ELSE 'NORMAL'
                    END as message_category
                FROM messages m
                JOIN sessions s ON m.session_id = s.id;
            """)
            print("✅ 创建消息流分析视图")
            
            # 内容创作分析视图
            cursor.execute("""
                CREATE OR REPLACE VIEW v_content_creation AS
                SELECT 
                    d.session_id,
                    s.user_id,
                    s.title as session_title,
                    d.draft_type,
                    COUNT(*) as draft_count,
                    SUM(d.word_count) as total_words,
                    AVG(d.word_count) as avg_words_per_draft,
                    MAX(d.version) as max_version,
                    COUNT(CASE WHEN d.is_final = 1 THEN 1 END) as final_drafts_count,
                    
                    -- 创作模式分析
                    CASE 
                        WHEN MAX(d.version) > 3 THEN 'Iterative'
                        WHEN COUNT(*) > 5 THEN 'Prolific'
                        WHEN AVG(d.word_count) > 500 THEN 'Detailed'
                        ELSE 'Basic'
                    END as creation_pattern,
                    
                    MIN(d.created_at) as first_draft_time,
                    MAX(d.updated_at) as last_update_time
                FROM drafts d
                JOIN sessions s ON d.session_id = s.id
                GROUP BY d.session_id, s.user_id, d.draft_type;
            """)
            print("✅ 创建内容创作分析视图")
            
            print("✅ Metabase分析视图 v2.0 创建成功")
            
        connection.close()
        
    except Exception as e:
        print(f"❌ 创建Metabase视图失败: {e}")
        print(f"详细错误: {str(e)}")

def check_services_status():
    """检查服务状态"""
    print("\n🔍 检查服务状态...")
    
    try:
        # 检查Docker容器状态
        result = run_command_safe(['docker-compose', 'ps'], cwd=os.path.dirname(__file__))
        print("Docker容器状态:")
        if result.stdout:
            safe_output = result.stdout.replace('\x00', '').encode('ascii', 'ignore').decode('ascii')
            print(safe_output)
        
        # 检查MySQL连接
        load_dotenv(os.path.join(os.path.dirname(__file__), "agent", ".env"))
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "3307"))
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        try:
            connection = pymysql.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                charset='utf8mb4',
                connect_timeout=5
            )
            print("✅ MySQL连接正常")
            connection.close()
        except Exception as e:
            print(f"❌ MySQL连接失败: {e}")
        
        # 检查Metabase是否可访问
        try:
            import requests
            response = requests.get('http://localhost:3000', timeout=5)
            if response.status_code == 200:
                print("✅ Metabase服务正常 - http://localhost:3000")
            else:
                print(f"⚠️ Metabase响应异常: {response.status_code}")
        except Exception as e:
            print(f"❌ Metabase不可访问: {e}")
            
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")


def test_database():
    """测试数据库连接"""
    load_dotenv(os.path.join(os.path.dirname(__file__), "agent", ".env"))
    
    try:
        from agent.persistence.database import DatabaseManager
        
        # 构建数据库URL
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3307")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "123456")
        db_name = os.getenv("DB_NAME", "tata")
        database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        
        db_manager = DatabaseManager(database_url)
        if db_manager.test_connection():
            print("✅ 数据库连接测试成功")
            
            # 测试基本功能
            user_info = db_manager.get_user("user_main")
            if user_info:
                print(f"✅ 找到默认用户: {user_info['name']}")
            else:
                print("⚠️ 默认用户不存在，正在创建...")
                success = db_manager.create_user("user_main", "默认用户", preferences={"theme": "default", "language": "zh-CN"})
                if success:
                    print("✅ 默认用户创建成功")
                else:
                    print("❌ 默认用户创建失败")
            
            return True
        else:
            print("❌ 数据库连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库测试错误: {e}")
        return False

def setup_complete_system():
    """完整系统设置"""
    print("🚀 开始完整的TATA系统设置...")
    print("=" * 60)
    
    # 1. 检查环境变量
    if not check_environment():
        print("❌ 请先修复环境变量配置")
        return False
    
    # 2. 检查Docker
    if not check_docker():
        print("❌ 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    
    # 3. 启动Docker服务
    if not start_docker_services():
        return False
    
    # 4. 设置数据库
    if not setup_database():
        return False
    
    # 5. 创建Metabase视图
    create_metabase_views()
    
    # 6. 测试数据库
    if not test_database():
        return False
    
    # 7. 检查服务状态
    check_services_status()
    
    print("\n" + "=" * 60)
    print("🎉 系统设置完成！")
    print("📊 Metabase可视化: http://localhost:3000")
    print("🗄️ MySQL数据库: localhost:3307")
    print("💡 提示: 首次访问Metabase需要设置管理员账户")
    print("=" * 60)
    
    # 打开Metabase
    try:
        webbrowser.open('http://localhost:3000')
    except:
        pass
    
    return True

if __name__ == "__main__":
    # 设置控制台编码
    if sys.platform.startswith('win'):
        os.system('chcp 65001 > nul')  # 设置Windows控制台为UTF-8
    
    print("🚀 TATA 数据库和可视化工具设置 v2.0")
    print("=" * 50)
    print("1. 完整系统设置 (推荐)")
    print("2. 仅设置数据库")
    print("3. 仅测试连接")
    print("4. 创建Metabase视图")
    print("5. 检查服务状态")
    print("6. 强制重新创建数据库 (⚠️ 删除所有数据)")
    print("7. 检查环境变量配置")
    
    choice = input("\n请选择 (1-7): ").strip()
    
    if choice == "1":
        setup_complete_system()
    elif choice == "2":
        if check_environment() and setup_database():
            test_database()
    elif choice == "3":
        test_database()
    elif choice == "4":
        create_metabase_views()
    elif choice == "5":
        check_services_status()
    elif choice == "6":
        if recreate_database():
            create_metabase_views()
            test_database()
    elif choice == "7":
        check_environment()
    else:
        print("❌ 无效选择")
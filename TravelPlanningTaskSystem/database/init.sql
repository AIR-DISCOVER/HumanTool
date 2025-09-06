-- TATA Database Schema - 生产环境完整版
-- 包含所有最新字段和生产环境优化

-- 设置字符编码
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

CREATE DATABASE IF NOT EXISTS tata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tata;

-- 1. 完整的用户表
DROP TABLE IF EXISTS drafts;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    display_name VARCHAR(100),
    user_type VARCHAR(50) DEFAULT 'general',
    experiment_group VARCHAR(20),
    description TEXT,
    overall_profile TEXT COMMENT '用户总体档案描述',
    information_capabilities JSON COMMENT '信息能力列表',
    reasoning_capabilities JSON COMMENT '推理能力列表',
    last_updated DATE COMMENT '档案最后更新时间',
    capabilities JSON,
    user_preferences JSON,
    `accessible` BOOLEAN DEFAULT TRUE,
    input_schema JSON,
    preferences JSON,
    total_sessions_count INT DEFAULT 0,
    total_words_generated INT DEFAULT 0,
    avg_session_duration_minutes DECIMAL(10,2) DEFAULT 0,
    last_active_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_user_type (user_type),
    INDEX idx_experiment_group (experiment_group),
    INDEX idx_last_active (last_active_at),
    INDEX idx_created_at (created_at),
    INDEX idx_display_name (display_name)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 会话表
CREATE TABLE sessions (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    status ENUM('active', 'paused', 'completed') DEFAULT 'active',
    agenda_doc LONGTEXT,
    core_goal TEXT,
    session_summary TEXT,
    message_count INT DEFAULT 0,
    draft_count INT DEFAULT 0,
    word_count INT DEFAULT 0,
    tool_usage_count INT DEFAULT 0,
    tools_used JSON,
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
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 消息表
CREATE TABLE messages (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    message_role ENUM('user', 'assistant', 'system', 'tool') DEFAULT 'user',
    type ENUM('user', 'ai', 'ai_pause', 'system', 'tool') DEFAULT 'user',
    content LONGTEXT,
    word_count INT DEFAULT 0,
    tool_name VARCHAR(50),
    parent_message_id VARCHAR(50),
    message_metadata JSON,
    llm_response_content LONGTEXT COMMENT 'LLM完整响应内容(JSON格式)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    INDEX idx_session_id (session_id),
    INDEX idx_message_role (message_role),
    INDEX idx_type (type),
    INDEX idx_tool_name (tool_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 4. 草稿表
CREATE TABLE drafts (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    draft_id VARCHAR(100) NOT NULL,
    content LONGTEXT,
    draft_type ENUM('story', 'character', 'plot', 'dialogue', 'outline', 'setting', 'other') DEFAULT 'other',
    version INT DEFAULT 1,
    is_final BOOLEAN DEFAULT FALSE,
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
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 5. 插入生产环境用户数据
INSERT INTO users (
    id, name, display_name, user_type, experiment_group,
    overall_profile, information_capabilities, reasoning_capabilities, 
    last_updated, `accessible`, preferences, created_at, updated_at
) VALUES (
    'user_tyr1', '唐旋', '唐旋', 'admin', 'admin',
    '具有3年视觉设计经验的海报设计师，擅长品牌视觉表达和创意概念呈现，对平面设计和视觉传达有深度理解',
    JSON_ARRAY(
        '品牌视觉策略制定：基于3年实践经验，能够提供品牌调性分析、视觉风格定位、色彩搭配建议等专业意见，适用于海报概念设计和视觉风格确认场景',
        '目标受众洞察表达：深度了解不同受众群体的视觉偏好和审美趋势，能够在设计评审和风格选择中提供精准的受众匹配建议和视觉传达策略'
    ),
    JSON_ARRAY(
        '视觉层次价值评估：基于设计原则评估版面布局的视觉冲击力，在构图设计和信息层级中提供专业的视觉优化建议',
        '创意表达平衡决策：在多重设计约束下平衡创意表达与信息传达，为设计元素选择和视觉重点提供合理的创意决策和优先级排序'
    ),
    '2025-06-19',
    TRUE,
    JSON_OBJECT('theme', 'default', 'language', 'zh-CN'),
    NOW(),
    NOW()
);

INSERT INTO users (
    id, name, display_name, user_type, experiment_group,
    overall_profile, information_capabilities, reasoning_capabilities, 
    last_updated, `accessible`, preferences, created_at, updated_at
) VALUES (
    'user_main', '默认用户', '通用协作者', 'general', 'A',
    '通用创作协作者，具备多元化背景和灵活适应能力，能够在不同领域提供支持和反馈',
    JSON_ARRAY(
        '通用知识整合：具备跨领域知识背景，能够整合不同来源的信息，适用于初步研究和信息收集场景',
        '多角度分析：能够从不同视角分析问题，在头脑风暴和创意讨论中提供多元化观点和建议'
    ),
    JSON_ARRAY(
        '逻辑梳理：具备基础的逻辑分析能力，能够梳理问题结构和关系，适用于思路整理和方案对比',
        '实用性评估：从使用者角度评估方案的可行性和实用性，为决策提供接地气的反馈和建议'
    ),
    '2025-06-19',
    TRUE,
    JSON_OBJECT('theme', 'default', 'language', 'zh-CN'),
    NOW(),
    NOW()
);

-- 6. 创建生产环境视图
CREATE OR REPLACE VIEW v_user_overview AS
SELECT 
    u.id,
    u.display_name,
    u.user_type,
    u.experiment_group,
    LEFT(u.overall_profile, 100) as profile_preview,
    JSON_LENGTH(u.information_capabilities) as info_capability_count,
    JSON_LENGTH(u.reasoning_capabilities) as reasoning_capability_count,
    u.last_updated,
    u.`accessible`,
    u.total_sessions_count,
    u.last_active_at,
    u.created_at
FROM users u
WHERE u.`accessible` = TRUE
ORDER BY u.user_type, u.display_name;

-- 7. 数据完整性检查
SELECT 
    'Database initialized successfully!' as status,
    COUNT(*) as total_users,
    SUM(CASE WHEN overall_profile IS NOT NULL THEN 1 ELSE 0 END) as users_with_profile,
    SUM(CASE WHEN `accessible` = TRUE THEN 1 ELSE 0 END) as accessible_users
FROM users;

-- 显示用户概览
SELECT * FROM v_user_overview;
-- 为现有数据库添加LLM响应内容字段的迁移脚本
-- 执行前请备份数据库

USE tata;

-- 检查字段是否已存在
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'tata'
    AND TABLE_NAME = 'messages'
    AND COLUMN_NAME = 'llm_response_content'
);

-- 只有当字段不存在时才添加
SET @sql = IF(@column_exists = 0,
    'ALTER TABLE messages ADD COLUMN llm_response_content LONGTEXT COMMENT "LLM完整响应内容(JSON格式)" AFTER message_metadata;',
    'SELECT "字段 llm_response_content 已存在，跳过添加" as message;'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 验证字段是否添加成功
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'tata'
AND TABLE_NAME = 'messages'
AND COLUMN_NAME = 'llm_response_content';

-- 显示表结构确认
DESCRIBE messages;
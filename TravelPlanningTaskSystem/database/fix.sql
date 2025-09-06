SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

USE tata;

-- 删除现有数据
DELETE FROM users WHERE id IN ('user_main', 'user_tyr1');

-- 重新插入数据，使用直接的JSON字符串格式
INSERT INTO users (
    id, name, display_name, user_type, experiment_group,
    overall_profile, information_capabilities, reasoning_capabilities, 
    last_updated, `accessible`, preferences, created_at, updated_at
) VALUES (
    'user_tyr1', '唐旋', '唐旋', 'admin', 'admin',
    '具有3年视觉设计经验的海报设计师，擅长品牌视觉表达和创意概念呈现，对平面设计和视觉传达有深度理解',
    '[
        "品牌视觉策略制定：基于3年实践经验，能够提供品牌调性分析、视觉风格定位、色彩搭配建议等专业意见，适用于海报概念设计和视觉风格确认场景",
        "目标受众洞察表达：深度了解不同受众群体的视觉偏好和审美趋势，能够在设计评审和风格选择中提供精准的受众匹配建议和视觉传达策略"
    ]',
    '[
        "视觉层次价值评估：基于设计原则评估版面布局的视觉冲击力，在构图设计和信息层级中提供专业的视觉优化建议",
        "创意表达平衡决策：在多重设计约束下平衡创意表达与信息传达，为设计元素选择和视觉重点提供合理的创意决策和优先级排序"
    ]',
    '2025-06-19',
    TRUE,
    '{"theme": "default", "language": "zh-CN"}',
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
    '[
        "通用知识整合：具备跨领域知识背景，能够整合不同来源的信息，适用于初步研究和信息收集场景",
        "多角度分析：能够从不同视角分析问题，在头脑风暴和创意讨论中提供多元化观点和建议"
    ]',
    '[
        "逻辑梳理：具备基础的逻辑分析能力，能够梳理问题结构和关系，适用于思路整理和方案对比",
        "实用性评估：从使用者角度评估方案的可行性和实用性，为决策提供接地气的反馈和建议"
    ]',
    '2025-06-19',
    TRUE,
    '{"theme": "default", "language": "zh-CN"}',
    NOW(),
    NOW()
);

-- 验证数据
SELECT 
    id, 
    display_name,
    JSON_EXTRACT(information_capabilities, '$[0]') as first_info_cap,
    JSON_EXTRACT(reasoning_capabilities, '$[0]') as first_reasoning_cap
FROM users 
WHERE id IN ('user_main', 'user_tyr1');
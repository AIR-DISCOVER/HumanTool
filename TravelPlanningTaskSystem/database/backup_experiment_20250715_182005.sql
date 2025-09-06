-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: tata
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `drafts`
--

DROP TABLE IF EXISTS `drafts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `drafts` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `draft_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` longtext COLLATE utf8mb4_unicode_ci,
  `draft_type` enum('story','character','plot','dialogue','outline','setting','other') COLLATE utf8mb4_unicode_ci DEFAULT 'other',
  `version` int DEFAULT '1',
  `is_final` tinyint(1) DEFAULT '0',
  `word_count` int DEFAULT '0',
  `created_by` enum('user','ai') COLLATE utf8mb4_unicode_ci DEFAULT 'ai',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_session_draft_version` (`session_id`,`draft_id`,`version`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_draft_type` (`draft_type`),
  KEY `idx_is_final` (`is_final`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_updated_at` (`updated_at`),
  CONSTRAINT `drafts_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `drafts`
--

LOCK TABLES `drafts` WRITE;
/*!40000 ALTER TABLE `drafts` DISABLE KEYS */;
/*!40000 ALTER TABLE `drafts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message_role` enum('user','assistant','system','tool') COLLATE utf8mb4_unicode_ci DEFAULT 'user',
  `type` enum('user','ai','ai_pause','system','tool') COLLATE utf8mb4_unicode_ci DEFAULT 'user',
  `content` longtext COLLATE utf8mb4_unicode_ci,
  `word_count` int DEFAULT '0',
  `tool_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_message_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message_metadata` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `parent_message_id` (`parent_message_id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_message_role` (`message_role`),
  KEY `idx_type` (`type`),
  KEY `idx_tool_name` (`tool_name`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `sessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`parent_message_id`) REFERENCES `messages` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES ('msg_18369302','session_fcb758a0','assistant','ai_pause','为了制定最佳的旅游计划，我需要您确认您希望访问的弗吉尼亚三个城市以及您对活动的偏好。请告诉我您的选择。',1,NULL,NULL,'{}','2025-07-15 08:13:53'),('msg_9db41267','session_fcb758a0','user','user','好的',1,NULL,NULL,'{}','2025-07-15 08:13:49'),('msg_ebe19495','session_fcb758a0','user','user','{\"user_profile\":\"user_main\",\"travel_query\":\"Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800.\"}',40,NULL,NULL,'{}','2025-07-15 08:13:33');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sessions` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('active','paused','completed') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `agenda_doc` longtext COLLATE utf8mb4_unicode_ci,
  `core_goal` text COLLATE utf8mb4_unicode_ci,
  `session_summary` text COLLATE utf8mb4_unicode_ci,
  `message_count` int DEFAULT '0',
  `draft_count` int DEFAULT '0',
  `word_count` int DEFAULT '0',
  `tool_usage_count` int DEFAULT '0',
  `tools_used` json DEFAULT NULL,
  `session_started_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `first_ai_response_at` timestamp NULL DEFAULT NULL,
  `last_activity_at` timestamp NULL DEFAULT NULL,
  `completed_at` timestamp NULL DEFAULT NULL,
  `duration_minutes` decimal(10,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_last_activity` (`last_activity_at`),
  KEY `idx_updated_at` (`updated_at`),
  CONSTRAINT `sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
INSERT INTO `sessions` VALUES ('session_fcb758a0','user_main','{\"user_profile\":\"user_main\",\"travel_query\":\"Can yo','active','# 工作议程\n\n- [ ] Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different cities in Virginia? The trip duration is for 7 days, from March 15th to March 21st, 2022, with a total budget of $1,800. @overall_goal\n\n**用户档案**: user_main\n**任务详情**: Can you help construct a travel plan that begins in Philadelphia and includes visits to 3 different ...',NULL,NULL,0,0,0,0,NULL,'2025-07-15 08:13:33',NULL,'2025-07-15 08:13:53',NULL,0.00,'2025-07-15 08:13:33','2025-07-15 08:13:53');
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `display_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'general',
  `experiment_group` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `overall_profile` text COLLATE utf8mb4_unicode_ci COMMENT '用户总体档案描述',
  `information_capabilities` json DEFAULT NULL COMMENT '信息能力列表',
  `reasoning_capabilities` json DEFAULT NULL COMMENT '推理能力列表',
  `last_updated` date DEFAULT NULL COMMENT '档案最后更新时间',
  `capabilities` json DEFAULT NULL,
  `user_preferences` json DEFAULT NULL,
  `accessible` tinyint(1) DEFAULT '1',
  `input_schema` json DEFAULT NULL,
  `preferences` json DEFAULT NULL,
  `total_sessions_count` int DEFAULT '0',
  `total_words_generated` int DEFAULT '0',
  `avg_session_duration_minutes` decimal(10,2) DEFAULT '0.00',
  `last_active_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_email` (`email`),
  KEY `idx_user_type` (`user_type`),
  KEY `idx_experiment_group` (`experiment_group`),
  KEY `idx_last_active` (`last_active_at`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_display_name` (`display_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('user_main','默认用户',NULL,'通用协作者','general','A',NULL,'通用创作协作者，具备多元化背景和灵活适应能力，能够在不同领域提供支持和反馈','[\"通用知识整合：具备跨领域知识背景，能够整合不同来源的信息，适用于初步研究和信息收集场景\", \"多角度分析：能够从不同视角分析问题，在头脑风暴和创意讨论中提供多元化观点和建议\"]','[\"逻辑梳理：具备基础的逻辑分析能力，能够梳理问题结构和关系，适用于思路整理和方案对比\", \"实用性评估：从使用者角度评估方案的可行性和实用性，为决策提供接地气的反馈和建议\"]','2025-06-19',NULL,NULL,1,NULL,'{\"theme\": \"default\", \"language\": \"zh-CN\"}',0,0,0.00,NULL,'2025-07-15 07:32:42','2025-07-15 07:32:42'),('user_tyr1','唐旋',NULL,'唐旋','admin','admin',NULL,'具有3年视觉设计经验的海报设计师，擅长品牌视觉表达和创意概念呈现，对平面设计和视觉传达有深度理解','[\"品牌视觉策略制定：基于3年实践经验，能够提供品牌调性分析、视觉风格定位、色彩搭配建议等专业意见，适用于海报概念设计和视觉风格确认场景\", \"目标受众洞察表达：深度了解不同受众群体的视觉偏好和审美趋势，能够在设计评审和风格选择中提供精准的受众匹配建议和视觉传达策略\"]','[\"视觉层次价值评估：基于设计原则评估版面布局的视觉冲击力，在构图设计和信息层级中提供专业的视觉优化建议\", \"创意表达平衡决策：在多重设计约束下平衡创意表达与信息传达，为设计元素选择和视觉重点提供合理的创意决策和优先级排序\"]','2025-06-19',NULL,NULL,1,NULL,'{\"theme\": \"default\", \"language\": \"zh-CN\"}',0,0,0.00,NULL,'2025-07-15 07:32:42','2025-07-15 07:32:42');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `v_user_overview`
--

DROP TABLE IF EXISTS `v_user_overview`;
/*!50001 DROP VIEW IF EXISTS `v_user_overview`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_user_overview` AS SELECT 
 1 AS `id`,
 1 AS `display_name`,
 1 AS `user_type`,
 1 AS `experiment_group`,
 1 AS `profile_preview`,
 1 AS `info_capability_count`,
 1 AS `reasoning_capability_count`,
 1 AS `last_updated`,
 1 AS `accessible`,
 1 AS `total_sessions_count`,
 1 AS `last_active_at`,
 1 AS `created_at`*/;
SET character_set_client = @saved_cs_client;

--
-- Dumping routines for database 'tata'
--

--
-- Final view structure for view `v_user_overview`
--

/*!50001 DROP VIEW IF EXISTS `v_user_overview`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_user_overview` AS select `u`.`id` AS `id`,`u`.`display_name` AS `display_name`,`u`.`user_type` AS `user_type`,`u`.`experiment_group` AS `experiment_group`,left(`u`.`overall_profile`,100) AS `profile_preview`,json_length(`u`.`information_capabilities`) AS `info_capability_count`,json_length(`u`.`reasoning_capabilities`) AS `reasoning_capability_count`,`u`.`last_updated` AS `last_updated`,`u`.`accessible` AS `accessible`,`u`.`total_sessions_count` AS `total_sessions_count`,`u`.`last_active_at` AS `last_active_at`,`u`.`created_at` AS `created_at` from `users` `u` where (`u`.`accessible` = true) order by `u`.`user_type`,`u`.`display_name` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-15 10:20:05

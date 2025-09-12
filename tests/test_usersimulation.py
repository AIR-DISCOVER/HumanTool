import sys
import os
import json
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agent.tool.usersimulation import (
    UserSimulator, 
    UserPersona, 
    SimulationRecord,
    generate_user_personas,
    simulate_product_trial,
    conduct_user_interview,
    market_research_tool,
    get_simulation_statistics
)

class MockLLMClient:
    """模拟LLM客户端"""
    
    def generate(self, prompt: str) -> str:
        """根据prompt类型返回不同的模拟响应"""
        if "用户研究agent" in prompt and "USER_PERSONA" in prompt:
            # 用户画像生成
            return json.dumps([
                {
                    "persona": "李明，32岁，是一名互联网公司的产品经理。他注重效率和用户体验，热衷于尝试新的数字工具。有稳定收入，愿意为提高工作效率付费。",
                    "intent": "寻找能够提高团队协作效率的项目管理工具",
                    "age": 32,
                    "age_group": "30-39",
                    "gender": "男性",
                    "income": [150000, 300000],
                    "income_group": "150000-300000"
                },
                {
                    "persona": "王小美，28岁，初创公司运营总监。时间宝贵，需要快速决策工具。对新技术敏感，愿意投资高效工具。",
                    "intent": "需要数据分析和用户反馈收集工具",
                    "age": 28,
                    "age_group": "25-34",
                    "gender": "女性",
                    "income": [120000, 250000],
                    "income_group": "120000-250000"
                }
            ], ensure_ascii=False)
        
        elif "模拟产品试用过程" in prompt or "当前状态" in prompt:
            # 产品试用模拟
            return json.dumps({
                "当前状态": "我正在查看产品的主页面，想了解它的核心功能和价格",
                "思考过程": "作为产品经理，我关注的是这个工具能否真正提升团队效率，界面是否足够直观",
                "下一步": "点击功能介绍页面，详细了解各项功能特性"
            }, ensure_ascii=False)
        
        elif "insights" in prompt or "高级见解" in prompt:
            # 用户洞察生成
            return json.dumps({
                "insights": [
                    "产品的导航设计很直观，符合用户习惯",
                    "功能介绍页面信息密度过高，需要更好的层级设计",
                    "缺少新手引导功能，对于首次使用者可能存在学习成本",
                    "价格策略清晰，但缺少免费试用期说明"
                ]
            }, ensure_ascii=False)
        
        elif "访谈问题" in prompt or "模拟一位刚使用过" in prompt:
            # 用户访谈
            return json.dumps({
                "answer": "嗯...整体来说这个产品给我的第一印象还不错。界面设计比较干净，功能看起来也比较实用。不过我觉得有些地方还是可以改进的，比如那个功能介绍页面，信息有点多，我花了一些时间才找到我真正需要的功能。"
            }, ensure_ascii=False)
        
        elif "市场调研分析" in prompt or "needs" in prompt:
            # 市场调研
            return json.dumps({
                "needs": "需要一个能够整合团队沟通、任务管理和进度跟踪的一体化平台",
                "pain_points": "现有工具分散，切换成本高，团队协作效率低",
                "preferences": "界面简洁直观，学习成本低，支持移动端操作",
                "budget_considerations": "月费在500-2000元之间比较合理",
                "decision_factors": "功能完整性、易用性、技术支持、数据安全",
                "usage_scenarios": "日常项目管理、团队会议、客户汇报、数据分析"
            }, ensure_ascii=False)
        
        else:
            # 默认返回
            return json.dumps({"message": "模拟响应"}, ensure_ascii=False)

class TestUserSimulator(unittest.TestCase):
    """用户模拟器测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.mock_llm = MockLLMClient()
        self.simulator = UserSimulator(llm_client=self.mock_llm)
    
    def test_generate_personas(self):
        """测试用户画像生成功能"""
        print("\n🧪 测试用户画像生成...")
        
        personas = self.simulator.generate_personas(
            count=2,
            product_desc="项目管理协作工具",
            target_audience="互联网公司产品和运营人员",
            requirements="注重效率和团队协作"
        )
        
        # 验证结果
        self.assertEqual(len(personas), 2)
        self.assertIsInstance(personas[0], UserPersona)
        self.assertTrue(personas[0].id)
        self.assertTrue(personas[0].persona)
        self.assertTrue(personas[0].intent)
        self.assertIsInstance(personas[0].age, int)
        self.assertIsInstance(personas[0].income, list)
        
        print(f"✅ 成功生成 {len(personas)} 个用户画像")
        print(f"   用户1: {personas[0].age}岁{personas[0].gender}")
        print(f"   用户2: {personas[1].age}岁{personas[1].gender}")
    
    def test_simulate_product_trial(self):
        """测试产品试用模拟功能"""
        print("\n🧪 测试产品试用模拟...")
        
        # 先生成用户画像
        personas = self.simulator.generate_personas(1, "测试产品", "测试用户")
        user_id = personas[0].id
        
        # 模拟产品试用
        result = self.simulator.simulate_product_trial(
            user_id=user_id,
            product_info="项目管理协作工具 - 支持任务分配、进度跟踪、团队沟通",
            page_info="产品主页 - 展示核心功能和价格方案",
            memory=["刚进入网站", "正在了解产品"]
        )
        
        # 验证结果
        self.assertIn("当前状态", result)
        self.assertIn("思考过程", result)
        self.assertIn("下一步", result)
        
        print("✅ 产品试用模拟成功")
        print(f"   当前状态: {result['当前状态'][:50]}...")
        print(f"   下一步: {result['下一步'][:50]}...")
    
    def test_generate_insights(self):
        """测试用户洞察生成功能"""
        print("\n🧪 测试用户洞察生成...")
        
        # 先生成用户画像
        personas = self.simulator.generate_personas(1, "测试产品", "测试用户")
        user_id = personas[0].id
        
        # 生成洞察
        insights = self.simulator.generate_insights(
            user_id=user_id,
            behaviors=[
                "浏览了产品主页",
                "查看了功能介绍",
                "对比了价格方案",
                "阅读了用户评价"
            ]
        )
        
        # 验证结果
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        print(f"✅ 成功生成 {len(insights)} 条洞察")
        for i, insight in enumerate(insights[:3]):
            print(f"   洞察{i+1}: {insight[:50]}...")
    
    def test_conduct_interview(self):
        """测试用户访谈功能"""
        print("\n🧪 测试用户访谈...")
        
        # 先生成用户画像
        personas = self.simulator.generate_personas(1, "测试产品", "测试用户")
        user_id = personas[0].id
        
        # 进行访谈
        questions = [
            "请描述一下您对这个产品的第一印象",
            "您觉得哪些功能对您最有用？",
            "您会向同行推荐这个产品吗？"
        ]
        
        responses = self.simulator.conduct_interview(
            user_id=user_id,
            questions=questions,
            behaviors=["浏览主页", "试用功能", "查看价格"],
            satisfaction=4
        )
        
        # 验证结果
        self.assertEqual(len(responses), 3)
        for response in responses:
            self.assertIn("question", response)
            self.assertIn("answer", response)
            self.assertTrue(response["answer"])
        
        print(f"✅ 完成了 {len(responses)} 个问题的访谈")
        print(f"   第一个回答: {responses[0]['answer'][:50]}...")
    
    def test_market_research(self):
        """测试市场调研功能"""
        print("\n🧪 测试市场调研...")
        
        # 先生成用户画像
        personas = self.simulator.generate_personas(1, "测试产品", "测试用户")
        user_id = personas[0].id
        
        # 进行市场调研
        result = self.simulator.market_research(
            user_id=user_id,
            research_topics=[
                "项目管理工具使用习惯",
                "团队协作痛点",
                "工具选择决策因素",
                "预算和付费意愿"
            ]
        )
        
        # 验证结果
        expected_keys = ["needs", "pain_points", "preferences", "budget_considerations", "decision_factors", "usage_scenarios"]
        for key in expected_keys:
            self.assertIn(key, result)
            self.assertTrue(result[key])
        
        print("✅ 市场调研完成")
        print(f"   需求: {result['needs'][:50]}...")
        print(f"   痛点: {result['pain_points'][:50]}...")
    
    def test_get_statistics(self):
        """测试统计功能"""
        print("\n🧪 测试数据统计...")
        
        # 生成多个用户并进行各种操作
        personas = self.simulator.generate_personas(3, "测试产品", "测试用户")
        
        for persona in personas:
            # 模拟试用
            self.simulator.simulate_product_trial(
                persona.id, "测试产品", "主页", ["进入网站"]
            )
            
            # 进行访谈
            self.simulator.conduct_interview(
                persona.id, ["产品印象如何？"], ["浏览主页"], 4
            )
        
        # 获取统计
        stats = self.simulator.get_statistics()
        
        # 验证结果
        self.assertEqual(stats["用户总数"], 3)
        self.assertIn("人口统计学分析", stats)
        self.assertIn("行为统计分析", stats)
        self.assertIn("质性信息分析", stats)
        
        print("✅ 统计分析完成")
        print(f"   用户总数: {stats['用户总数']}")
        print(f"   平均年龄: {stats['人口统计学分析']['平均年龄']}")
        print(f"   总记录数: {stats['行为统计分析']['总记录数']}")
    
    def test_export_data(self):
        """测试数据导出功能"""
        print("\n🧪 测试数据导出...")
        
        # 生成数据
        personas = self.simulator.generate_personas(2, "测试产品", "测试用户")
        self.simulator.conduct_interview(personas[0].id, ["测试问题"], [], 4)
        
        # JSON导出
        json_data = self.simulator.export_data("json")
        self.assertTrue(json_data)
        
        # 验证JSON格式
        parsed_data = json.loads(json_data)
        self.assertIn("用户画像", parsed_data)
        self.assertIn("模拟记录", parsed_data)
        self.assertIn("统计分析", parsed_data)
        
        # CSV导出
        csv_data = self.simulator.export_data("csv")
        self.assertTrue(csv_data)
        self.assertIn("用户ID,年龄,性别", csv_data)
        
        print("✅ 数据导出成功")
        print(f"   JSON数据长度: {len(json_data)} 字符")
        # 修复：提取反斜杠到变量中
        newline = '\n'
        print(f"   CSV行数: {len(csv_data.split(newline))}")
    
    def test_fallback_mechanism(self):
        """测试降级机制"""
        print("\n🧪 测试降级机制...")
        
        # 创建没有LLM客户端的模拟器
        simulator_no_llm = UserSimulator(llm_client=None)
        
        # 测试降级用户画像生成
        personas = simulator_no_llm.generate_personas(2, "测试产品", "测试用户")
        self.assertEqual(len(personas), 2)
        self.assertTrue(personas[0].persona)
        
        print("✅ 降级机制正常工作")
        print(f"   降级生成用户: {personas[0].age}岁{personas[0].gender}")

class TestLangChainTools(unittest.TestCase):
    """LangChain工具接口测试"""
    
    @patch('agent.tool.usersimulation.UserSimulator')
    def test_generate_user_personas_tool(self, mock_simulator_class):
        """测试用户画像生成工具"""
        print("\n🧪 测试LangChain用户画像工具...")
        
        # 模拟返回值
        mock_persona = UserPersona(
            id="test-id",
            persona="测试用户",
            intent="测试意图",
            age=30,
            age_group="25-35",
            gender="男性",
            income=[100000, 200000],
            income_group="100000-200000"
        )
        
        mock_simulator = Mock()
        mock_simulator.generate_personas.return_value = [mock_persona]
        mock_simulator_class.return_value = mock_simulator
        
        # 调用工具
        result = generate_user_personas(
            count=1,
            product_description="测试产品",
            target_audience="测试用户",
            requirements="测试要求"
        )
        
        # 验证结果
        self.assertTrue(result)
        parsed_result = json.loads(result)
        self.assertEqual(len(parsed_result), 1)
        self.assertEqual(parsed_result[0]['age'], 30)
        
        print("✅ LangChain用户画像工具测试通过")
    
    def test_integration_workflow(self):
        """测试完整工作流程"""
        print("\n🧪 测试完整工作流程...")
        
        simulator = UserSimulator(llm_client=MockLLMClient())
        
        # 1. 生成用户画像
        personas = simulator.generate_personas(2, "智能笔记应用", "知识工作者")
        self.assertEqual(len(personas), 2)
        
        # 2. 产品试用模拟
        trial_result = simulator.simulate_product_trial(
            personas[0].id,
            "智能笔记应用 - AI辅助整理和搜索",
            "应用首页",
            ["下载应用", "注册账户"]
        )
        self.assertIn("当前状态", trial_result)
        
        # 3. 生成洞察
        insights = simulator.generate_insights(personas[0].id, ["试用核心功能", "测试AI助手"])
        self.assertGreater(len(insights), 0)
        
        # 4. 用户访谈
        responses = simulator.conduct_interview(
            personas[0].id,
            ["应用的AI功能如何？", "会推荐给同事吗？"],
            ["使用一周", "完成几个项目"],
            satisfaction=4
        )
        self.assertEqual(len(responses), 2)
        
        # 5. 统计分析
        stats = simulator.get_statistics()
        self.assertEqual(stats["用户总数"], 2)
        
        # 6. 数据导出
        export_data = simulator.export_data()
        self.assertTrue(export_data)
        
        print("✅ 完整工作流程测试通过")
        print(f"   生成用户: {len(personas)}个")
        print(f"   行为记录: {stats['行为统计分析']['总记录数']}条")
        print(f"   洞察数量: {len(insights)}条")

def run_tests():
    """运行所有测试"""
    print("🚀 开始用户模拟工具测试")
    print("=" * 50)
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestUserSimulator))
    test_suite.addTest(unittest.makeSuite(TestLangChainTools))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_tests()
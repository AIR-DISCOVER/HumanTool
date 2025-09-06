from langchain_core.tools import tool

class Tool:
    """工具基类"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs):
        """执行工具，子类需要重写此方法"""
        raise NotImplementedError()

class CalculatorTool(Tool):
    """计算器工具示例"""
    def __init__(self):
        super().__init__("calculator", "执行数学计算")
    
    def execute(self, expression):
        try:
            return str(eval(expression))  # 注意：实际应用中应使用更安全的方式
        except Exception as e:
            return f"计算错误: {str(e)}"
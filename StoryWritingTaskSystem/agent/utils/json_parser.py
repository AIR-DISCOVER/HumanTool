"""
JSON解析工具 - 统一的JSON处理接口
"""
import json
import re
from typing import Dict, Any, Optional

class JSONParser:
    """JSON解析和格式化工具"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def parse(self, content: str) -> Optional[Dict[str, Any]]:
        """解析JSON内容
        
        Args:
            content: 待解析的JSON字符串
            
        Returns:
            解析后的字典，失败时返回None
        """
        if not content or not content.strip():
            return None
            
        try:
            # 直接尝试JSON解析
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        try:
            json_content = self._extract_json_block(content)
            if json_content:
                return json.loads(json_content)
        except json.JSONDecodeError:
            pass
        
        # 尝试修复常见的JSON格式问题
        try:
            fixed_content = self._fix_common_json_issues(content)
            return json.loads(fixed_content)
        except json.JSONDecodeError:
            pass
        
        if self.logger:
            self.logger.warning(f"【JSON parser】JSON解析失败，内容：{content[:100]}...")
        
        return None
    
    def format_json(self, data: Dict[str, Any], indent: int = 2) -> str:
        """格式化数据为JSON字符串
        
        Args:
            data: 待格式化的数据
            indent: 缩进空格数
            
        Returns:
            格式化后的JSON字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except Exception as e:
            if self.logger:
                self.logger.error(f"JSON格式化失败: {e}")
            return json.dumps({"error": f"格式化失败: {str(e)}"}, ensure_ascii=False, indent=indent)
    
    def _extract_json_block(self, content: str) -> Optional[str]:
        """从markdown代码块中提取JSON"""
        # 查找 ```json 代码块
        json_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 查找 ``` 代码块（可能省略了json标识）
        code_pattern = r'```\s*\n(.*?)\n```'
        match = re.search(code_pattern, content, re.DOTALL)
        if match:
            block_content = match.group(1).strip()
            # 检查是否看起来像JSON
            if block_content.startswith('{') and block_content.endswith('}'):
                return block_content
        
        return None
    
    def _fix_common_json_issues(self, content: str) -> str:
        """修复常见的JSON格式问题"""
        # 移除markdown代码块标记
        content = re.sub(r'```json\s*\n?', '', content)
        content = re.sub(r'\n?```', '', content)
        
        # 移除多余的空白字符
        content = content.strip()
        
        # 确保JSON对象以 { 开始和 } 结束
        if not content.startswith('{'):
            # 尝试找到第一个 {
            start_pos = content.find('{')
            if start_pos != -1:
                content = content[start_pos:]
        
        if not content.endswith('}'):
            # 尝试找到最后一个 }
            end_pos = content.rfind('}')
            if end_pos != -1:
                content = content[:end_pos + 1]
        
        return content
    
    def is_valid_json(self, content: str) -> bool:
        """检查字符串是否为有效的JSON"""
        return self.parse(content) is not None
    
    def extract_json_from_text(self, content: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON对象（向后兼容方法）"""
        return self.parse(content)

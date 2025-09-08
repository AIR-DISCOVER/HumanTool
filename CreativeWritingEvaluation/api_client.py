#!/usr/bin/env python3
"""
简单易用的API调用客户端
支持一行代码调用API: output = api_call("你的问题")
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """简单易用的API调用客户端"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: int = 30,
                 temperature: float = 0.1,
                 max_tokens: Optional[int] = None):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量读取
            api_base: API基础URL，如果不提供则从环境变量读取
            model: 模型名称，如果不提供则从环境变量读取
            timeout: 请求超时时间（秒）
            temperature: 生成文本的随机性（0-1）
            max_tokens: 最大生成token数
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_API_BASE")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("API密钥未找到。请在环境变量中设置OPENAI_API_KEY或在初始化时提供api_key参数")
        
        # 初始化客户端
        self._init_client()
        
        # 对话历史
        self.conversation_history = []
    
    def _init_client(self):
        """初始化ChatOpenAI客户端"""
        client_params = {
            "openai_api_key": self.api_key,
            "model": self.model,
            "timeout": self.timeout,
            "temperature": self.temperature
        }
        
        if self.api_base:
            client_params["openai_api_base"] = self.api_base
        
        if self.max_tokens:
            client_params["max_tokens"] = self.max_tokens
            
        self.client = ChatOpenAI(**client_params)
    
    def call(self, 
             message: str, 
             system_prompt: Optional[str] = None,
             keep_history: bool = False) -> str:
        """
        调用API获取响应
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词（可选）
            keep_history: 是否保持对话历史
            
        Returns:
            API响应内容
        """
        try:
            messages = []
            
            # 添加系统提示词
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            
            # 如果保持历史，添加之前的对话
            if keep_history and self.conversation_history:
                messages.extend(self.conversation_history)
            
            # 添加当前用户消息
            user_message = HumanMessage(content=message)
            messages.append(user_message)
            
            # 调用API
            response = self.client.invoke(messages)
            
            # 打印API调用的输入和输出
            print("=== API调用输入 ===")
            print(f"system_prompt: {system_prompt}")
            print(f"message: {message}")
            print("=== API调用输出 ===")
            print(f"response: {response.content}")
            
            # 如果保持历史，更新对话历史
            if keep_history:
                self.conversation_history.append(user_message)
                self.conversation_history.append(AIMessage(content=response.content))
                
                # 限制历史长度，避免token过多
                if len(self.conversation_history) > 20:  # 保留最近10轮对话
                    self.conversation_history = self.conversation_history[-20:]
            
            return response.content
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def batch_call(self, messages: List[str], 
                   system_prompt: Optional[str] = None) -> List[str]:
        """
        批量调用API
        
        Args:
            messages: 消息列表
            system_prompt: 系统提示词（可选）
            
        Returns:
            响应列表
        """
        results = []
        for message in messages:
            try:
                result = self.call(message, system_prompt, keep_history=False)
                results.append(result)
            except Exception as e:
                logger.error(f"批量调用中的消息失败: {message[:50]}... 错误: {e}")
                results.append(f"错误: {str(e)}")
        
        return results
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        聊天模式（自动保持对话历史）
        
        Args:
            message: 用户消息
            system_prompt: 系统提示词（可选）
            
        Returns:
            API响应内容
        """
        return self.call(message, system_prompt, keep_history=True)
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清除")
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Returns:
            对话历史列表，每个元素包含role和content
        """
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                history.append({"role": "system", "content": msg.content})
        
        return history
    
    def set_temperature(self, temperature: float):
        """设置生成文本的随机性"""
        self.temperature = temperature
        self._init_client()
    
    def set_max_tokens(self, max_tokens: int):
        """设置最大生成token数"""
        self.max_tokens = max_tokens
        self._init_client()


# 创建全局客户端实例
_global_client = None

def get_client() -> APIClient:
    """获取全局客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = APIClient()
    return _global_client

def api_call(message: str, 
             system_prompt: Optional[str] = None,
             keep_history: bool = False) -> str:
    """
    简单的API调用函数 - 一行代码调用API
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词（可选）
        keep_history: 是否保持对话历史
        
    Returns:
        API响应内容
        
    Example:
        output = api_call("你好，请介绍一下Python")
        output = api_call("写一个计算斐波那契数列的函数", system_prompt="你是一个Python专家")
    """
    client = get_client()
    return client.call(message, system_prompt, keep_history)

def api_chat(message: str, system_prompt: Optional[str] = None) -> str:
    """
    聊天模式API调用 - 自动保持对话历史
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词（可选）
        
    Returns:
        API响应内容
        
    Example:
        response1 = api_chat("我叫张三")
        response2 = api_chat("我的名字是什么？")  # 会记住之前的对话
    """
    client = get_client()
    return client.chat(message, system_prompt)

def clear_chat_history():
    """清除聊天历史"""
    client = get_client()
    client.clear_history()

def get_chat_history() -> List[Dict[str, str]]:
    """获取聊天历史"""
    client = get_client()
    return client.get_history()


# 使用示例
if __name__ == "__main__":
    # 示例1: 简单调用
    print("=== 简单调用示例 ===")
    try:
        output = api_call("你好，请用一句话介绍Python编程语言")
        print(f"回答: {output}")
    except Exception as e:
        print(f"调用失败: {e}")
    
    # 示例2: 带系统提示词的调用
    print("\n=== 带系统提示词的调用示例 ===")
    try:
        output = api_call(
            "写一个计算阶乘的函数", 
            system_prompt="你是一个Python编程专家，请提供简洁清晰的代码"
        )
        print(f"回答: {output}")
    except Exception as e:
        print(f"调用失败: {e}")
    
    # 示例3: 聊天模式
    print("\n=== 聊天模式示例 ===")
    try:
        response1 = api_chat("我叫小明，我喜欢编程")
        print(f"回答1: {response1}")
        
        response2 = api_chat("我的名字是什么？我有什么爱好？")
        print(f"回答2: {response2}")
        
        # 清除历史
        clear_chat_history()
        print("聊天历史已清除")
        
    except Exception as e:
        print(f"聊天失败: {e}")

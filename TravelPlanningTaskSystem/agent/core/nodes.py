"""
节点管理模块入口 - 保持向后兼容性
"""
# 导入新的 NodeManager
from .nodes.node_manager import NodeManager

# 向后兼容性导出
__all__ = ["NodeManager"]
from typing import Dict, List, Tuple, Optional, Any
import json
from ..graph_ver2 import TaskNode
from ..types import GraphState, TaskNode

def calculate_task_depth(task_id: str, task_tree: Dict[str, TaskNode]) -> int:
    """计算任务的深度"""
    depth = 0
    current_id = task_tree[task_id]["parent_id"]
    while current_id:
        if current_id in task_tree:
            depth += 1
            current_id = task_tree[current_id]["parent_id"]
        else:
            break
    return depth

def check_task_limit(task_tree: Dict[str, TaskNode], max_total_tasks: int) -> bool:
    """检查任务总数是否超过限制"""
    total_tasks = len(task_tree)
    return total_tasks > max_total_tasks

def calculate_max_depth(total_tasks: int, base_max_depth: int = 3) -> int:
    """根据任务总数计算最大允许深度"""
    return max(1, base_max_depth - (total_tasks // 15))

def collect_ancestor_descriptions(task_id: str, task_tree: Dict[str, TaskNode]) -> List[str]:
    """收集当前任务的所有祖先任务描述"""
    descriptions = []
    current_id = task_tree[task_id]["parent_id"]
    while current_id:
        if current_id in task_tree:
            descriptions.append(task_tree[current_id]["description"])
            current_id = task_tree[current_id]["parent_id"]
        else:
            break
    return descriptions

def collect_sibling_tasks(task_id: str, task_tree: Dict[str, TaskNode]) -> List[str]:
    """收集当前任务的同级任务描述"""
    siblings = []
    parent_id = task_tree[task_id]["parent_id"]
    if parent_id and parent_id in task_tree:
        parent = task_tree[parent_id]
        for child_id in parent["children_ids"]:
            if child_id != task_id and child_id in task_tree:
                siblings.append(task_tree[child_id]["description"])
    return siblings

def check_force_leaf_by_depth(task_depth: int, total_tasks: int, max_depth: int) -> Tuple[bool, str]:
    """根据任务深度判断是否强制设为叶节点，返回(是否强制叶节点, 深度信息)"""
    force_leaf = task_depth >= max_depth
    
    depth_info = ""
    if force_leaf:
        depth_info = f"""
        注意：当前任务已经位于深度{task_depth}，已达到当前允许的最大深度({max_depth})。
        系统的任务总数已达{total_tasks}个。
        请将此任务视为叶节点执行，除非它绝对必须进一步分解。
        """
    
    return force_leaf, depth_info

def mark_as_leaf_node(task: TaskNode, task_id: str, dfs_stack: List[Tuple[str, str]]) -> None:
    """将任务标记为叶节点，并更新DFS栈"""
    task["is_leaf"] = True
    task["status"] = "pending_execution"
    dfs_stack.append((task_id, "EXECUTE"))

def prepare_context_info(ancestor_descriptions: List[str], sibling_tasks: List[str]) -> str:
    """准备任务分解的上下文信息"""
    context_info = ""
    
    if ancestor_descriptions:
        context_info += f"""
        这个任务的上下文路径是:
        {' -> '.join(reversed(ancestor_descriptions))} -> 当前任务
        """
    
    if sibling_tasks:
        context_info += f"""
        同级任务包括:
        {json.dumps(sibling_tasks, ensure_ascii=False)}
        """
        
    return context_info

def generate_task_limit_warning(total_tasks: int, max_total_tasks: int) -> str:
    """生成任务数量接近上限的警告信息"""
    task_limit_warning = ""
    if total_tasks > max_total_tasks * 0.7:
        task_limit_warning = f"""
        警告：系统当前任务总数已达{total_tasks}个，接近最大限制({max_total_tasks})。
        强烈建议将此任务视为叶节点而不是进一步分解。
        """
    return task_limit_warning

def extract_json_from_markdown(text: str) -> str:
    """从可能包含markdown的文本中提取JSON部分"""
    # 查找JSON块
    import re
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        return json_match.group(1).strip()
    
    # 尝试找到花括号包围的内容
    json_match = re.search(r'({[\s\S]*})', text)
    if json_match:
        return json_match.group(1).strip()
    
    # 如果上述都失败，返回原始文本
    return text.strip()
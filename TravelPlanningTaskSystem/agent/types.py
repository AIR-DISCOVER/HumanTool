print("types.py loaded")

from typing import Dict, List, Optional, TypedDict, Any, Tuple

class TaskNode(TypedDict):
    id: str
    question: str
    description: str
    answer: Optional[str]
    parent_id: Optional[str]
    children_ids: List[str]
    is_root: bool
    is_leaf: bool
    status: str
    prompt_for_llm: Optional[str]

class GraphState(TypedDict):
    input_query: str
    task_tree: Dict[str, TaskNode]
    dfs_stack: List[Tuple[str, str]]
    intermediate_results: Dict[str, Any]
    active_task_id: Optional[str]
    current_routing_action: Optional[str]
    messages: List[Dict[str, str]]
    next_task_list: List[str]
    error_message: Optional[str]
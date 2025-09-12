from typing import TypedDict, List, Dict, Any, Optional
import logging
from langchain_core.language_models.chat_models import BaseChatModel


class HumanToolPreferences(TypedDict):
    """用户偏好设置"""
    communication_style: Optional[str] # 用户期望的交流风格 (例如: "formal", "casual", "concise")
    task_style: Optional[str]          # 用户处理任务的风格 (例如: "detailed_oriented", "big_picture")
    task_allocate: Optional[str]       # 用户在任务分配中想承担的权重 (例如: "lead", "collaborate", "delegate_specifics")

class HumanToolInputSchemaProperties(TypedDict, total=False):
    """
    Tool 参数的 JSON Schema 属性定义。
    每个键是一个参数名，值是该参数的 schema (例如: {"type": "string", "description": "..."})。
    """
    pass # 具体属性将由每个工具定义

class HumanToolInputSchema(TypedDict):
    """Tool 参数的 JSON Schema"""
    type: str # 通常是 "object"
    properties: HumanToolInputSchemaProperties
    required: Optional[List[str]]

class HumanTool(TypedDict):
    """定义一个人类工具/能力档案"""
    user_name: str                     # 用户的唯一标识符
    tool_name: str                     # Tool 的唯一标识符 (例如: user_name + "_" + capability_name)
    description: str                   # 供LLM阅读的描述，描述这个接口/能力提供什么
    capabilities: List[str]            # 对用户工具所具备专长的分类描述 (例如: ["legal_document_review", "software_architecture_design"])
    preferences: Optional[HumanToolPreferences] # 用户偏好
    accessible: bool                   # 当前是否可联系/可用
    input_schema: Optional[HumanToolInputSchema] # 调用此人类能力时，期望的输入结构 (用于LLM构造更精确的 human_question)

def get_human_tool_description_for_llm(human_tools: dict) -> str:
    """为LLM生成人类工具的描述文本 - 支持新的overall_profile结构"""
    if not human_tools:
        return "\n**👤 用户画像**: 暂无特定用户画像，使用通用协作模式\n\n"
    
    description = "\n**👤 请参考用户的画像来调整话术**:\n\n"
    
    # 🎯 支持新的overall_profile结构（来自profile_manager）
    for tool_name, tool_config in human_tools.items():
        user_id = tool_config.get('user_id', tool_name)
        display_name = tool_config.get('display_name', user_id)
        overall_profile = tool_config.get('overall_profile', '')
        
        description += f"### 🎯 {display_name} ({user_id})\n\n"
        
        # 🎯 关键修复：优先显示overall_profile（包含所有能力描述）
        if overall_profile:
            description += f"**档案描述**: {overall_profile}\n\n"
        else:
            description += f"**档案描述**: 暂无详细档案信息\n\n"
        
        # 🎯 保持向后兼容：如果有分类能力信息，也显示
        info_capabilities = tool_config.get('information_capabilities', [])
        if info_capabilities:
            description += f"**📚 信息获取能力**:\n"
            for i, capability in enumerate(info_capabilities, 1):
                description += f"{i}. {capability}\n"
            description += "\n"
        
        reasoning_capabilities = tool_config.get('reasoning_capabilities', [])
        if reasoning_capabilities:
            description += f"**🧠 推理分析能力**:\n"
            for i, capability in enumerate(reasoning_capabilities, 1):
                description += f"{i}. {capability}\n"
            description += "\n"
        
        # 兼容旧格式
        old_capabilities = tool_config.get('capabilities', [])
        if old_capabilities and not info_capabilities and not reasoning_capabilities:
            description += f"**通用能力**: {', '.join(old_capabilities)}\n\n"
        
        # last_updated = tool_config.get('last_updated', '')
        # if last_updated:
        #     description += f"*档案更新时间: {last_updated}*\n\n"
        
        description += "---\n\n"
    
    description += """💡 **协作策略**:

    


### 一、**【交互模式】**

Initially: 
Prime：在交互开始时，向用户告知背景并设定任务目标
Configure：告知用户你的能力、将如何与用户协同，可以根据用户偏好和需求定制交互方式

During interaction:
Probe: 通过逐步深入提问用户，收集全面信息
Cue: 提供有用的提示或建议来引导用户回应

Elicit: 激发用户的深度思考和创造，激发用户创造力
Augment: 增强和完善用户的输出

Guide: 逐步引导用户完成结构化流程 

Critique: 批驳、挑战用户，进行辩论，增强批判性思考、更全面考虑问题

When wrong:
Explain: 当用户出现困惑或误解时提供解释
Correct: *纠正用户时必选* - 纠正用户的错误，并寻求准确信息
Reflect：用户表示不满时必选 - 反思用户提出的问题，承认失败并改进方法

Ending: 
Approve: 在完成或实施解决方案前寻求用户最终确认 

### 二、**【沟通原则】**
Naturalness:
Echoing responses
Casual language

Emotionality:
Feedback
Using emoji
Encourage 

Build relationship:
Emphatic messages
Humor

Transparency:
Present capabilities：告知用户你的能力
Acknowledge limitations：告知用户你的局限

What to avoid:
Repetitive messages
Exaggeration



"""
    
    return description

# 🎯 全局管理器
_global_human_tool_manager = None

def set_global_human_tool_manager(manager):
    """设置全局人类工具管理器"""
    global _global_human_tool_manager
    _global_human_tool_manager = manager

def get_global_human_tool_manager():
    """获取全局人类工具管理器"""
    return _global_human_tool_manager

def get_user_human_tools(user_name: str) -> Dict[str, Any]:
    """获取用户的人类工具配置 - 全局函数版本"""
    if _global_human_tool_manager:
        return _global_human_tool_manager.get_user_human_tools(user_name)
    else:
        # 回退到默认配置
        manager = HumanToolManager()
        return manager.get_user_human_tools(user_name)

class HumanToolManager:
    """人类工具管理器"""
    
    def __init__(self, llm: BaseChatModel, user_name: str, database_manager=None, verbose: bool = False):
        self.llm = llm
        self.user_name = user_name
        self.database_manager = database_manager
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
    
    def get_user_human_tools(self, user_name: str) -> Dict[str, Any]:
        """获取用户的专业档案配置"""
        
        print(f"🔍 [DEBUG] HumanToolManager.get_user_human_tools() 开始")
        print(f"🔍 [DEBUG] 请求的用户名: {user_name}")
        print(f"🔍 [DEBUG] 数据库管理器存在: {self.database_manager is not None}")
        
        # 🎯 从数据库获取用户档案
        if self.database_manager:
            try:
                print(f"🔍 [DEBUG] 正在从数据库获取用户档案...")
                print(f"🔍 [DEBUG] 数据库管理器类型: {type(self.database_manager)}")
                print(f"🔍 [DEBUG] 数据库管理器属性: {dir(self.database_manager)}")
                
                # 检查是否有 get_user_profile 方法
                if hasattr(self.database_manager, 'get_user_profile'):
                    user_profile = self.database_manager.get_user_profile(user_name)
                    print(f"🔍 [DEBUG] 数据库返回的用户档案: {user_profile}")
                else:
                    print(f"❌ [DEBUG] 数据库管理器缺少 get_user_profile 方法")
                    user_profile = None
                
                if user_profile:
                    # 🎯 关键修复：检查档案是否有有效的描述信息
                    overall_profile = user_profile.get('overall_profile', '')
                    description = user_profile.get('description', '')
                    
                    print(f"🔍 [DEBUG] overall_profile: {overall_profile[:100] if overall_profile else 'None'}...")
                    print(f"🔍 [DEBUG] description: {description[:100] if description else 'None'}...")
                    
                    # 如果数据库中有有效的档案描述，使用数据库档案
                    if overall_profile or description:
                        print(f"✅ [DEBUG] 使用数据库用户档案: {user_name}")
                        if self.verbose:
                            print(f"✅ 使用数据库用户档案: {user_name}")
                        result = self._convert_db_profile_to_tools(user_profile)
                        print(f"🔍 [DEBUG] 转换后的工具配置: {result}")
                        return result
                    else:
                        print(f"⚠️ [DEBUG] 数据库用户档案描述为空，回退到默认档案: {user_name}")
                        if self.verbose:
                            print(f"⚠️ 数据库用户档案描述为空，回退到默认档案: {user_name}")
                else:
                    print(f"❌ [DEBUG] 数据库中未找到用户档案: {user_name}")
                
            except Exception as e:
                print(f"❌ [DEBUG] 从数据库获取用户档案失败: {e}")
                if self.verbose:
                    print(f"从数据库获取用户档案失败: {e}")
        else:
            print(f"⚠️ [DEBUG] 数据库管理器不存在")
        
        # 🎯 回退到默认档案
        print(f"🔄 [DEBUG] 使用默认用户档案: {user_name}")
        if self.verbose:
            print(f"🔄 使用默认用户档案: {user_name}")
        result = {"user_profile": self._get_default_profile(user_name)}
        print(f"🔍 [DEBUG] 默认档案结果: {result}")
        return result
    
    def _convert_db_profile_to_tools(self, user_profile: Dict) -> Dict[str, Any]:
        """将数据库用户档案转换为工具配置格式"""
        import json
        
        # 解析JSON字段
        info_capabilities = user_profile.get('information_capabilities', '[]')
        reasoning_capabilities = user_profile.get('reasoning_capabilities', '[]')
        
        if isinstance(info_capabilities, str):
            try:
                info_capabilities = json.loads(info_capabilities)
            except:
                info_capabilities = []
        
        if isinstance(reasoning_capabilities, str):
            try:
                reasoning_capabilities = json.loads(reasoning_capabilities)
            except:
                reasoning_capabilities = []
        
        # 🎯 关键修复：确保返回的数据结构包含所有必要字段
        user_id = user_profile.get('id')
        display_name = user_profile.get('display_name') or user_profile.get('name') or user_id
        overall_profile = user_profile.get('overall_profile', '')
        
        # 🎯 如果没有overall_profile，使用description字段
        if not overall_profile:
            overall_profile = user_profile.get('description', '')
        
        # 🎯 如果还是没有，根据用户ID生成默认描述
        if not overall_profile:
            if user_id == 'user_main':
                overall_profile = "通用创作协作者，具备多元化背景和灵活适应能力"
            elif user_id == 'user_1':
                overall_profile = "创作老手，擅长文学创作和故事构建，具有丰富的创作经验"
            else:
                overall_profile = f"专业协作者 {display_name}，具备专业的协作能力"
        
        return {
            "user_profile": {
                "user_id": user_id,
                "display_name": display_name,
                "overall_profile": overall_profile,
                "information_capabilities": info_capabilities,
                "reasoning_capabilities": reasoning_capabilities,
                "last_updated": str(user_profile.get('last_updated', ''))
            }
        }
    
    def _get_default_profile(self, user_name: str) -> Dict[str, Any]:
        """🎯 移除硬编码档案 - 仅在数据库完全不可用时提供最基础的回退"""
        if self.verbose:
            print(f"⚠️ 使用最基础的回退档案: {user_name}")
        
        # 🎯 仅提供最基础的通用档案，不包含具体的硬编码内容
        return {
            "user_id": user_name,
            "display_name": user_name,
            "overall_profile": f"协作者 {user_name}，档案信息需要从数据库获取",
            "information_capabilities": [],
            "reasoning_capabilities": [],
            "last_updated": ""
        }
    
    def get_available_profiles(self) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的用户档案"""
        try:
            profiles = {}
            
            # 🎯 修复：从数据库获取用户档案
            if self.database_manager:
                try:
                    # 尝试从数据库获取用户档案
                    db_profiles = self.database_manager.get_all_users()
                    for user in db_profiles:
                        profiles[user.get('id')] = {
                            'name': user.get('name', user.get('id')),
                            'capabilities': {
                                'description': user.get('description', '通用用户档案')
                            }
                        }
                except Exception as e:
                    self.logger.warning(f"从数据库获取档案失败: {e}")
            
            # 🎯 移除硬编码档案 - 如果数据库没有数据，返回空字典
            if not profiles:
                self.logger.warning("数据库中没有用户档案数据，返回空档案列表")
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"获取可用档案失败: {e}")
            # 返回最基本的档案
            return {
                'user_main': {
                    'name': '默认用户',
                    'capabilities': {'description': '通用用户档案'}
                }
            }
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取指定用户的档案信息"""
        try:
            available_profiles = self.get_available_profiles()
            return available_profiles.get(user_id, {
                'name': user_id,
                'capabilities': {'description': '通用用户档案'}
            })
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return {'name': user_id, 'capabilities': {'description': '通用用户档案'}}
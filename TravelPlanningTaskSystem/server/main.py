from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import uuid
import traceback
import os
import sys
import logging
import json
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from sqlalchemy import text

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
database_manager = None

# 只保留一次环境变量加载和路径设置
def setup_environment():
    """设置环境变量和项目路径（确保只执行一次）"""
    # 避免重复执行
    if hasattr(setup_environment, '_executed'):
        return
    setup_environment._executed = True
    
    # 加载agent目录下的环境变量
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    env_path = os.path.join(project_root, "agent", ".env")
    
    load_dotenv(env_path)
    print(f"📁 加载环境变量1: {env_path}")
    
    # 添加项目路径
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"📂 添加项目路径: {project_root}")

# 执行环境设置
setup_environment()
print("✅ [DIAGNOSTIC] setup_environment() executed.") # 新增

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "your_mysql_username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_mysql_password")
DB_NAME = os.getenv("DB_NAME", "tata")

# 导入拆分后的模块
from server.api_models import ChatRequest, ChatResponse, DraftUpdateRequest, HealthResponse, ExportResponse
from server.streaming_wrapper import StreamingWrapper
from server.stream_handlers import StreamHandler

# 初始化组件（确保只执行一次）
def initialize_agent():
    """初始化Agent组件（确保只执行一次）"""
    global AGENT_AVAILABLE, streaming_wrapper
    
    # 避免重复执行
    if hasattr(initialize_agent, '_executed'):
        return AGENT_AVAILABLE, streaming_wrapper
    initialize_agent._executed = True
    
    try:
        # 使用新架构
        from agent.graph import AgendaAgent  # 确保使用新版本
        streaming_wrapper = StreamingWrapper(AgendaAgent)
        return True, streaming_wrapper
    except Exception as e:
        print(f"❌ Failed to import Agent: {e}")
        return False, None

# 执行初始化
AGENT_AVAILABLE, streaming_wrapper = initialize_agent()
print(f"✅ [DIAGNOSTIC] AGENT_AVAILABLE: {AGENT_AVAILABLE}") # 新增

# 🎯 使用新的 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global database_manager
    
    # 启动时执行
    print("🚀【server/main】 TATA Story Assistant 启动中...")
    
    try:
        from agent.persistence.database import DatabaseManager
        database_manager = DatabaseManager()
        
        if database_manager.test_connection():
            print("✅【server/main】 数据库连接成功")
        else:
            print("❌【server/main】 数据库连接失败，将使用内存模式")
            database_manager = None
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print("⚠️ 将在无数据库模式下运行")
        database_manager = None
    
    print("✅ 应用启动完成")
    
    # yield 分隔启动和关闭事件
    yield
    
    # 关闭时执行
    print("🔄 应用关闭中...")
    if database_manager:
        try:
            # 如果有需要清理的数据库连接
            print("📊 关闭数据库连接...")
        except Exception as e:
            print(f"⚠️ 数据库关闭时出错: {e}")
    print("✅ 应用已关闭")

print("✅ [DIAGNOSTIC] About to define FastAPI app instance.") # 新增
# 🎯 使用 lifespan 参数创建 FastAPI 应用
app = FastAPI(
    title="TATA Story Assistant API", 
    version="2.0.0",
    lifespan=lifespan  # 使用新的生命周期处理器
)
print("✅ [DIAGNOSTIC] FastAPI app instance defined.") # 新增

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)
print("✅ [DIAGNOSTIC] Middleware added.") # 新增

# 全局存储
sessions = {}
drafts_storage = {}
user_agents = {}  # {user_id: {session_id: agent}}

@app.get("/")
async def root():
    return {
        "message": "TATA Story Assistant API",
        "version": "2.0.0",
        "agent_available": AGENT_AVAILABLE,
        "endpoints": {
            "chat": "/api/chat", 
            "drafts": "/api/drafts", 
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        agent_available=AGENT_AVAILABLE,
        active_sessions=len(sessions),
        timestamp=time.time()
    )

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """主聊天端点 - 支持多轮交互记忆"""
    print(f"🎯【main】 [CHAT] 收到请求:")
    print(f"  - Message: {request.message}")
    print(f"  - User ID: {request.user_id}")
    print(f"  - Session ID: {request.session_id}")
    print(f"  - Stream: {request.stream}")
    
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Agent not available")
    
    start_time = time.time()
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    user_id = request.user_id or "user_main"
    
    # 确保用户存在
    if database_manager:
        user_info = database_manager.get_user(user_id)
        if not user_info:
            database_manager.create_user(user_id, name=user_id)
            print(f"✅ [CHAT] 创建新用户: {user_id}")
    
    # 🎯 修复：每次都重新创建Agent以确保使用最新的用户档案
    print(f"🆕 [CHAT] 为用户 {user_id} 创建新Agent实例 (session: {session_id})")
    print(f"🔍 [DEBUG] 传递给Agent的参数:")
    print(f"  - user_name: {user_id}")
    print(f"  - database_manager: {database_manager}")
    print(f"  - verbose: True")
    
    try:
        agent = streaming_wrapper.create_agent(
            verbose=True,
            user_name=user_id,
            database_manager=database_manager
        )
        
        print(f"🔍 [DEBUG] Agent创建完成，检查用户档案...")
        
        # 🎯 验证Agent是否使用了正确的用户档案
        if hasattr(agent, 'agent_core') and hasattr(agent.agent_core, 'human_tools'):
            human_tools = agent.agent_core.human_tools
            print(f"🔍 [DEBUG] Agent的human_tools: {human_tools}")
            
            if 'user_profile' in human_tools:
                profile = human_tools['user_profile']
                print(f"🔍 [DEBUG] Agent使用的用户档案:")
                print(f"  - 用户ID: {profile.get('user_id')}")
                print(f"  - 显示名称: {profile.get('display_name')}")
                print(f"  - 档案描述: {profile.get('overall_profile', 'None')[:100]}...")
            else:
                print(f"❌ [DEBUG] Agent的human_tools中没有user_profile")
        else:
            print(f"❌ [DEBUG] Agent没有human_tools属性")
        
        # 🎯 可选：仍然缓存Agent但添加刷新机制
        if user_id not in user_agents:
            user_agents[user_id] = {}
        
        user_agents[user_id][session_id] = {
            "agent": agent,
            "created_at": time.time(),
            "user_id": user_id  # 记录用户ID用于调试
        }
        
        print(f"✅ [CHAT] Agent创建成功，使用用户档案: {user_id}")
        
    except Exception as e:
        print(f"❌ [CHAT] Agent创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")
    
    if request.stream:
        # 流式响应
        stream_handler = StreamHandler()
        return StreamingResponse(
            stream_handler.generate_stream_response_with_memory(
                agent, 
                request.message, 
                session_id,
                user_id,
                database_manager
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 非流式响应
        try:
            result = agent.run_interactive(request.message, session_id)
            
            return ChatResponse(
                response=result.get("final_answer", ""),
                status="completed" if not result.get("is_interactive_pause") else "waiting",
                session_id=session_id,
                agenda=result.get("final_agenda"),
                draft_contents=result.get("draft_contents"),
                processing_time=time.time() - start_time
            )
        except Exception as e:
            print(f"❌ [CHAT] 非流式聊天错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# 用户管理API
@app.post("/api/users")
async def create_user(user_data: dict):
    """创建用户"""
    if not database_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    success = database_manager.create_user(
        user_id=user_id,
        name=user_data.get("name"),
        email=user_data.get("email"),
        preferences=user_data.get("preferences", {})
    )
    
    if success:
        return {"status": "created", "user_id": user_id}
    else:
        raise HTTPException(status_code=409, detail="User already exists")

# 获取可用的用户账号列表
@app.get("/api/users/accounts")
async def get_user_accounts():
    """获取可用的用户账号列表"""
    logger.info("✅ [DIAGNOSTIC] /api/users/accounts endpoint called.")
    try:
        # 🎯 检查数据库连接
        if not database_manager or not database_manager.test_connection():
            logger.warning("数据库连接失败，使用降级响应")
            raise Exception("数据库连接失败")
        
        # 🎯 简化数据库查询 - 直接查询而不依赖可能不存在的方法
        try:
            db = database_manager.get_session()
            
            # 🎯 先检查表结构，确定使用哪种查询方式
            try:
                # 检查是否有新字段
                result = db.execute(text("SHOW COLUMNS FROM users LIKE 'user_type'"))
                has_user_type = result.fetchone() is not None
                
                result = db.execute(text("SHOW COLUMNS FROM users LIKE 'display_name'"))
                has_display_name = result.fetchone() is not None
                
                logger.info(f"数据库字段检查: user_type={has_user_type}, display_name={has_display_name}")
                
                if has_user_type and has_display_name:
                    # 🎯 使用新字段查询
                    sql = """
                        SELECT id, name, display_name, user_type, experiment_group, description
                        FROM users
                        ORDER BY id
                    """
                    result = db.execute(text(sql))
                    db_users = result.fetchall()
                    
                    accounts = []
                    for user in db_users:
                        accounts.append({
                            'id': user[0],
                            'name': user[2] or user[1],  # display_name 或 name
                            'experiment_group': user[4] or 'Control',
                            'description': user[5] or '',
                            'user_type': user[3] or 'general'
                        })
                    
                    logger.info(f"使用新字段查询到 {len(accounts)} 个用户")
                    
                else:
                    # 🎯 降级到基础字段查询
                    sql = "SELECT id, name FROM users ORDER BY id"
                    result = db.execute(text(sql))
                    db_users = result.fetchall()
                    
                    accounts = []
                    for user in db_users:
                        # 🎯 根据用户ID生成合适的显示信息
                        if user[0] == 'user_main':
                            accounts.append({
                                'id': user[0],
                                'name': '默认用户',
                                'experiment_group': 'Control',
                                'description': '通用创作协作者',
                                'user_type': 'general'
                            })
                        elif user[0] == 'user_tyr':
                            accounts.append({
                                'id': user[0], 
                                'name': '唐苑容',
                                'experiment_group': 'A',
                                'description': '创作老手，擅长文学创作和故事构建',
                                'user_type': 'admin'
                            })
                        else:
                            # 其他用户使用通用格式
                            accounts.append({
                                'id': user[0],
                                'name': user[1] or user[0],
                                'experiment_group': 'Control',
                                'description': '',
                                'user_type': 'general'
                            })
                    
                    logger.info(f"使用基础字段查询到 {len(accounts)} 个用户")
                
            except Exception as query_error:
                logger.error(f"数据库查询错误: {query_error}")
                raise query_error
            
            finally:
                db.close()
            
            if accounts:
                logger.info(f"成功从数据库返回 {len(accounts)} 个可用账号")
                return {"accounts": accounts, "total": len(accounts)}
            else:
                logger.warning("数据库中没有找到用户，使用降级响应")
                raise Exception("数据库中没有用户")
            
        except Exception as db_error:
            logger.warning(f"数据库操作失败: {db_error}")
            raise db_error
        
    except Exception as e:
        logger.error(f"获取用户账号列表失败: {e}")
        
        # 🎯 降级响应 - 确保始终返回可用账号
        fallback_accounts = [
            {
                "id": "user_main", 
                "name": "默认用户", 
                "experiment_group": "Control",
                "description": "通用创作协作者，适应性强",
                "user_type": "general"
            },
            {
                "id": "user_tyr", 
                "name": "唐苑容", 
                "experiment_group": "A",
                "description": "创作老手，擅长文学创作和故事构建",
                "user_type": "admin"
            }
        ]
        
        logger.info(f"使用降级配置返回 {len(fallback_accounts)} 个账号")
        return {"accounts": fallback_accounts, "total": len(fallback_accounts)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """获取用户信息"""
    if not database_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    user_info = database_manager.get_user(user_id)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/users/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """获取用户的会话列表"""
    if not database_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    sessions = database_manager.get_user_sessions(user_id)
    return {"user_id": user_id, "sessions": sessions}

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取会话的消息历史"""
    if not database_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    messages = database_manager.get_messages(session_id)
    return {"session_id": session_id, "messages": messages}

@app.get("/api/drafts/{session_id}")
async def get_drafts(session_id: str):
    """获取会话的所有草稿"""
    if database_manager:
        drafts = database_manager.get_drafts(session_id)
        return {"session_id": session_id, "drafts": drafts}
    else:
        # 回退到内存存储
        return {"session_id": session_id, "drafts": drafts_storage.get(session_id, {})}

@app.post("/api/drafts/update")
async def update_draft(request: DraftUpdateRequest):
    """更新草稿内容"""
    if request.session_id not in drafts_storage:
        drafts_storage[request.session_id] = {}
    
    drafts_storage[request.session_id][request.draft_id] = {
        "content": request.content,
        "last_updated": time.time(),
        "updated_by": "user"
    }
    
    return {
        "status": "updated", 
        "draft_id": request.draft_id
    }

@app.post("/api/drafts/{session_id}/export")
async def export_drafts(session_id: str) -> ExportResponse:
    """导出会话的所有草稿"""
    if session_id not in drafts_storage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    drafts = drafts_storage[session_id]
    combined_content = "\n".join([
        f"## {draft_id}\n\n{draft_data['content']}\n" 
        for draft_id, draft_data in drafts.items()
    ])
    
    return ExportResponse(
        session_id=session_id,
        export_content=combined_content,
        exported_at=time.time()
    )

# 会话管理API
@app.get("/api/sessions")
async def get_sessions():
    """获取活跃会话列表"""
    session_info = {}
    for session_id, session_data in sessions.items():
        session_info[session_id] = {
            "created_at": session_data["created_at"],
            "message_count": session_data["message_count"],
            "has_drafts": session_id in drafts_storage and len(drafts_storage[session_id]) > 0
        }
    return {"sessions": session_info}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话和相关数据"""
    deleted_items = []
    
    if session_id in sessions:
        del sessions[session_id]
        deleted_items.append("session")
    
    if session_id in drafts_storage:
        del drafts_storage[session_id]
        deleted_items.append("drafts")
    
    if not deleted_items:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "status": "deleted",
        "session_id": session_id,
        "deleted_items": deleted_items
    }



# 🎯 添加账号选择保存端点
@app.post("/api/users/select-account")
async def select_account(request: Dict[str, Any]):
    """保存用户账号选择"""
    try:
        account_id = request.get("account_id")
        if not account_id:
            raise HTTPException(status_code=400, detail="缺少 account_id")
        
        logger.info(f"用户选择账号: {account_id}")
        
        # 这里可以保存用户选择到数据库或缓存
        # 目前只是记录日志
        
        return {"success": True, "message": f"账号 {account_id} 选择已保存"}
        
    except Exception as e:
        logger.error(f"保存账号选择失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🎯 关键修复：配置静态文件服务
# 确保静态文件目录存在
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

generated_images_dir = "static/generated_images"
if not os.path.exists(generated_images_dir):
    os.makedirs(generated_images_dir, exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/user-profiles")
async def get_user_profiles():
    """获取用户档案列表"""
    try:
        profiles = []
        
        # 从数据库获取用户档案
        if database_manager:
            try:
                db_users = database_manager.get_all_users()
                for user in db_users:
                    profiles.append({
                        'id': user.get('id'),
                        'name': user.get('name', user.get('id')),
                        'description': user.get('description', '用户档案')
                    })
            except Exception as db_error:
                logger.error(f"从数据库获取档案失败: {db_error}")
        
        # 如果数据库没有数据或连接失败，使用默认档案
        if not profiles:
            profiles = [
                {
                    'id': 'user_main',
                    'name': '默认用户',
                    'description': '通用用户档案，适应性强'
                },
                {
                    'id': 'travel_expert',
                    'name': '旅游专家',
                    'description': '专业的旅游规划专家'
                },
                {
                    'id': 'budget_traveler',
                    'name': '预算旅行者',
                    'description': '注重性价比的旅行者'
                },
                {
                    'id': 'luxury_traveler',
                    'name': '奢华旅行者',
                    'description': '追求高端体验的旅行者'
                }
            ]
        
        # 🎯 修复：直接返回档案列表，以匹配前端期望的数组格式
        return profiles
        
    except Exception as e:
        logger.error(f"获取用户档案失败: {e}")
        # 🎯 修复：在异常情况下也返回一个包含默认用户的数组
        return [{'id': 'user_main', 'name': '默认用户', 'description': '通用用户档案'}]

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口 - 支持配置初始化"""
    try:
        # 检查是否为配置初始化请求
        if request.message.startswith('{') and 'user_profile' in request.message:
            # 这是配置初始化请求
            logger.info(f"收到配置初始化请求: {request.message}")
            
            if not AGENT_AVAILABLE:
                raise HTTPException(status_code=503, detail="AI Agent not available")
            
            session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
            user_id = request.user_id or "user_main"
            
            agent = streaming_wrapper.create_agent(
                verbose=True,
                user_name=user_id,
                database_manager=database_manager
            )
            
            result = agent.run_interactive(request.message, session_id)
            
            # 🎯 修复：配置初始化也需要流式响应格式
            async def generate_config_response():
                # 发送连接确认
                yield f"data: {json.dumps({'type': 'connection', 'content': '连接已建立', 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
                
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'content': '配置初始化中...', 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)
                
                # 发送开场白作为最终回复
                final_answer = result.get('final_answer', '配置完成')
                final_msg = json.dumps({
                    'type': 'final',
                    'content': final_answer,
                    'timestamp': time.time(),
                    'metadata': {
                        'session_id': session_id,
                        'agenda': result.get('agenda_doc', ''),
                        'user_profile': user_id,
                        'is_config_init': True
                    }
                }, ensure_ascii=False)
                yield f"data: {final_msg}\n\n"
                
                # 结束标记
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_config_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # 普通消息的流式处理
        logger.info(f"处理普通流式消息: {request.message[:50]}...")
        if not AGENT_AVAILABLE:
            raise HTTPException(status_code=503, detail="AI Agent not available")

        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        user_id = request.user_id or "user_main"

        # 🎯 修复：每次都重新创建Agent以确保使用最新的用户档案
        print(f"🆕 [STREAM] 为用户 {user_id} 创建新Agent实例 (session: {session_id})")
        agent = streaming_wrapper.create_agent(
            verbose=True, user_name=user_id, database_manager=database_manager
        )
        
        # 🎯 可选：仍然缓存Agent但每次都刷新
        if user_id not in user_agents:
            user_agents[user_id] = {}
        user_agents[user_id][session_id] = {
            "agent": agent,
            "created_at": time.time(),
            "user_id": user_id
        }
        
        print(f"✅ [STREAM] Agent创建成功，使用用户档案: {user_id}")
        
        stream_handler = StreamHandler()
        return StreamingResponse(
            stream_handler.generate_stream_response_with_memory(
                agent, request.message, session_id, user_id, database_manager
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"流式聊天接口错误: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    
    # 🎯 确保工作目录正确
    print(f"当前工作目录: {os.getcwd()}")
    print(f"静态文件目录: {os.path.abspath('static')}")
    
    # 确保目录存在
    os.makedirs("static/generated_images", exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

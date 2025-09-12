import json
import time
import uuid
import asyncio
import traceback
from typing import Dict, Any, Set, Callable, AsyncGenerator
import threading
from queue import Queue

class StreamHandler:
    """处理流式响应的逻辑 - 修复版本"""
    
    def __init__(self):
        self.event_counter = 0
        self.event_queue = Queue()
        self.sent_events = set()  # 🎯 新增：记录已发送的事件
        print(f"✅ [STREAM] StreamHandler 初始化完成")

    def create_stream_callback(self) -> Callable:
        """创建流式回调函数 - 修复内容截断问题"""
        
        def stream_callback(event_type: str, content: str, metadata: Dict[str, Any] = None) -> str:
            """流式回调函数 - 将事件加入队列"""
            try:
                self.event_counter += 1
                
                # 🎯 关键修复：创建事件唯一标识
                event_id = f"{event_type}_{hash(content[:100])}_{metadata.get('tool_name', '') if metadata else ''}"
                
                # 检查是否已发送过相同事件
                if event_id in self.sent_events:
                    print(f"⚠️ [STREAM CALLBACK] 跳过重复事件: {event_type}")
                    return ""
                
                # 记录事件
                self.sent_events.add(event_id)
                
                # 基础事件数据 - 不要截断内容！
                event_data = {
                    'type': event_type,
                    'content': content,  # 保持完整内容，不要截断
                    'timestamp': time.time(),
                    'id': self.event_counter
                }
                
                # 根据事件类型添加元数据
                if event_type == 'tool_call' and metadata:
                    event_data['metadata'] = {
                        'call_id': metadata.get('call_id', ''),
                        'tool_name': metadata.get('tool_name', ''),
                        'tool_display_name': metadata.get('tool_display_name', '工具调用'),
                        'params': metadata.get('params', {}),
                        'status': metadata.get('status', 'calling')
                    }
                elif event_type == 'tool_result' and metadata:
                    event_data['metadata'] = {
                        'call_id': metadata.get('call_id', ''),
                        'tool_name': metadata.get('tool_name', ''),
                        'result': metadata.get('result', content),  # 完整结果
                        'status': 'completed'
                    }
                elif event_type == 'assistant_message' and metadata:
                    event_data['metadata'] = {
                        'message_type': metadata.get('message_type', 'general'),
                        'tool_name': metadata.get('tool_name', ''),
                        'step': metadata.get('step', '')
                    }
                elif event_type == 'draft_update' and metadata:
                    event_data['metadata'] = {
                        'draft_id': metadata.get('draft_id', ''),
                        'content': metadata.get('content', content),  # 完整草稿内容
                        'updated_by': metadata.get('updated_by', 'ai')
                    }
                elif event_type == 'agenda_update' and metadata:
                    event_data['metadata'] = {
                        'agenda_summary': metadata.get('agenda_summary', {}),
                        'agenda_text': metadata.get('agenda_text', '')
                    }
                
                event_json = json.dumps(event_data, ensure_ascii=False)
                formatted_event = f"data: {event_json}\n\n"
                
                # 关键：将事件放入队列
                self.event_queue.put(formatted_event)
                
                # 在日志中显示截断版本，但实际传输完整内容
                content_preview = content[:50] + "..." if len(content) > 50 else content
                print(f"📤 [STREAM CALLBACK #{self.event_counter}] {event_type}: {content_preview} (队列大小: {self.event_queue.qsize()})")
                return formatted_event

            except Exception as e:
                print(f"❌ [STREAM CALLBACK] 错误: {e}")
                error_event = json.dumps({
                    'type': 'error',
                    'content': f'流式回调错误: {str(e)}',
                    'timestamp': time.time()
                }, ensure_ascii=False)
                return f"data: {error_event}\n\n"

        return stream_callback
    
    async def generate_stream_response(
        self, 
        agent, 
        message: str, 
        session_id: str,
        drafts_storage: Dict[str, Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """生成流式响应 - 修复实时发送"""
        try:
            print(f"🌊 [STREAM] Starting stream for session {session_id}")
            
            # 重置状态
            self.event_counter = 0
            # 清空队列
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except:
                    break
            
            # 立即发送连接确认
            connection_msg = json.dumps({
                'type': 'connection', 
                'content': '连接已建立', 
                'timestamp': time.time()
            }, ensure_ascii=False)
            yield f"data: {connection_msg}\n\n"
            await asyncio.sleep(0.01)
            
            # 设置流式回调函数
            stream_callback = self.create_stream_callback()
            
            # 设置回调
            if hasattr(agent, 'set_stream_callback'):
                agent.set_stream_callback(stream_callback) 
                print(f"✅ [STREAM] 回调函数已设置到agent")
            
            # 在单独的线程中运行Agent，同时处理事件队列
            agent_result = {}
            agent_finished = threading.Event()
            agent_error = None
            
            def run_agent():
                nonlocal agent_result, agent_error
                try:
                    print(f"🎮 [STREAM] 开始运行Agent")
                    print(f"🎮 [STREAM] 会话ID: {session_id}")
                    print(f"🎮 [STREAM] 用户消息: {message[:50]}...")
                    
                    # 检查Agent是否有database_manager
                    if hasattr(agent, 'database_manager') and agent.database_manager:
                        print(f"🎮 [STREAM] Agent已配置数据库管理器")
                    else:
                        print(f"🎮 [STREAM] Agent未配置数据库管理器")
                    
                    if hasattr(agent, 'run_interactive_streaming'):
                        print(f"🎮 [STREAM] 使用实时流式方法")
                        agent.run_interactive_streaming(message, session_id)
                        agent_result = agent.get_final_result() or {}
                    else:
                        print(f"🎮 [STREAM] 使用普通方法")
                        agent_result = agent.run_interactive(message, session_id)
                        
                    print(f"🎮 [STREAM] Agent处理完成")
                    if agent_result:
                        print(f"🎮 [STREAM] 结果keys: {list(agent_result.keys())}")
                        print(f"🎮 [STREAM] session_id in result: {agent_result.get('session_id')}")
                    else:
                        print(f"🎮 [STREAM] 无结果返回")
                        
                except Exception as e:
                    print(f"❌ [STREAM] Agent执行错误: {e}")
                    import traceback
                    traceback.print_exc()
                    agent_error = e
                finally:
                    agent_finished.set()
            
            # 启动Agent线程
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            # 持续监听队列并发送事件
            events_sent = 0
            while not agent_finished.is_set() or not self.event_queue.empty():
                try:
                    # 尝试从队列获取事件（非阻塞）
                    try:
                        event = self.event_queue.get_nowait()
                        events_sent += 1
                        print(f"📤 [STREAM] 发送队列事件 #{events_sent}: {event[:50]}...")
                        yield event
                        await asyncio.sleep(0.001)  # 很短的延迟确保顺序
                    except:
                        # 队列为空，短暂等待
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"⚠️ [STREAM] 队列处理错误: {e}")
                    break
            
            # 等待Agent线程完成
            agent_thread.join(timeout=5.0)
            
            # 检查Agent错误
            if agent_error:
                raise agent_error
            
            print(f"✅ [AGENT] 处理完成，结果keys: {list(agent_result.keys()) if agent_result else 'None'}")
            print(f"📊 [STREAM] 总共发送了 {events_sent} 个队列事件")
            
            # 确保有结果
            if not agent_result:
                agent_result = {
                    "final_answer": "处理完成，但没有具体结果返回。",
                    "human_question": None,  # 🎯 添加这个字段
                    "is_interactive_pause": False,
                    "draft_contents": {},
                    "final_agenda": ""
                }
            
            # 🎯 新增：调试日志，查看实际的 agent_result 内容
            print(f"🔍 [DEBUG] agent_result keys: {list(agent_result.keys()) if agent_result else 'None'}")
            if agent_result.get("is_interactive_pause"):
                print(f"🔍 [DEBUG] human_question: {agent_result.get('human_question', 'None')}")
                print(f"🔍 [DEBUG] final_answer: {agent_result.get('final_answer', 'None')}")
            
            # 🎯 关键修复：添加缺失的 final_msg 定义
            # 发送最终响应
            if agent_result.get("is_interactive_pause"):
                # 获取真正的human_question而不是默认值
                final_content = agent_result.get("human_question") or agent_result.get("final_answer")
                
                # 如果还是没有内容，才使用默认值，但不要是"等待用户输入..."
                if not final_content or final_content.strip() == "":
                    final_content = "请告诉我您的想法，我们可以继续讨论。"
                
                final_msg = json.dumps({
                    'type': 'interactive_pause',
                    'content': final_content,
                    'timestamp': time.time(),
                    'metadata': {
                        'session_id': session_id,
                        'agenda': agent_result.get("final_agenda", ""),
                        'draft_contents': agent_result.get("draft_contents", {})
                    }
                }, ensure_ascii=False)
            else:
                final_msg = json.dumps({
                    'type': 'final',
                    'content': agent_result.get("final_answer", "处理完成"),
                    'timestamp': time.time(),
                    'metadata': {
                        'session_id': session_id,
                        'agenda': agent_result.get("final_agenda", ""),
                        'draft_contents': agent_result.get("draft_contents", {})
                    }
                }, ensure_ascii=False)
            
            yield f"data: {final_msg}\n\n"
            yield "data: [DONE]\n\n"
            
            self.logger.info(f"🏁 【stream headler】最终消息{final_msg}；；Stream completed, session: {session_id}, total events: {events_sent + 2}")

            # print(f"🏁 [STREAM] Stream completed, total callback events: {self.event_counter}, total sent events: {events_sent + 2}")
            
        except Exception as e_stream:
            print(f"❌ [STREAM] Error: {e_stream}")
            print(traceback.format_exc())
            error_msg = json.dumps({
                'type': 'error',
                'content': f'流式处理错误: {str(e_stream)}',
                'timestamp': time.time()
            }, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"
    
    async def generate_stream_response_with_memory(
        self, 
        agent, 
        message: str, 
        session_id: str,
        user_id: str,
        database_manager = None
    ) -> AsyncGenerator[str, None]:
        """生成流式响应 - 支持记忆的版本"""
        try:
            # 🎯 关键修复：重置去重状态
            self.event_counter = 0
            self.sent_events = set()  # 清空去重记录
        
            # 清空队列
            while not self.event_queue.empty():
                try:
                    self.event_queue.get_nowait()
                except:
                    break
            
            # 发送连接确认
            connection_msg = json.dumps({
                'type': 'connection', 
                'content': '连接已建立，正在加载会话历史...', 
                'timestamp': time.time(),
                'metadata': {'session_id': session_id, 'user_id': user_id}
            }, ensure_ascii=False)
            yield f"data: {connection_msg}\n\n"
            await asyncio.sleep(0.01)
            
            # 设置流式回调
            stream_callback = self.create_stream_callback()
            if hasattr(agent, 'set_stream_callback'):
                agent.set_stream_callback(stream_callback)
            
            # 在单独线程中运行Agent
            agent_result = {}
            agent_finished = threading.Event()
            agent_error = None
            
            def run_agent():
                nonlocal agent_result, agent_error
                try:
                    if hasattr(agent, 'run_interactive_streaming'):
                        agent.run_interactive_streaming(message, session_id)
                        agent_result = agent.get_final_result() or {}
                    else:
                        agent_result = agent.run_interactive(message, session_id)
                except Exception as e:
                    agent_error = e
                finally:
                    agent_finished.set()
            
            # 启动Agent线程
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            # 持续监听队列并发送事件
            events_sent = 0
            while not agent_finished.is_set() or not self.event_queue.empty():
                try:
                    try:
                        event = self.event_queue.get_nowait()
                        events_sent += 1
                        yield event
                        await asyncio.sleep(0.001)
                    except:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"⚠️ [STREAM] 队列处理错误: {e}")
                    break
            
            # 等待Agent完成
            agent_thread.join(timeout=5.0)
            
            if agent_error:
                raise agent_error
            
            # 确保有结果
            if not agent_result:
                agent_result = {
                    "final_answer": "处理完成，但没有具体结果返回。",
                    "human_question": None,  # 🎯 添加这个字段
                    "is_interactive_pause": False,
                    "draft_contents": {},
                    "final_agenda": "",
                    "session_id": session_id
                }
            
            # 🎯 新增：调试日志，查看实际的 agent_result 内容
            print(f"🔍 [DEBUG] agent_result keys: {list(agent_result.keys()) if agent_result else 'None'}")
            if agent_result.get("is_interactive_pause"):
                print(f"🔍 [DEBUG] human_question: {agent_result.get('human_question', 'None')}")
                print(f"🔍 [DEBUG] final_answer: {agent_result.get('final_answer', 'None')}")
            
            # 🎯 关键修复：确保议程信息通过现有事件传递
            # 🎯 在现有的最终消息构建前添加详细检查
            print(f"🔍 [后端检查点A] agent_result 所有keys: {list(agent_result.keys()) if agent_result else 'None'}")
            
            # 检查所有可能包含议程的字段
            agenda_fields_to_check = ['updated_agenda_doc', 'agenda_doc', 'final_agenda']
            agenda_found = None
            agenda_source_field = None
            
            for field in agenda_fields_to_check:
                value = agent_result.get(field)
                if value:
                    agenda_found = value
                    agenda_source_field = field
                    print(f"🔍 [后端检查点B] 在字段 {field} 中找到议程: {value[:100]}...")
                    break
                else:
                    print(f"🔍 [后端检查点C] 字段 {field} 为空或不存在")
            
            if not agenda_found:
                print(f"🔍 [后端检查点D] 所有议程字段都为空")
                # 尝试从 agent_core.current_state 中获取
                if hasattr(agent, 'agent_core') and hasattr(agent.agent_core, 'current_state'):
                    current_state = getattr(agent.agent_core, 'current_state', {})
                    for field in agenda_fields_to_check:
                        value = current_state.get(field)
                        if value:
                            agenda_found = value
                            agenda_source_field = f"current_state.{field}"
                            print(f"🔍 [后端检查点E] 从 current_state.{field} 中找到议程: {value[:100]}...")
                            break
            
            if agent_result.get("is_interactive_pause"):
                final_content = agent_result.get("human_question") or agent_result.get("final_answer")
                
                if not final_content or final_content.strip() == "":
                    final_content = "请告诉我您的想法，我们可以继续讨论。"
                
                print(f"🔍 [后端检查点F] 构建 interactive_pause，议程来源字段: {agenda_source_field}")
                
                final_msg = json.dumps({
                    'type': 'interactive_pause',
                    'content': final_content,
                    'timestamp': time.time(),
                    'metadata': {
                        'session_id': session_id,
                        'agenda': agent_result.get("final_agenda", ""),
                        'agenda_doc': agenda_found or "",  # 🎯 使用找到的议程
                        'updated_agenda_doc': agent_result.get("updated_agenda_doc", ""),
                        'final_agenda': agent_result.get("final_agenda", ""),
                        'agenda_source_field': agenda_source_field,  # 🎯 调试信息：议程来源
                        'draft_contents': agent_result.get("draft_contents", {})
                    }
                }, ensure_ascii=False)
                
                print(f"🔍 [后端检查点G] final_msg metadata keys: {list(json.loads(final_msg)['metadata'].keys())}")
                print(f"🔍 [后端检查点H] agenda_doc 长度: {len(agenda_found or '')}")
            else:
                print(f"🔍 [后端检查点I] 构建 final，议程来源字段: {agenda_source_field}")
                
                final_msg = json.dumps({
                    'type': 'final',
                    'content': agent_result.get("final_answer", "处理完成"),
                    'timestamp': time.time(),
                    'metadata': {
                        'session_id': session_id,
                        'agenda': agent_result.get("final_agenda", ""),
                        'agenda_doc': agenda_found or "",  # 🎯 使用找到的议程
                        'updated_agenda_doc': agent_result.get("updated_agenda_doc", ""),
                        'final_agenda': agent_result.get("final_agenda", ""),
                        'agenda_source_field': agenda_source_field,  # 🎯 调试信息：议程来源
                        'draft_contents': agent_result.get("draft_contents", {})
                    }
                }, ensure_ascii=False)
                
                print(f"🔍 [后端检查点J] final_msg metadata keys: {list(json.loads(final_msg)['metadata'].keys())}")
                print(f"🔍 [后端检查点K] agenda_doc 长度: {len(agenda_found or '')}")
            
            yield f"data: {final_msg}\n\n"
            yield "data: [DONE]\n\n"
            
            print(f"🏁 [STREAM] 记忆版流式处理完成, 会话: {session_id}, 事件数: {events_sent}")
            
        except Exception as e:
            print(f"❌ [STREAM] 记忆版流式处理错误: {e}")
            error_msg = json.dumps({
                'type': 'error',
                'content': f'流式处理错误: {str(e)}',
                'timestamp': time.time(),
                'metadata': {'session_id': session_id}
            }, ensure_ascii=False)
            yield f"data: {error_msg}\n\n"
            yield "data: [DONE]\n\n"

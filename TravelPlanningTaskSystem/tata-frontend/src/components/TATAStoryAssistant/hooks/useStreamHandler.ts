import { useCallback, useRef } from 'react';
import { StreamChunk, Message, ThinkingStep, ToolCall, AgendaSummary } from '../types';

export const useStreamHandler = ({
  setMessages,
  setCurrentThinkingSteps,
  setCurrentToolCalls,
  setCurrentAgenda,
  setIsProcessing,
  setDebugInfo,
  currentThinkingSteps,
  currentToolCalls,
  messageInputRef,
  chatEndRef
}: any) => {
  
  // 🎯 新增：跟踪已处理的事件
  const processedEvents = useRef(new Set<string>());
  // 🎯 新增：为每个消息单独跟踪工具调用
  const messageToolCalls = useRef<Map<string, ToolCall[]>>(new Map());
  
  const handleStreamChunk = useCallback((chunk: StreamChunk, aiMessageId: string) => {
    // 🎯 关键修复：创建事件唯一标识符
    const eventId = `${chunk.type}_${chunk.timestamp}_${chunk.content.slice(0, 50)}`;
    
    // 检查是否已处理过相同事件
    if (processedEvents.current.has(eventId)) {
      console.log(`⚠️ 跳过重复事件: ${chunk.type}`);
      return;
    }
    
    // 标记事件已处理
    processedEvents.current.add(eventId);
    
    console.log(`📦 ${chunk.type}: ${chunk.content.slice(0, 50)}...`);
    setDebugInfo((prev: string[]) => [...prev, `📦 ${chunk.type}: ${chunk.content.slice(0, 50)}...`]);
    
    switch (chunk.type) {
      case 'connection':
        console.log('🔗 连接确认:', chunk.content);
        setDebugInfo((prev: string[]) => [...prev, `🔗 连接确认: ${chunk.content}`]);
        break;
        
      case 'start':
        console.log('🚀 开始处理:', chunk.content);
        setDebugInfo((prev: string[]) => [...prev, `🚀 开始处理: ${chunk.content}`]);
        break;
        
      case 'thinking':
        // 保持现有的思考过滤逻辑
        const isImportantThinking = (
          (chunk.content.includes('决定调用') || 
          chunk.content.includes('决定使用') || 
          chunk.content.includes('选择工具') ||
          chunk.content.includes('执行工具')) &&
          chunk.content.length > 15 &&
          !chunk.content.includes('正在初始化') &&
          !chunk.content.includes('继续分析') &&
          !chunk.content.includes('让我思考') &&
          !chunk.content.includes('现在我来')
        );
        
        if (isImportantThinking) {
          // 现有的思考处理逻辑保持不变
          let simplifiedContent = chunk.content;
          
          if (chunk.content.includes('决定调用') || chunk.content.includes('决定使用')) {
            const match = chunk.content.match(/决定(调用|使用)(.{1,20})/);
            if (match) {
              simplifiedContent = `${match[1]}${match[2]}`;
            }
          } else if (chunk.content.includes('工具')) {
            const match = chunk.content.match(/(选择|执行).*?工具(.{1,15})/);
            if (match) {
              simplifiedContent = `${match[1]}工具${match[2]}`;
            }
          } else {
            return;
          }
          
          simplifiedContent = simplifiedContent
            .replace(/工具来/, '')
            .replace(/功能/, '')
            .replace(/进行/, '')
            .slice(0, 25);
          
          if (chunk.content.length > 25) {
            simplifiedContent += '...';
          }
          
          const newThinkingStep: ThinkingStep = {
            content: simplifiedContent,
            type: chunk.type,
            timestamp: chunk.timestamp,
            step_name: '工具选择'
          };
          
          setCurrentThinkingSteps((prevSteps: ThinkingStep[]) => {
            const updatedSteps = [...prevSteps, newThinkingStep];
            
            setMessages((prevMessages: Message[]) => prevMessages.map(msg => 
              msg.id === aiMessageId 
                ? { 
                    ...msg, 
                    thinking_steps: updatedSteps,
                    content: msg.tool_calls && msg.tool_calls.length > 0 
                      ? `准备工具调用... (${msg.tool_calls.length}个工具)`
                      : `思考中... (${updatedSteps.length}步)`,
                    is_streaming: true 
                  }
                : msg
            ));
            return updatedSteps;
          });
          
          setDebugInfo((prev: string[]) => [...prev, `🧠 工具选择: ${simplifiedContent}`]);
        }
        break;

    case 'assistant_message':
      const messageType = chunk.metadata?.message_type || 'general';
      
      // 跳过思考类型的消息
      if (messageType === 'tool_summary') {
        setDebugInfo((prev: string[]) => [...prev, `🔧 工具摘要已跳过: ${chunk.content.slice(0, 30)}...`]);
        return;
      }
      
      // 所有assistant_message都显示在思考卡片中
      let simplifiedContent = chunk.content;
      
      // 根据内容类型进行不同的精简处理
      if (chunk.content.includes('决定执行: call_tool')) {
        // 工具调用决策
        const toolMatch = chunk.content.match(/工具: ([^)]+)/);
        simplifiedContent = toolMatch ? `调用${toolMatch[1]}工具` : '调用工具';
      } else if (chunk.content.includes('工具') && chunk.content.includes('执行完成')) {
        // 工具执行完成
        const toolMatch = chunk.content.match(/工具 ([^\s]+) 执行完成/);
        simplifiedContent = toolMatch ? `${toolMatch[1]}执行完成` : '工具执行完成';
      } else {
        // 其他助手消息
        simplifiedContent = chunk.content
          .replace(/用户希望.*?为了帮助用户/g, '分析需求')
          .replace(/我决定执行: /g, '')
          .replace(/现在我将/g, '')
          .replace(/接下来/g, '')
          .slice(0, 40);
        
        if (chunk.content.length > 40) {
          simplifiedContent += '...';
        }
      }
      
      const assistantStep: ThinkingStep = {
        content: `💭 ${simplifiedContent}`,
        type: 'assistant_message',
        timestamp: chunk.timestamp,
        step_name: chunk.content.includes('决定执行') ? '工具调用' : 
                  chunk.content.includes('执行完成') ? '执行完成' : '分析'
      };
      
      setCurrentThinkingSteps((prevSteps: ThinkingStep[]) => {
        const updatedSteps = [...prevSteps, assistantStep];
        
        setMessages((prevMessages: Message[]) => prevMessages.map(msg => 
          msg.id === aiMessageId 
            ? { 
                ...msg, 
                thinking_steps: updatedSteps,
                is_streaming: true 
              }
            : msg
        ));
        return updatedSteps;
      });
      
      setDebugInfo((prev: string[]) => [...prev, `🤖 助手: ${simplifiedContent}`]);
      break;


      case 'tool_call':
        const newToolCall: ToolCall = {
          id: chunk.metadata?.call_id || `${Date.now()}`,
          tool_name: chunk.metadata?.tool_name || '',
          tool_display_name: chunk.metadata?.tool_display_name || '工具调用',
          params: {},
          status: chunk.metadata?.status || 'calling',
          call_time: chunk.timestamp
        };
        
        // 🎯 关键修复：为当前消息单独管理工具调用
        const currentMessageTools = messageToolCalls.current.get(aiMessageId) || [];
        const updatedMessageTools = [...currentMessageTools, newToolCall];
        messageToolCalls.current.set(aiMessageId, updatedMessageTools);
        
        // 添加工具调用到思考步骤中
        const toolCallStep: ThinkingStep = {
          content: `🔧 ${newToolCall.tool_display_name}`,
          type: 'tool_call',
          timestamp: chunk.timestamp,
          step_name: '执行工具'
        };
        
        setCurrentThinkingSteps((prevSteps: ThinkingStep[]) => {
          const updatedSteps = [...prevSteps, toolCallStep];
          
          setMessages((prevMessages: Message[]) => prevMessages.map(msg => 
            msg.id === aiMessageId 
              ? { 
                  ...msg, 
                  thinking_steps: updatedSteps,
                  tool_calls: updatedMessageTools, // 🎯 使用当前消息的工具调用
                  is_streaming: true 
                }
              : msg
          ));
          return updatedSteps;
        });
        
        // 🎯 更新全局状态（仅用于当前处理显示）
        setCurrentToolCalls(updatedMessageTools);
        
        setDebugInfo((prev: string[]) => [...prev, `🔧 工具调用: ${newToolCall.tool_display_name}`]);
        break;

      case 'tool_result':
        if (chunk.metadata?.call_id && chunk.content) {
          const callId = chunk.metadata.call_id;
          const result = chunk.content;
          const toolName = chunk.metadata?.tool_name || '';
          const toolDisplayName = chunk.metadata?.tool_display_name || '工具结果';
          
          // 🎯 修复：更新当前消息的工具调用状态
          const messageTools = messageToolCalls.current.get(aiMessageId) || [];
          const updatedTools = messageTools.map(call => 
            call.id === callId 
              ? { 
                  ...call, 
                  result: result,
                  status: 'completed' as const,
                  result_time: chunk.timestamp 
                }
              : call
          );
          messageToolCalls.current.set(aiMessageId, updatedTools);
          
          // 更新流式消息状态
          setMessages((prevMessages: Message[]) => prevMessages.map(msg => 
            msg.id === aiMessageId 
              ? { 
                  ...msg, 
                  tool_calls: updatedTools, // 🎯 使用当前消息的工具调用
                  content: `正在处理工具结果... (${updatedTools.filter(c => c.status === 'completed').length}/${updatedTools.length} 完成)`,
                  is_streaming: true 
                }
              : msg
          ));
          
          // 🎯 更新全局状态
          setCurrentToolCalls(updatedTools);
          
          // 🎯 第二步：立即创建独立的工具结果消息
          const toolResultMessage: Message = {
            id: `tool-result-${callId}-${Date.now()}`,
            type: 'tool_result',
            content: `## 🔧 ${toolDisplayName}执行结果\n\n${result}`,
            timestamp: chunk.timestamp || Date.now(),
            isMarkdown: true,
            thinking_steps: [],
            tool_calls: [{
              id: callId,
              tool_name: toolName,
              tool_display_name: toolDisplayName,
              params: {},
              status: 'completed',
              call_time: chunk.timestamp,
              result: result,
              result_time: chunk.timestamp
            }],
            is_streaming: false
          };
          
          // 立即添加工具结果消息
          setMessages((prevMessages: Message[]) => [...prevMessages, toolResultMessage]);
          
          setDebugInfo((prev: string[]) => [...prev, `✅ 工具结果立即显示: ${toolDisplayName} (${result.length}字符)`]);
          
          // 自动滚动
          setTimeout(() => {
            chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }, 150);
        }
        break;


      case 'interactive_pause':
      case 'final':
        console.log('💬 收到AI回复:', chunk.content);
        
        // 🎯 添加详细检查点
        console.log('🔍 [前端检查点1] 完整chunk对象:', JSON.stringify(chunk, null, 2));
        console.log('🔍 [前端检查点2] chunk.metadata:', chunk.metadata);
        console.log('🔍 [前端检查点3] 所有可能的议程字段检查:');
        console.log('  - agenda_doc:', chunk.metadata?.agenda_doc);
        console.log('  - updated_agenda_doc:', chunk.metadata?.updated_agenda_doc);
        console.log('  - agenda:', chunk.metadata?.agenda);
        console.log('  - final_agenda:', chunk.metadata?.final_agenda);
        
        // 🎯 尝试从所有可能的字段中获取议程信息
        const agendaSource = chunk.metadata?.agenda_doc || 
                           chunk.metadata?.updated_agenda_doc || 
                           chunk.metadata?.agenda || 
                           chunk.metadata?.final_agenda;
        
        console.log('🔍 [前端检查点4] 最终选择的议程来源:', agendaSource ? 'Found' : 'Not Found');
        
        if (agendaSource) {
          console.log('🔍 [前端检查点5] 议程内容预览:', agendaSource.slice(0, 200));
          try {
            const agendaSummary = parseAgendaText(agendaSource);
            setCurrentAgenda(agendaSummary);
            setDebugInfo((prev: string[]) => [...prev, `📋 议程已更新: ${agendaSummary.total_tasks || 0} 个任务，完成率 ${Math.round(agendaSummary.completion_rate)}%`]);
            console.log('📋 [前端检查点6] 议程解析成功:', agendaSummary);
          } catch (parseError) {
            console.error('🔍 [前端检查点7] 议程解析失败:', parseError);
            setDebugInfo((prev: string[]) => [...prev, `❌ 议程解析失败: ${parseError instanceof Error ? parseError.message : String(parseError)}`]);
          }
        } else {
          console.warn('⚠️ [前端检查点8] 所有议程字段都为空');
          setDebugInfo((prev: string[]) => [...prev, `⚠️ 未收到议程信息 - metadata keys: ${Object.keys(chunk.metadata || {}).join(', ')}`]);
        }
        
        // 正常的消息处理逻辑保持不变...
        setMessages((prevMessages: Message[]) => {
          // 现有的消息处理逻辑
          const pauseMessageId = `pause_${aiMessageId}_${chunk.timestamp}`;
          const existingPause = prevMessages.find(msg => msg.id === pauseMessageId);
          if (existingPause) {
            console.log('⚠️ 跳过重复的暂停消息');
            return prevMessages;
          }
          
          // 继续现有的消息创建逻辑...
          const updatedMessages = prevMessages.map((msg: Message) => {
            if (msg.id === aiMessageId) {
              return { 
                ...msg, 
                thinking_steps: msg.thinking_steps || currentThinkingSteps,
                tool_calls: msg.tool_calls || currentToolCalls,
                is_streaming: false 
              };
            }
            return msg;
          });
          
          const pauseMessage: Message = {
            id: pauseMessageId,
            type: 'ai',
            content: `## 💭AI\n\n${chunk.content}`,
            timestamp: chunk.timestamp || Date.now(),
            thinking_steps: [],
            tool_calls: [],
            is_streaming: false,
            isMarkdown: true
          };
          
          return [...updatedMessages, pauseMessage];
        });
        
        setIsProcessing(false);
        setTimeout(() => {
          chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 150);
        break;
        
      case 'draft_update':
        // 🎯 移除草稿处理，只保留调试信息
        if (chunk.metadata?.draft_id && chunk.content) {
          const draftId = chunk.metadata.draft_id;
          const content = chunk.content;
          
          setDebugInfo((prev: string[]) => [...prev, `📝 后端草稿更新: ${draftId} (${content.length} 字符)`]);
          console.log(`📝 后端生成草稿 ${draftId}:`, content);
        } else {
          setDebugInfo((prev: string[]) => [...prev, `⚠️ 草稿更新缺少必要信息`]);
        }
        break;

      case 'agenda_update':
        console.log('📋 收到议程更新事件:', chunk);
        console.log('📋 议程内容:', chunk.content);
        console.log('📋 元数据:', chunk.metadata);
        
        if (chunk.metadata?.agenda_summary) {
          const agendaSummary: AgendaSummary = chunk.metadata.agenda_summary;
          setCurrentAgenda(agendaSummary);
          setDebugInfo((prev: string[]) => [...prev, `📋 议程更新: ${agendaSummary.total_tasks} 个任务，完成率 ${Math.round(agendaSummary.completion_rate)}%`]);
          console.log('📋 完整议程信息:', agendaSummary);
        } else {
          console.warn('⚠️ 议程更新事件缺少 agenda_summary');
        }
        break;
        
      case 'final':
        // 现有的final处理逻辑保持不变，但要确保不重复处理interactive_pause
        if (chunk.metadata?.message_type === 'interactive_pause') {
          // 如果是interactive_pause，跳过final处理，因为已经在上面处理了
          return;
        }
        
        console.log('🎯 收到最终回复:', chunk.content);
        setDebugInfo((prev: string[]) => [...prev, `🎯 最终回复完整内容: ${chunk.content}`]);
        
        setMessages((prevMessages: Message[]) => {
          const updatedMessages = prevMessages.map((msg: Message) => {
            if (msg.id === aiMessageId) {
              // 🎯 获取当前消息的工具调用记录
              const finalToolCalls = messageToolCalls.current.get(aiMessageId) || [];
              
              return { 
                ...msg, 
                thinking_steps: msg.thinking_steps || currentThinkingSteps,
                tool_calls: finalToolCalls, // 🎯 使用当前消息的工具调用
                is_streaming: false 
              };
            }
            return msg;
          });
          
          // 🎯 关键修复：移除工具结果重复显示，只显示AI的最终回复
          const formattedAssistantContent = chunk.content
            .replace(/\n/g, '\n\n')
            .replace(/\*\*(.*?)\*\*/g, '**$1**');
           
          const finalReplyMessage: Message = {
            id: `final_reply_${Date.now()}`,
            type: 'ai',
            content: `## ✨ 助手回复\n\n${formattedAssistantContent}`,  // 只显示AI回复，不包含工具结果
            timestamp: chunk.timestamp || Date.now(),
            thinking_steps: [],
            tool_calls: [],
            is_streaming: false,
            isMarkdown: true
          };
          
          return [...updatedMessages, finalReplyMessage];
        });
        
        // 🎯 重要：处理完成后清理状态
        setCurrentThinkingSteps([]);
        setCurrentToolCalls([]);
        
        setIsProcessing(false);
        
        setTimeout(() => {
          chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 150);
        break;
        
      case 'error':
        console.error('❌ 收到错误:', chunk.content);
        setMessages((prev: Message[]) => prev.map((msg: Message) => 
          msg.id === aiMessageId 
            ? { 
                ...msg, 
                content: `## ❌ 错误\n\n**${chunk.content}**`,
                thinking_steps: currentThinkingSteps,
                tool_calls: currentToolCalls,
                is_streaming: false,
                type: 'error',
                isMarkdown: true
              }
            : msg
        ));
        setIsProcessing(false);
        break;
        
      default:
        console.log(`未处理的数据块类型: ${chunk.type}`);
        setDebugInfo((prev: string[]) => [...prev, `❓ 未知类型: ${chunk.type}`]);
        break;
    }
  }, [currentThinkingSteps, currentToolCalls, setMessages, setCurrentThinkingSteps, setCurrentToolCalls, setCurrentAgenda, setIsProcessing, setDebugInfo, messageInputRef, chatEndRef]);

  const handleStreamResponse = useCallback(async (response: Response, aiMessageId: string) => {
    let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
    
    try {
      // 🎯 关键修复：在每次新的流处理开始时清理所有状态
      processedEvents.current.clear();
      messageToolCalls.current.delete(aiMessageId);
      
      // 🎯 新增：清理全局状态，避免累积
      setCurrentThinkingSteps([]);
      setCurrentToolCalls([]);
      
      reader = response.body?.getReader() || null;
      if (!reader) {
        throw new Error('无法获取响应流读取器');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }

            try {
              const chunk = JSON.parse(data);
              handleStreamChunk(chunk, aiMessageId);
            } catch (e) {
              console.error('解析流式数据失败:', e);
              console.error('原始数据:', data);
            }
          }
        }
      }
    } catch (error) {
      console.error('流式响应处理失败:', error);
    } finally {
      if (reader) {
        reader.releaseLock();
      }
      setIsProcessing(false);
    }
  }, [handleStreamChunk, setMessages, setCurrentThinkingSteps, setCurrentToolCalls, setIsProcessing, setDebugInfo]);

  return {
    handleStreamResponse
  };
};

// 修复 parseAgendaText 函数，确保返回完整的 AgendaSummary 类型
function parseAgendaText(agendaText: string): AgendaSummary {
  const tasks = {
    pending: [] as string[],
    completed: [] as Array<{task: string, result?: string}>,
    in_progress: [] as Array<{task: string, reason?: string}>,
    overall_goal: null as string | null,
    overall_goal_status: 'pending' as 'pending' | 'completed' | 'in_progress' // 🎯 新增：跟踪目标状态
  };
  
  if (!agendaText) {
    return { 
      ...tasks, 
      total_tasks: 0, 
      completion_rate: 0,
      pending_count: 0,
      completed_count: 0,
      in_progress_count: 0,
      goals_count: 0,
      tasks_by_status: {
        goals: [],
        pending: [],
        completed: [],
        in_progress: []
      }
    };
  }
  
  const lines = agendaText.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || !trimmed.startsWith('-')) continue;
    
    if (trimmed.includes('- [ ]')) {
      const task = trimmed.replace('- [ ]', '').trim();
      if (task.includes('@overall_goal')) {
        tasks.overall_goal = task.replace('@overall_goal', '').trim();
        tasks.overall_goal_status = 'pending'; // 🎯 设置状态
      } else {
        tasks.pending.push(task);
      }
    } else if (trimmed.includes('- [x]')) {
      const task = trimmed.replace('- [x]', '').trim();
      const resultMatch = task.match(/\(结果: (.+?)\)/);
      const taskName = task.replace(/\s*\(结果:.*?\)/, '');
      
      // 🎯 关键修复：检查已完成的 @overall_goal
      if (taskName.includes('@overall_goal')) {
        tasks.overall_goal = taskName.replace('@overall_goal', '').trim();
        tasks.overall_goal_status = 'completed';
      } else {
        tasks.completed.push({
          task: taskName,
          result: resultMatch ? resultMatch[1] : undefined
        });
      }
    } else if (trimmed.includes('- [-]')) {
      const task = trimmed.replace('- [-]', '').trim();
      const reasonMatch = task.match(/\(原因: (.+?)\)/);
      const taskName = task.replace(/\s*\(原因:.*?\)/, '');
      
      // 🎯 关键修复：检查进行中的 @overall_goal
      if (taskName.includes('@overall_goal')) {
        tasks.overall_goal = taskName.replace('@overall_goal', '').trim();
        tasks.overall_goal_status = 'in_progress';
      } else {
        tasks.in_progress.push({
          task: taskName,
          reason: reasonMatch ? reasonMatch[1] : undefined
        });
      }
    }
  }
  
  const totalTasks = tasks.pending.length + tasks.completed.length + tasks.in_progress.length;
  const completionRate = totalTasks > 0 ? (tasks.completed.length / totalTasks) * 100 : 0;
  const goalsCount = tasks.overall_goal ? 1 : 0;
  
  // 🎯 修复：根据 overall_goal 的实际状态创建 goals 数组
  const goalTask = tasks.overall_goal ? {
    id: 'overall_goal',
    description: tasks.overall_goal,
    status: tasks.overall_goal_status as 'pending' | 'completed' | 'in_progress',
    result: tasks.overall_goal_status === 'completed' ? '目标已达成' : 
           tasks.overall_goal_status === 'in_progress' ? '目标进行中' : undefined
  } : null;
  
  return {
    ...tasks,
    total_tasks: totalTasks,
    completion_rate: completionRate,
    pending_count: tasks.pending.length,
    completed_count: tasks.completed.length,
    in_progress_count: tasks.in_progress.length,
    goals_count: goalsCount,
    tasks_by_status: {
      goals: goalTask ? [goalTask] : [],
      pending: tasks.pending.map((task, index) => ({
        id: `pending_${index}`,
        description: task,
        status: 'pending' as const
      })),
      completed: tasks.completed.map((task, index) => ({
        id: `completed_${index}`,
        description: task.task,
        status: 'completed' as const,
        result: task.result
      })),
      in_progress: tasks.in_progress.map((task, index) => ({
        id: `in_progress_${index}`,
        description: task.task,
        status: 'in_progress' as const,
        result: task.reason
      }))
    }
  };
}
import React from 'react';
import { Message, ThinkingStep, ToolCall } from '../types';
import { getStepIcon, getToolStatusIcon } from '../utils/messageUtils';
import { formatTime } from '../utils/formatUtils';
import ReactMarkdown from 'react-markdown';

interface MessageCardProps {
  message: Message;
}

export const MessageCard: React.FC<MessageCardProps> = ({ message }) => {
  // 检查内容是否为空
  const isEmptyContent = !message.content || message.content.trim() === '';
  
  // 检查是否有思考步骤但没有内容
  const hasThinkingOnly = message.thinking_steps && message.thinking_steps.length > 0 && isEmptyContent;
  
  // 检查是否有工具调用但没有内容
  const hasToolsOnly = message.tool_calls && message.tool_calls.length > 0 && isEmptyContent;

  // 🎯 修复：合并思考和工具调用的显示逻辑
  const renderProcessCard = () => {
    const hasThinking = message.thinking_steps && message.thinking_steps.length > 0;
    const hasTools = message.tool_calls && message.tool_calls.length > 0;
    
    // 如果既有思考又有工具调用，合并显示
    // if (hasThinking && hasTools) {
    //   return (
    //     <div className="message-card process-card">
    //       <div className="card-header">
    //         <span className="card-icon">⚙️</span>
    //         <span className="card-title">处理过程</span>
    //         <span className="card-badge">
    //           {message.thinking_steps!.length}步思考 · {message.tool_calls!.length}个工具
    //         </span>
    //       </div>
    //       <div className="card-content">
    //         {/* 先显示思考步骤 */}
    //         {message.thinking_steps!.map((step, index) => (
    //           <div key={`thinking-${index}`} className="thinking-step-inline">
    //             <span className="step-icon-inline">{getStepIcon(step.type)}</span>
    //             <div className="step-content-inline">
    //               <div className="step-title-inline">{step.step_name || '思考中'}</div>
    //               <div className="step-text-inline">{step.content}</div>
    //             </div>
    //           </div>
    //         ))}
            
    //         {/* 然后显示工具调用 */}
    //         {message.tool_calls!.map((tool, index) => (
    //           <div key={`tool-${index}`} className="tool-call-inline">
    //             <div className="tool-header-inline">
    //               <span className="tool-status">{getToolStatusIcon(tool.status)}</span>
    //               <span className="tool-name">{tool.tool_display_name}</span>
    //               <span className="tool-timing">
    //                 {tool.status === 'calling' ? '执行中...' : '已完成'}
    //               </span>
    //             </div>
    //             {tool.result && (
    //               <div className="tool-result-inline">
    //                 <span className="result-label">状态:</span>
    //                 <div className="result-summary">
    //                   {tool.status === 'completed' 
    //                     ? `✅ 执行成功 (${Math.ceil((tool.result as string).length / 10)}字符)` 
    //                     : tool.status === 'error' 
    //                     ? '❌ 执行失败' 
    //                     : '⏳ 处理中...'}
    //                 </div>
    //               </div>
    //             )}
    //           </div>
    //         ))}
    //       </div>
    //     </div>
    //   );
    // }
    
    // 如果只有思考步骤
    if (hasThinking) {
      return renderThinkingCard(message.thinking_steps!);
    }
    
    // 如果只有工具调用
    // if (hasTools) {
    //   return renderToolsCard(message.tool_calls!);
    // }
    
    return null;
  };

  const renderThinkingCard = (steps: ThinkingStep[]) => (
    <div className="message-card thinking-card">
      {/* <div className="card-header">
        <span className="card-icon">🤔</span>
        <span className="card-title">思考过程</span>
        <span className="card-badge">{steps.length}步</span>
      </div> */}
      {/* <div className="card-content">
        {steps.map((step, index) => (
          <div key={index} className="thinking-step-inline">
            <span className="step-icon-inline">{getStepIcon(step.type)}</span>
            <div className="step-content-inline">
              <div className="step-title-inline">{step.step_name || '思考中'}</div>
              <div className="step-text-inline">{step.content}</div>
            </div>
          </div>
        ))}
      </div> */}
    </div> 
  );

  // const renderToolsCard = (tools: ToolCall[]) => (
  //   <div className="message-card tools-card">
  //     <div className="card-header">
  //       <span className="card-icon">🔧</span>
  //       <span className="card-title">工具调用</span>
  //       <span className="card-badge">{tools.length}个</span>
  //     </div>
  //     <div className="card-content">
  //       {tools.map((tool, index) => (
  //         <div key={index} className="tool-call-inline">
  //           <div className="tool-header-inline">
  //             <span className="tool-status">{getToolStatusIcon(tool.status)}</span>
  //             <span className="tool-name">{tool.tool_display_name}</span>
  //             <span className="tool-timing">
  //               {tool.status === 'calling' ? '执行中...' : '已完成'}
  //             </span>
  //           </div>
  //           {tool.result && (
  //             <div className="tool-result-inline">
  //               <span className="result-label">状态:</span>
  //               <div className="result-summary">
  //                 {tool.status === 'completed' 
  //                   ? `✅ 执行成功 (${Math.ceil((tool.result as string).length / 10)}字符)` 
  //                   : tool.status === 'error' 
  //                   ? '❌ 执行失败' 
  //                   : '⏳ 处理中...'}
  //               </div>
  //             </div>
  //           )}
  //         </div>
  //       ))}
  //     </div>
  //   </div>
  // );

  // 生成兜底内容
  const getFallbackContent = () => {
    if (hasThinkingOnly) {
      return "💭 思考完成，正在整理回复...";
    }
    
    if (hasToolsOnly) {
      return "🔧 工具执行完成，正在处理结果...";
    }
    
    if (message.type === 'assistant' || message.type === 'ai') {
      return "🤖 收到您的消息！正在思考中...";
    }
    
    return "📝 消息处理中...";
  };

  return (
    <div className={`message ${message.type}`}>
      <div className="message-avatar">
        {message.type === 'user' ? '👤' : 
         message.type === 'ai' ? '🤖' : 
         message.type === 'assistant' ? '🤖' :
         message.type === 'ai_pause' ? '💬' :
         message.type === 'tool_result' ? '🔧' :
         message.type === 'error' ? '❌' :
         '⚠️'}
      </div>
      <div className="message-bubble">
        <div className="message-content">
          <div className="message-text">
            {/* 🎯 关键修复：根据消息类型选择渲染方式 */}
            {isEmptyContent ? (
              <div className="fallback-content">
                {getFallbackContent()}
              </div>
            ) : message.type === 'user' ? (
              // 🎯 用户消息：保持换行格式
              <div className="user-message-content">
                {message.content.split('\n').map((line, index, array) => (
                  <React.Fragment key={index}>
                    {line}
                    {index < array.length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
            ) : message.isMarkdown ? (
              // AI消息：使用Markdown渲染
              <ReactMarkdown
                className="prose prose-sm max-w-none"
                components={{
                  h2: (props: any) => <h2 className="text-lg font-bold mt-4 mb-2 text-blue-600" {...props} />,
                  h3: (props: any) => <h3 className="text-md font-semibold mt-3 mb-2 text-gray-700" {...props} />,
                  p: (props: any) => <p className="mb-2 leading-relaxed" {...props} />,
                  strong: (props: any) => <strong className="font-bold text-gray-900" {...props} />,
                  em: (props: any) => <strong className="font-bold text-gray-900" {...props} />,
                  hr: (props: any) => <hr className="my-4 border-gray-300" {...props} />,
                  ul: (props: any) => <ul className="list-disc ml-4 mb-2" {...props} />,
                  ol: ({ ordered, ...props }: any) => (
                    <ol className={`ml-4 mb-2 ${ordered !== false ? 'list-decimal' : 'list-none'}`} {...props} />
                  ),
                  li: (props: any) => <li className="mb-1" {...props} />,
                  img: (props: any) => {
                    const absoluteSrc = props.src.startsWith('/')
                      ? `http://localhost:8000${props.src}`
                      : props.src;

                    console.log('🖼️ [图片渲染] Attempting to load image with src:', absoluteSrc);

                    return (
                      <img
                        {...props}
                        src={absoluteSrc}
                        className="generated-image"
                        style={{
                          maxWidth: '100%',
                          height: 'auto',
                          borderRadius: '8px',
                          margin: '8px 0'
                        }}
                        onLoad={() => console.log('✅ Markdown图片加载成功:', absoluteSrc)}
                        onError={(e) => console.error('❌ Markdown图片加载失败:', absoluteSrc, e)}
                      />
                    );
                  },
                } as any}
              >
                {/* 预处理文本：处理换行符和星号转换 */}
                {message.content
                  // 🎯 新增：处理换行符 - 将字符串形式的换行符转换为实际换行符
                  .replace(/\\n\\n/g, '\n\n')  // 将字符串 \n\n 转换为实际换行
                  .replace(/\\n/g, '\n')       // 将字符串 \n 转换为实际换行
                  // 先保护已有的双星号，用临时标记替换
                  .replace(/\*\*([^*]+?)\*\*/g, '___BOLD_START___$1___BOLD_END___')
                  // 然后将剩余的单星号转换为双星号
                  .replace(/\*([^*]+?)\*/g, '**$1**')
                  // 最后恢复原来的双星号
                  .replace(/___BOLD_START___([^_]+?)___BOLD_END___/g, '**$1**')
                }
              </ReactMarkdown>
            ) : (
              // 其他消息：保持换行格式
              <div className="whitespace-pre-wrap">{message.content}</div>
            )}
            {message.is_streaming && (
              <span className="streaming-indicator">
                <span></span>
                <span></span>
                <span></span>
              </span>
            )}
          </div>
          
          {/* 🎯 修复：使用合并的处理过程卡片 */}
          {renderProcessCard()}
          
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};
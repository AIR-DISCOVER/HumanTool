export interface StreamChunk {
  type: 'connection' | 'start' | 'thinking' | 'tool_call' | 'tool_result' | 'draft_update' | 'agenda_update' | 'final' | 'interactive_pause' | 'error' | 'heartbeat' | 'assistant_message';
  content: string;
  timestamp: number;
  step_name?: string;
  metadata?: {
    call_id?: string;
    tool_name?: string;
    tool_display_name?: string;
    params?: any;
    status?: 'calling' | 'completed' | 'error';
    result?: string;
    draft_id?: string;
    updated_by?: string;
    agenda_summary?: AgendaSummary;
    agenda_text?: string;
    agenda_doc?: string;
    updated_agenda_doc?: string;  // 🎯 添加
    final_agenda?: string;        // 🎯 添加
    agenda?: string;
    agenda_source_field?: string; // 🎯 调试字段
    draft_contents?: Record<string, any>;
    message_type?: string;
    step?: string;
    full_agenda?: string;
    newly_completed_tasks?: string[];
    session_id?: string;
  };
}

export interface Message {
  id: string;
  type: "user" | "ai" | "ai_pause" | "assistant" | "error" | "tool_result";  // 🎯 添加 tool_result
  content: string;
  timestamp: number;
  thinking_steps?: ThinkingStep[];
  tool_calls?: ToolCall[];
  is_streaming?: boolean;
  isMarkdown?: boolean;
}

export interface ThinkingStep {
  content: string;
  type: string;
  timestamp: number;
  step_name?: string;
  metadata?: any;
}

export interface ToolCall {
  id: string;
  tool_name: string;
  tool_display_name: string;
  params: any;
  status: 'calling' | 'completed' | 'error';
  call_time: number;
  result?: any;
  result_time?: number;
}

export interface DraftContent {
  content: string;
  last_updated: number;
  updated_by?: string;
}

export interface AgendaTask {
  id?: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'goals';
  result?: string;
  subtasks?: SubTask[]; // 添加子任务支持
}

export interface SubTask {
  id?: string;
  name?: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  result?: string;
}

export interface AgendaSummary {
  total_tasks: number;
  pending_count: number;
  completed_count: number;
  in_progress_count: number;
  goals_count: number;
  completion_rate: number;
  tasks_by_status: {
    pending: AgendaTask[];
    completed: AgendaTask[];
    in_progress: AgendaTask[];
    goals: AgendaTask[];
  };
}

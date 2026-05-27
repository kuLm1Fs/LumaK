export type AgentStatus = "Idle" | "Thinking" | "Running Tool" | "Waiting User" | "Error";

export type ToolStatus = "running" | "success" | "failed";

export type TaskStatus = "pending" | "running" | "done" | "failed";

export type AgentTask = {
  id: string;
  title: string;
  status: TaskStatus;
};

export type RuntimeMetrics = {
  tokens?: string;
  cost?: string;
  latency?: string;
  git?: string;
};

export type UserMessageEvent = {
  type: "user_message";
  id: string;
  content: string;
  timestamp: number;
};

export type AssistantMessageEvent = {
  type: "assistant_message";
  id: string;
  content: string;
  timestamp: number;
};

export type ThinkingStartEvent = {
  type: "thinking_start";
  label?: string;
  timestamp: number;
};

export type ThinkingEndEvent = {
  type: "thinking_end";
  timestamp: number;
};

export type ToolCallStartEvent = {
  type: "tool_call_start";
  id: string;
  name: string;
  args: Record<string, unknown>;
  timestamp: number;
};

export type ToolCallEndEvent = {
  type: "tool_call_end";
  id: string;
  status: Exclude<ToolStatus, "running">;
  resultPreview: string;
  timestamp: number;
};

export type ErrorEvent = {
  type: "error";
  id: string;
  message: string;
  timestamp: number;
};

export type StatusUpdateEvent = {
  type: "status_update";
  status: AgentStatus;
  model?: string;
  currentStep?: string;
  tasks?: AgentTask[];
  metrics?: RuntimeMetrics;
  log?: string;
  timestamp: number;
};

export type AgentEvent =
  | UserMessageEvent
  | AssistantMessageEvent
  | ThinkingStartEvent
  | ThinkingEndEvent
  | ToolCallStartEvent
  | ToolCallEndEvent
  | ErrorEvent
  | StatusUpdateEvent;

export type RuntimeUnsubscribe = () => void;

export interface AgentRuntime {
  subscribe(listener: (event: AgentEvent) => void): RuntimeUnsubscribe;
  sendMessage(message: string): Promise<void>;
  dispose(): void;
}

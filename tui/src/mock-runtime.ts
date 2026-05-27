import type { AgentEvent, AgentRuntime, AgentTask, RuntimeUnsubscribe } from "./events.js";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class MockAgentRuntime implements AgentRuntime {
  private listeners = new Set<(event: AgentEvent) => void>();
  private runId = 0;
  private disposed = false;

  subscribe(listener: (event: AgentEvent) => void): RuntimeUnsubscribe {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  dispose(): void {
    this.disposed = true;
    this.listeners.clear();
  }

  async sendMessage(message: string): Promise<void> {
    const runId = ++this.runId;
    const startedAt = Date.now();
    const toolId = `tool-${runId}`;
    const tasks: AgentTask[] = [
      { id: "understand", title: "Understand request", status: "running" },
      { id: "inspect", title: "Inspect workspace", status: "pending" },
      { id: "answer", title: "Compose response", status: "pending" },
    ];

    this.emit({ type: "user_message", id: `user-${runId}`, content: message, timestamp: Date.now() });
    this.emit({
      type: "status_update",
      status: "Thinking",
      currentStep: "Reading prompt and planning next action",
      tasks,
      metrics: placeholderMetrics(),
      log: "Queued user prompt",
      timestamp: Date.now(),
    });
    this.emit({ type: "thinking_start", label: "Planning", timestamp: Date.now() });

    await this.wait(runId, 550);
    tasks[0] = { ...tasks[0], status: "done" };
    tasks[1] = { ...tasks[1], status: "running" };
    this.emit({
      type: "status_update",
      status: "Running Tool",
      currentStep: "Calling workspace_search",
      tasks,
      metrics: placeholderMetrics(),
      log: "Starting mock tool call workspace_search",
      timestamp: Date.now(),
    });
    this.emit({ type: "thinking_end", timestamp: Date.now() });
    this.emit({
      type: "tool_call_start",
      id: toolId,
      name: "workspace_search",
      args: {
        query: summarizePrompt(message),
        include: ["src", "tests", "docs"],
        limit: 5,
      },
      timestamp: Date.now(),
    });

    await this.wait(runId, 850);
    this.emit({
      type: "tool_call_end",
      id: toolId,
      status: "success",
      resultPreview: "Found matching TUI entrypoint, event helpers, and existing tests. No real files were changed by the mock tool.",
      timestamp: Date.now(),
    });

    tasks[1] = { ...tasks[1], status: "done" };
    tasks[2] = { ...tasks[2], status: "running" };
    this.emit({
      type: "status_update",
      status: "Thinking",
      currentStep: "Synthesizing final answer",
      tasks,
      metrics: { tokens: "~1.4k", cost: "--", latency: `${((Date.now() - startedAt) / 1000).toFixed(1)}s`, git: "--" },
      log: "Tool returned successfully",
      timestamp: Date.now(),
    });
    this.emit({ type: "thinking_start", label: "Writing response", timestamp: Date.now() });

    await this.wait(runId, 500);
    tasks[2] = { ...tasks[2], status: "done" };
    this.emit({ type: "thinking_end", timestamp: Date.now() });
    this.emit({
      type: "assistant_message",
      id: `assistant-${runId}`,
      content:
        `Mock agent response for: "${message}".\n\n` +
        "This demonstrates the full loop: user input, thinking state, tool call block, tool result preview, task progress, and recovery to input mode. TODO: replace MockAgentRuntime with the real LLM/tool runtime adapter.",
      timestamp: Date.now(),
    });
    this.emit({
      type: "status_update",
      status: "Waiting User",
      currentStep: "Waiting for the next prompt",
      tasks,
      metrics: { tokens: "~1.8k", cost: "--", latency: `${((Date.now() - startedAt) / 1000).toFixed(1)}s`, git: "--" },
      log: "Run complete",
      timestamp: Date.now(),
    });
  }

  private emit(event: AgentEvent): void {
    if (this.disposed) {
      return;
    }
    for (const listener of this.listeners) {
      listener(event);
    }
  }

  private async wait(runId: number, ms: number): Promise<void> {
    await sleep(ms);
    if (this.disposed || runId !== this.runId) {
      throw new Error("mock run interrupted");
    }
  }
}

function summarizePrompt(message: string): string {
  const normalized = message.replace(/\s+/g, " ").trim();
  return normalized.length > 72 ? `${normalized.slice(0, 69)}...` : normalized;
}

function placeholderMetrics() {
  return {
    tokens: "--",
    cost: "--",
    latency: "--",
    git: "--",
  };
}

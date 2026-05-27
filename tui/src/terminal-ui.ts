import { emitKeypressEvents } from "node:readline";
import stringWidth from "string-width";

import { chooseLayout, formatArgsSummary, padRight, truncateText, wrapText } from "./app-utils.js";
import type { AgentEvent, AgentRuntime, AgentStatus, AgentTask, RuntimeMetrics, ToolStatus } from "./events.js";

type ChatLine =
  | { kind: "message"; role: "you" | "lumaK" | "system"; content: string }
  | { kind: "tool"; id: string; name: string; args: Record<string, unknown>; status: ToolStatus; resultPreview?: string }
  | { kind: "error"; content: string };

type TerminalUiOptions = {
  projectName: string;
  model: string;
  workspace: string;
};

const CLEAR = "\x1b[2J\x1b[H";
const ALT_SCREEN = "\x1b[?1049h";
const MAIN_SCREEN = "\x1b[?1049l";
const HIDE_CURSOR = "\x1b[?25l";
const SHOW_CURSOR = "\x1b[?25h";
const DISABLE_WRAP = "\x1b[?7l";
const ENABLE_WRAP = "\x1b[?7h";
const CLEAR_LINE = "\x1b[2K";

const color = {
  dim: (text: string) => `\x1b[90m${text}\x1b[0m`,
  bold: (text: string) => `\x1b[1m${text}\x1b[0m`,
  cyan: (text: string) => `\x1b[36m${text}\x1b[0m`,
  green: (text: string) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text: string) => `\x1b[33m${text}\x1b[0m`,
  red: (text: string) => `\x1b[31m${text}\x1b[0m`,
};

const divider = {
  vertical: color.dim(" │ "),
  horizontal: (width: number, label: string) => color.dim(sectionRule(width, label)),
};

export class TerminalUi {
  private readonly runtime: AgentRuntime;
  private readonly options: TerminalUiOptions;
  private readonly unsubscribe: () => void;
  private chat: ChatLine[] = [];
  private logs: string[] = [];
  private tasks: AgentTask[] = [];
  private metrics: RuntimeMetrics = { tokens: "--", cost: "--", latency: "--", git: "--" };
  private model: string;
  private status: AgentStatus = "Idle";
  private currentStep = "Ready";
  private input = "";
  private chatScrollOffset = 0;
  private stopped = false;

  constructor(runtime: AgentRuntime, options: TerminalUiOptions) {
    this.runtime = runtime;
    this.options = options;
    this.model = options.model;
    this.unsubscribe = runtime.subscribe((event) => this.handleEvent(event));
  }

  start(): void {
    process.stdout.write(`${ALT_SCREEN}${DISABLE_WRAP}`);
    emitKeypressEvents(process.stdin);
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
    }
    process.stdin.setEncoding("utf8");
    process.stdin.resume();
    process.stdin.on("keypress", this.onKeypress);
    process.stdout.on("resize", this.render);
    process.on("SIGINT", () => this.stop());
    process.on("SIGTERM", () => this.stop());
    this.pushSystem("LumaK code-agent TUI started. Type /help for commands.");
    this.render();
  }

  stop(): void {
    if (this.stopped) {
      return;
    }
    this.stopped = true;
    this.unsubscribe();
    this.runtime.dispose();
    process.stdin.off("keypress", this.onKeypress);
    process.stdout.off("resize", this.render);
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(false);
    }
    process.stdout.write(`${ENABLE_WRAP}${MAIN_SCREEN}`);
    process.exit(0);
  }

  private readonly onKeypress = (chunkValue: unknown, keyValue?: unknown) => {
    const chunk = typeof chunkValue === "string" ? chunkValue : "";
    const key = isKeypress(keyValue) ? keyValue : undefined;
    if (key?.ctrl && key.name === "c") {
      this.stop();
      return;
    }
    if (key?.name === "return") {
      void this.submitInput();
      return;
    }
    if (key?.name === "up" || key?.name === "pageup") {
      this.scrollChat(key.name === "pageup" ? 8 : 1);
      return;
    }
    if (key?.name === "down" || key?.name === "pagedown") {
      this.scrollChat(key.name === "pagedown" ? -8 : -1);
      return;
    }
    if (key?.name === "home") {
      this.chatScrollOffset = Number.MAX_SAFE_INTEGER;
      this.render();
      return;
    }
    if (key?.name === "end") {
      this.chatScrollOffset = 0;
      this.render();
      return;
    }
    if (key?.name === "backspace") {
      this.input = this.input.slice(0, -1);
      this.render();
      return;
    }
    if (key?.ctrl && key.name === "u") {
      this.input = "";
      this.render();
      return;
    }
    if (!key?.ctrl && chunk && chunk >= " " && chunk !== "\x7f") {
      this.input += chunk;
      this.render();
    }
  };

  private async submitInput(): Promise<void> {
    const text = this.input.trim();
    this.input = "";
    if (!text) {
      this.render();
      return;
    }

    if (text === "/exit" || text === "/quit") {
      this.stop();
      return;
    }
    if (text === "/clear") {
      this.chat = [];
      this.logs = [];
      this.chatScrollOffset = 0;
      this.pushSystem("Screen cleared.");
      this.render();
      return;
    }
    if (text === "/help") {
      this.pushSystem("Commands: /help show commands, /clear clear chat and logs, /exit leave the TUI. Enter submits, Ctrl+C exits. Scroll chat with Up/Down, PageUp/PageDown, Home/End.");
      this.render();
      return;
    }

    try {
      this.chatScrollOffset = 0;
      await this.runtime.sendMessage(text);
    } catch (error) {
      if (!this.stopped) {
        this.handleEvent({
          type: "error",
          id: `error-${Date.now()}`,
          message: error instanceof Error ? error.message : String(error),
          timestamp: Date.now(),
        });
      }
    }
  }

  private handleEvent(event: AgentEvent): void {
    if (event.type === "user_message") {
      this.chatScrollOffset = 0;
      this.chat.push({ kind: "message", role: "you", content: event.content });
    } else if (event.type === "assistant_message") {
      this.chatScrollOffset = 0;
      this.chat.push({ kind: "message", role: "lumaK", content: event.content });
    } else if (event.type === "thinking_start") {
      this.status = "Thinking";
      this.currentStep = event.label || "Thinking";
      this.addLog(this.currentStep);
    } else if (event.type === "thinking_end") {
      this.addLog("Thinking finished");
    } else if (event.type === "tool_call_start") {
      this.status = "Running Tool";
      this.currentStep = `Running ${event.name}`;
      this.chatScrollOffset = 0;
      this.chat.push({ kind: "tool", id: event.id, name: event.name, args: event.args, status: "running" });
      this.addLog(`Tool started: ${event.name}`);
    } else if (event.type === "tool_call_end") {
      const block = this.chat.find((item) => item.kind === "tool" && item.id === event.id);
      if (block?.kind === "tool") {
        block.status = event.status;
        block.resultPreview = event.resultPreview;
      }
      this.addLog(`Tool ${event.status}: ${event.id}`);
    } else if (event.type === "error") {
      this.status = "Error";
      this.currentStep = "Recovered from error";
      this.chatScrollOffset = 0;
      this.chat.push({ kind: "error", content: event.message });
      this.addLog(`Error: ${event.message}`);
    } else if (event.type === "status_update") {
      this.status = event.status;
      this.model = event.model || this.model;
      this.currentStep = event.currentStep || this.currentStep;
      this.tasks = event.tasks || this.tasks;
      this.metrics = event.metrics || this.metrics;
      if (event.log) {
        this.addLog(event.log);
      }
    }
    this.render();
  }

  private render = (): void => {
    if (this.stopped) {
      return;
    }
    const width = Math.max(50, process.stdout.columns || 88);
    const height = Math.max(18, process.stdout.rows || 28);
    const header = this.renderHeader(width);
    const input = this.renderInput(width);
    const bodyHeight = Math.max(5, height - header.length - input.length);
    const body = chooseLayout(width, height) === "side" ? this.renderSideBody(width, bodyHeight) : this.renderStackedBody(width, bodyHeight);
    const screen = [...header, ...body, ...input].slice(0, height).map((line) => fitColumn(line, width));
    while (screen.length < height) {
      screen.push("");
    }

    // Move cursor to input position (IME needs this anchor)
    // screen = header + body + input. input[1] is the content line (middle of 3-line input frame).
    // screen indices: header.len (3) + bodyHeight + 0 = border, + 1 = content, + 2 = border
    // content is at index: header.len + bodyHeight + 1 = height - 3 + 1 = height - 2 (0-based)
    // 1-based row = (height - 2) + 1 = height - 1
    const inputRow = height - 1; // 1-based
    const promptStr = "❯ ";
    const promptCol = stringWidth(promptStr); // should be 2
    const cursorCol = promptCol + 1 + stringWidth(this.input); // prompt + space + input
    const cursorMove = `\x1b[${inputRow};${cursorCol}H`;
    const screenOutput = `${CLEAR}${screen.map((line) => `${CLEAR_LINE}${line}`).join("\n")}${cursorMove}`;
    process.stdout.write(screenOutput);
  };

  private renderHeader(width: number): string[] {
    const status = this.status;
    const indicator = runtimeIndicator(status);
    return [
      color.bold(padRight(` ${indicator} ${this.options.projectName} | model ${this.model} | cwd ${this.options.workspace} | ${status}`, width)),
      color.dim(padRight(` step: ${this.currentStep}`, width)),
      color.dim("─".repeat(width)),
    ];
  }

  private renderInput(width: number): string[] {
    return renderInputFrame(this.input, this.status, width);
  }

  private renderSideBody(width: number, height: number): string[] {
    const separatorWidth = 3;
    const statusWidth = Math.min(40, Math.max(32, Math.floor(width * 0.32)));
    const chatWidth = Math.max(20, width - statusWidth - separatorWidth);
    const chat = this.withPanelHeader(this.chatTitle(), chatWidth, this.renderChat(chatWidth, Math.max(1, height - 1)));
    const status = this.withPanelHeader("Status", statusWidth, this.renderStatus(statusWidth, Math.max(1, height - 1)));
    return Array.from(
      { length: height },
      (_, index) => `${fitColumn(chat[index] || "", chatWidth)}${divider.vertical}${fitColumn(status[index] || "", statusWidth)}`,
    );
  }

  private renderStackedBody(width: number, height: number): string[] {
    const statusHeight = Math.min(10, Math.max(6, Math.floor(height * 0.35)));
    const chatHeight = Math.max(3, height - statusHeight - 2);
    return [
      divider.horizontal(width, this.chatTitle()),
      ...this.renderChat(width, chatHeight),
      divider.horizontal(width, "Status"),
      ...this.renderStatus(width, statusHeight),
    ].slice(0, height);
  }

  private renderChat(width: number, height: number): string[] {
    const lines: string[] = [];
    if (this.chat.length === 0) {
      lines.push(color.dim("No messages yet."));
    }
    for (const item of this.chat) {
      if (item.kind === "message") {
        lines.push(...renderMessageBox(item, width));
        lines.push("");
      } else if (item.kind === "tool") {
        lines.push(...this.renderTool(item, width));
        lines.push("");
      } else {
        lines.push(...this.renderWrapped("error> ", item.content, width).map((line) => color.red(line)));
        lines.push("");
      }
    }
    this.chatScrollOffset = Math.min(this.chatScrollOffset, Math.max(0, lines.length - height));
    return viewport(lines, height, this.chatScrollOffset);
  }

  private renderTool(item: Extract<ChatLine, { kind: "tool" }>, width: number): string[] {
    return renderToolPreview(item, width);
  }

  private renderWrapped(prefix: string, content: string, width: number): string[] {
    const bodyWidth = Math.max(8, width - visibleLength(prefix));
    const prefixWidth = visibleLength(prefix);
    return wrapText(content, bodyWidth).map((line, index) => `${index === 0 ? prefix : " ".repeat(prefixWidth)}${line}`);
  }

  private renderStatus(width: number, height: number): string[] {
    const topLines = [
      padRight(`state: ${this.status}`, width),
      padRight(`step: ${this.currentStep}`, width),
      padRight(`tokens: ${this.metrics.tokens || "--"}  cost: ${this.metrics.cost || "--"}`, width),
      padRight(`latency: ${this.metrics.latency || "--"}  git: ${this.metrics.git || "--"}`, width),
    ];
    const taskLines = [
      color.dim(padRight("Tasks", width)),
      ...this.renderTasks(width),
    ];
    const logCapacity = Math.max(0, height - topLines.length - taskLines.length - 1);
    const lines = [
      ...topLines,
      ...taskLines,
      color.dim(padRight("Logs", width)),
      ...this.logs.slice(-logCapacity).map((line) => padRight(`- ${line}`, width)),
    ];
    return head(lines, height);
  }

  private renderTasks(width: number): string[] {
    if (this.tasks.length === 0) {
      return [padRight("- none", width)];
    }
    return this.tasks.slice(0, 5).map((task) => padRight(`${taskMark(task.status)} ${task.title}`, width));
  }

  private pushSystem(content: string): void {
    this.chat.push({ kind: "message", role: "system", content });
  }

  private addLog(line: string): void {
    this.logs.push(line);
    this.logs = this.logs.slice(-8);
  }

  private withPanelHeader(title: string, width: number, lines: string[]): string[] {
    return [divider.horizontal(width, title), ...lines];
  }

  private chatTitle(): string {
    if (this.chatScrollOffset <= 0) {
      return "Chat / Trace";
    }
    return this.chatScrollOffset > 999 ? "Chat / Trace ↑top" : `Chat / Trace ↑${this.chatScrollOffset}`;
  }

  private scrollChat(delta: number): void {
    this.chatScrollOffset = Math.max(0, this.chatScrollOffset + delta);
    this.render();
  }
}

function isKeypress(value: unknown): value is { name?: string; ctrl?: boolean; sequence?: string } {
  return typeof value === "object" && value !== null;
}

function tail(lines: string[], height: number): string[] {
  const visible = lines.slice(Math.max(0, lines.length - height));
  while (visible.length < height) {
    visible.push("");
  }
  return visible;
}

function viewport(lines: string[], height: number, scrollOffset: number): string[] {
  const maxOffset = Math.max(0, lines.length - height);
  const offset = Math.min(scrollOffset, maxOffset);
  const end = Math.max(height, lines.length - offset);
  const visible = lines.slice(Math.max(0, end - height), end);
  while (visible.length < height) {
    visible.push("");
  }
  return visible;
}

function head(lines: string[], height: number): string[] {
  const visible = lines.slice(0, height);
  while (visible.length < height) {
    visible.push("");
  }
  return visible;
}

export function renderToolPreview(item: Extract<ChatLine, { kind: "tool" }>, width: number): string[] {
  const boxWidth = Math.max(20, width);
  const borderWidth = Math.max(8, boxWidth - 2);
  const innerWidth = Math.max(8, boxWidth - 4);
  const title = ` ${toolStatusDot(item.status)} ${item.name} ${item.status} `;
  const borderFill = "─".repeat(Math.max(0, borderWidth - visibleLength(title)));
  const bodyLines = [
    ...wrapText(`args: ${formatArgsSummary(item.args, innerWidth)}`, innerWidth),
    ...(item.resultPreview ? wrapText(`result: ${item.resultPreview}`, innerWidth) : []),
  ];
  const previewLines = bodyLines.slice(0, 4);
  const hidden = bodyLines.length - previewLines.length;
  const lines = [
    fitColumn(`╭${title}${borderFill}╮`, boxWidth),
    ...previewLines.map((line) => fitColumn(`│ ${line}`, boxWidth - 1) + "│"),
  ];

  if (hidden > 0) {
    lines.push(fitColumn(color.dim(`│ ... ${hidden} more hidden`), boxWidth - 1) + color.dim("│"));
  }

  lines.push(color.dim(`╰${"─".repeat(borderWidth)}╯`));

  if (item.status === "failed") {
    return lines.map((line) => color.red(truncateVisible(line, width)));
  }
  return lines.map((line) => truncateVisible(line, width));
}

export function renderMessageBox(item: Extract<ChatLine, { kind: "message" }>, width: number): string[] {
  const boxWidth = Math.max(20, width);
  const borderWidth = Math.max(8, boxWidth - 2);
  const innerWidth = Math.max(8, boxWidth - 4);
  const title = ` ${messageRoleLabel(item.role)} `;
  const borderFill = "─".repeat(Math.max(0, borderWidth - visibleLength(title)));
  const contentLines = wrapText(item.content, innerWidth);
  const lines = [
    fitColumn(`╭${title}${borderFill}╮`, boxWidth),
    ...contentLines.map((line) => fitColumn(`│ ${line}`, boxWidth - 1) + "│"),
    color.dim(`╰${"─".repeat(borderWidth)}╯`),
  ];

  const fitted = lines.map((line) => truncateVisible(line, width));
  if (item.role === "system") {
    return fitted.map((line) => color.dim(line));
  }
  return fitted;
}

export function renderInputFrame(input: string, status: AgentStatus, width: number): string[] {
  const prompt = "❯ ";
  const busyText = status === "Thinking" || status === "Running Tool" ? color.dim("  [busy]") : "";
  const busyWidth = visibleLength(busyText);
  const promptWidth = visibleLength(prompt);
  const available = Math.max(1, width - promptWidth - busyWidth);
  const truncatedInput = truncateToWidth(input, available);
  return [
    color.dim("─".repeat(width)),
    `${prompt}${truncatedInput} `,
    color.dim("─".repeat(width)),
  ];
}

function truncateToWidth(text: string, maxWidth: number): string {
  if (visibleLength(text) <= maxWidth) {
    return text;
  }
  let result = "";
  let width = 0;
  for (const char of text) {
    const charW = charWidth(char);
    if (width + charW > maxWidth) {
      break;
    }
    result += char;
    width += charW;
  }
  return result;
}

export function taskMark(status: AgentTask["status"]): string {
  if (status === "done") {
    return color.dim("●");
  }
  if (status === "running") {
    return color.green("●");
  }
  if (status === "failed") {
    return color.red("●");
  }
  return color.dim("○");
}

function runtimeIndicator(status: AgentStatus): string {
  if (status === "Thinking" || status === "Running Tool") {
    return color.green("●");
  }
  if (status === "Error") {
    return color.red("●");
  }
  return color.dim("●");
}

function toolStatusDot(status: ToolStatus): string {
  if (status === "running") {
    return color.green("●");
  }
  if (status === "failed") {
    return color.red("●");
  }
  return color.dim("●");
}

function messageRoleLabel(role: Extract<ChatLine, { kind: "message" }>["role"]): string {
  if (role === "lumaK") {
    return `${color.green("●")} ${color.bold("lumaK")}`;
  }
  if (role === "you") {
    return `${color.cyan("●")} ${color.bold("you")}`;
  }
  return "system";
}

function sectionRule(width: number, label: string): string {
  if (width <= 0) {
    return "";
  }
  const title = ` ${label} `;
  const titleWidth = visibleLength(title);
  if (width <= titleWidth + 2) {
    return "─".repeat(width);
  }
  return `${title}${"─".repeat(width - titleWidth)}`;
}

function stripAnsi(text: string): string {
  return text.replace(/\x1b\[[0-9;]*m/g, "");
}

function visibleLength(text: string): number {
  let width = 0;
  for (const char of stripAnsi(text)) {
    width += charWidth(char);
  }
  return width;
}

function truncateVisible(text: string, width: number): string {
  if (visibleLength(text) <= width) {
    return text;
  }
  if (width <= 3) {
    return ".".repeat(Math.max(0, width));
  }

  let output = "";
  let visible = 0;
  for (let index = 0; index < text.length; ) {
    const ansi = /^\x1b\[[0-9;]*m/.exec(text.slice(index));
    if (ansi) {
      output += ansi[0];
      index += ansi[0].length;
      continue;
    }

    const codePoint = text.codePointAt(index);
    if (codePoint === undefined) {
      break;
    }
    const char = String.fromCodePoint(codePoint);
    const nextWidth = charWidth(char);
    if (visible + nextWidth > width - 3) {
      break;
    }
    output += char;
    visible += nextWidth;
    index += char.length;
  }
  return `${output}\x1b[0m...`;
}

function padVisible(text: string, width: number): string {
  const truncated = truncateVisible(text, width);
  return `${truncated}${" ".repeat(Math.max(0, width - visibleLength(truncated)))}`;
}

function fitColumn(text: string, width: number): string {
  return padVisible(text, width);
}

function charWidth(char: string): number {
  const codePoint = char.codePointAt(0) || 0;
  if (codePoint === 0) {
    return 0;
  }
  if (codePoint < 32 || (codePoint >= 0x7f && codePoint < 0xa0)) {
    return 0;
  }
  if (
    codePoint >= 0x1100 &&
    (codePoint <= 0x115f ||
      codePoint === 0x2329 ||
      codePoint === 0x232a ||
      (codePoint >= 0x2e80 && codePoint <= 0xa4cf && codePoint !== 0x303f) ||
      (codePoint >= 0xac00 && codePoint <= 0xd7a3) ||
      (codePoint >= 0xf900 && codePoint <= 0xfaff) ||
      (codePoint >= 0xfe10 && codePoint <= 0xfe19) ||
      (codePoint >= 0xfe30 && codePoint <= 0xfe6f) ||
      (codePoint >= 0xff00 && codePoint <= 0xff60) ||
      (codePoint >= 0xffe0 && codePoint <= 0xffe6))
  ) {
    return 2;
  }
  return 1;
}

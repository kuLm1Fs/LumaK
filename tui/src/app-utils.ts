export type CliArgs = {
  gatewayUrl: string;
  maxTokens: number;
  model: string;
  runtime: "mock" | "gateway";
  sessionId: string;
  startGateway: boolean;
  workspace: string;
};

export type AgentPayload = Record<string, unknown>;
export type LocalGatewayAddress = {
  host: string;
  port: string;
};

import wrapAnsi from "wrap-ansi";
import stringWidth from "string-width";
import sliceAnsi from "slice-ansi";

export function wrapText(text: string, width: number): string[] {
  if (width <= 1) {
    return [text];
  }

  return wrapAnsi(text, width, {
    hard: true,
    trim: false,
    wordWrap: true,
  }).split("\n");
}

export function truncateText(text: string, width: number): string {
  if (width <= 0) {
    return "";
  }

  if (stringWidth(text) <= width) {
    return text;
  }

  if (width <= 3) {
    return ".".repeat(width);
  }

  return `${sliceAnsi(text, 0, width - 3)}...`;
}

export function padRight(text: string, width: number): string {
  const truncated = truncateText(text, width);
  const visible = stringWidth(truncated);

  return truncated + " ".repeat(Math.max(0, width - visible));
}

export function formatArgsSummary(args: Record<string, unknown>, width = 80): string {
  const pairs = Object.entries(args).map(([key, value]) => `${key}=${formatValue(value)}`);
  return truncateText(pairs.join(" "), width);
}

export function chooseLayout(width: number, height: number): "side" | "stacked" {
  return width >= 100 && height >= 24 ? "side" : "stacked";
}

export function formatAgentEvent(event: string, payload: AgentPayload = {}): string | null {
  if (event === "skills.selected") {
    const skillNames = payload.skill_names;
    if (Array.isArray(skillNames) && skillNames.length > 0) {
      return `Skills: ${skillNames.map(String).join(", ")}`;
    }
    return "Skills: none";
  }

  if (event === "model.request") {
    return `Model request: ${String(payload.model ?? "default")}`;
  }

  if (event === "tool.before") {
    return `Tool starting: ${String(payload.tool_name ?? "unknown")}`;
  }

  if (event === "tool.after") {
    const toolName = String(payload.tool_name ?? "unknown");
    return payload.success === false ? `Tool failed: ${toolName}` : `Tool done: ${toolName}`;
  }

  if (event === "session.end") {
    return "Session complete";
  }

  return null;
}

export function displayRole(role: string): string {
  return role === "assistant" ? "lumak" : role;
}

export function createSessionId(prefix = "tui"): string {
  const cryptoLike = globalThis.crypto;
  if (cryptoLike && "randomUUID" in cryptoLike) {
    return `${prefix}-${cryptoLike.randomUUID()}`;
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function parseLocalGatewayUrl(url: string): LocalGatewayAddress | null {
  try {
    const parsed = new URL(url);
    if (!["127.0.0.1", "localhost"].includes(parsed.hostname)) {
      return null;
    }

    return {
      host: parsed.hostname,
      port: parsed.port || "8765",
    };
  } catch {
    return null;
  }
}

export function parseCliArgs(argv: string[]): CliArgs {
  const args: CliArgs = {
    gatewayUrl: process.env.LUMAK_GATEWAY_URL || "ws://127.0.0.1:8765",
    maxTokens: 1024,
    model: process.env.LUMAK_MODEL || "mock-code-agent",
    runtime: "gateway",
    sessionId: createSessionId(),
    startGateway: true,
    workspace: process.cwd(),
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--gateway" && next) {
      args.gatewayUrl = next;
      index += 1;
    } else if (arg === "--max-tokens" && next) {
      args.maxTokens = Number.parseInt(next, 10);
      index += 1;
    } else if (arg === "--model" && next) {
      args.model = next;
      index += 1;
    } else if (arg === "--runtime" && next) {
      args.runtime = next === "gateway" ? "gateway" : "mock";
      index += 1;
    } else if (arg === "--session" && next) {
      args.sessionId = next;
      index += 1;
    } else if (arg === "--workspace" && next) {
      args.workspace = next;
      index += 1;
    } else if (arg === "--no-start-gateway") {
      args.startGateway = false;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }
  }

  if (!Number.isFinite(args.maxTokens) || args.maxTokens <= 0) {
    args.maxTokens = 1024;
  }

  return args;
}

export function printHelp(): void {
  process.stdout.write(`LumaK TypeScript TUI

Usage:
  lumak-tui [options]

Options:
  --gateway <url>        WebSocket gateway URL. Default: ws://127.0.0.1:8765
  --runtime <name>       Runtime adapter: gateway or mock. Default: gateway
  --model <name>         Model label shown in the header. Default: mock-code-agent
  --max-tokens <count>   Maximum model output tokens. Default: 1024
  --session <id>         Session id to use. Default: generated tui-* id
  --workspace <path>     Workspace for the auto-started gateway. Default: cwd
  --no-start-gateway     Connect to an existing gateway only
  -h, --help             Show this help
`);
}

function formatValue(value: unknown): string {
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "number" || typeof value === "boolean" || value == null) {
    return String(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => formatValue(item)).join(",")}]`;
  }
  return "{...}";
}

#!/usr/bin/env node
import { parseCliArgs } from "./app-utils.js";
import type { AgentRuntime } from "./events.js";
import { GatewayAgentRuntime } from "./gateway-runtime.js";
import { MockAgentRuntime } from "./mock-runtime.js";
import { TerminalUi } from "./terminal-ui.js";

const args = parseCliArgs(process.argv.slice(2));
const repoRoot = decodeURIComponent(new URL("../..", import.meta.url).pathname);

function createRuntime(): AgentRuntime {
  if (args.runtime === "mock") {
    return new MockAgentRuntime();
  }
  return new GatewayAgentRuntime(args, repoRoot);
}

const ui = new TerminalUi(createRuntime(), {
  projectName: "LumaK",
  model: args.model,
  workspace: args.workspace,
});

ui.start();

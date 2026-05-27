import assert from "node:assert/strict";
import test from "node:test";

import { MockAgentRuntime } from "../dist/mock-runtime.js";

test("mock runtime emits the complete code-agent event flow", async () => {
  const runtime = new MockAgentRuntime();
  const events = [];
  runtime.subscribe((event) => events.push(event));

  await runtime.sendMessage("inspect the project");

  assert.deepEqual(
    events.map((event) => event.type),
    [
      "user_message",
      "status_update",
      "thinking_start",
      "status_update",
      "thinking_end",
      "tool_call_start",
      "tool_call_end",
      "status_update",
      "thinking_start",
      "thinking_end",
      "assistant_message",
      "status_update",
    ],
  );
  assert.equal(events.find((event) => event.type === "tool_call_start")?.name, "workspace_search");
  assert.equal(events.find((event) => event.type === "tool_call_end")?.status, "success");
});

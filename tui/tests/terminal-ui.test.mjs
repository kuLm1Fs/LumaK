import assert from "node:assert/strict";
import test from "node:test";

import { renderInputFrame, renderMessageBox, renderToolPreview, taskMark } from "../dist/terminal-ui.js";

test("input frame uses divider lines and chevron prompt", () => {
  const lines = renderInputFrame("hello", "Idle", 50);

  assert.equal(lines.length, 3);
  assert.equal(stripAnsi(lines[0]), "─".repeat(50));
  assert.equal(stripAnsi(lines[1]), "❯ hello");
  assert.equal(stripAnsi(lines[2]), "─".repeat(50));
});

test("message and tool boxes keep every visible row aligned", () => {
  const message = renderMessageBox(
    {
      kind: "message",
      role: "lumaK",
      content: "A box should keep the right edge aligned with its top and bottom border.",
    },
    48,
  );
  const tool = renderToolPreview(
    {
      id: "tool-1",
      name: "Bash",
      args: { command: "echo done" },
      status: "success",
      resultPreview: "done",
    },
    48,
  );

  assert.deepEqual(message.map(visibleLength), message.map(() => 48));
  assert.deepEqual(tool.map(visibleLength), tool.map(() => 48));
});

test("chat messages render as compact boxed dialogue", () => {
  const lines = renderMessageBox(
    {
      kind: "message",
      role: "lumaK",
      content: "Here is a concise answer with enough text to wrap onto the next line cleanly.",
    },
    48,
  );

  assert.match(lines[0], /lumaK/);
  assert.match(lines[0], /╭/);
  assert.match(lines.at(-1), /╰/);
  assert.ok(lines.every((line) => line.length > 0));
  assert.ok(lines.length >= 4);
});

test("system messages stay visually muted inside the same dialogue shape", () => {
  const lines = renderMessageBox(
    {
      kind: "message",
      role: "system",
      content: "Screen cleared.",
    },
    36,
  );

  assert.match(lines[0], /\x1b\[90m/);
  assert.match(lines[0], /system/);
});

test("tool preview is boxed and keeps event details compact", () => {
  const lines = renderToolPreview(
    {
      id: "tool-1",
      name: "Bash",
      args: {
        command:
          "curl -s http://localhost:3000/lessons/l5 2>&1 | grep -o '\"statusCode\":[0-9]*' || echo 'Page OK'",
        description: "Check lesson page",
      },
      status: "running",
      resultPreview:
        '"statusCode":500\nstack line 1\nstack line 2\nstack line 3\nstack line 4\nstack line 5',
    },
    72,
  );

  assert.match(lines[0], /Bash/);
  assert.match(lines[0], /\x1b\[32m●\x1b\[0m/);
  assert.ok(lines.length <= 8);
  assert.ok(lines.some((line) => line.includes("more hidden")));
});

test("tool preview uses muted dots after commands finish", () => {
  const lines = renderToolPreview(
    {
      id: "tool-1",
      name: "Bash",
      args: { command: "echo done" },
      status: "success",
      resultPreview: "done",
    },
    40,
  );

  assert.match(lines[0], /\x1b\[90m●\x1b\[0m/);
});

test("task marks use colored status dots", () => {
  assert.match(taskMark("running"), /\x1b\[32m●\x1b\[0m/);
  assert.match(taskMark("done"), /\x1b\[90m●\x1b\[0m/);
  assert.match(taskMark("pending"), /\x1b\[90m○\x1b\[0m/);
});

function stripAnsi(text) {
  return text.replace(/\x1b\[[0-9;]*m/g, "");
}

function visibleLength(text) {
  return [...stripAnsi(text)].length;
}

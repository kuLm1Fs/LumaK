# Evaluation: Session History Pollution & Tool Content Leak

## Problem

Session `22611b99-31f6-4e88-94c3-77c1c7c3121e` exhibited multiple cascading failures:

### 1. Memory store polluted with tool internals
- `loop.py` wrote `serialize_content_blocks(response.content)` (thinking, tool_use blocks) into `MemoryStore` as assistant messages
- Tool results (via `append_message(messages, {"role": "user", "content": results}, memory_store=...)`) were also persisted
- On session resume, these appeared as conversation history, confusing the model

### 2. History bloat with no dedup
- Same session_id reused across page reloads and project switches (lumaK → TripWeaver → RAG → lumaK)
- `session.py:prepare_session_messages` appended incoming messages without checking for duplicates
- Same user message ("分析当前目录的结构") appeared 2-3 times in history
- Message count grew from 1 to 13 across sub-sessions

### 3. `glob('**/*')` hang
- `run_glob` would traverse `node_modules/` matching thousands of files, causing multi-minute hangs
- No timeout mechanism

### 4. Session ID never rotates
- Web frontend's `getOrCreateSessionId()` cached the same UUID in `localStorage` permanently
- Every page load and project switch reused the same session, accumulating stale history

### 5. Empty chat.response when model returns tool_use-only
- `response_to_text` was changed to return `""` instead of `str(response.content)` (fixing the raw Python object leak)
- But MiniMax sometimes returns `end_turn` with only `ToolUseBlock`s (no text), causing empty answer → frontend showed "Agent 已完成，但没有返回文本。"
- No fallback in gateway for this case

### Trace Evidence
File: `.trace/22611b99-31f6-4e88-94c3-77c1c7c3121e.jsonl`
- Lines 5-7: model returned `glob('**/*')` tool_use, no tool.before/tool.after followed, 3-minute gap
- Lines 8-13: session restarted with same message, same glob call, same hang
- Lines 70-74: old assistant tool_use blocks and tool results injected as user messages
- Lines 86-89: same contamination pattern repeated
- Line 157: `session.end {final_output: "max steps reached"}`

---

## Diagnosis Approach

1. **Trace inspection**: Read `.trace/{session_id}.jsonl` to understand the event timeline
2. **Code flow analysis**: Traced `agent.run()` → `agent_loop()` → `llm_client.messages.create()` → response handling → `memory_store`
3. **Cross-reference**: Compared trace events with `loop.py`, `session.py`, `store.py`, and `gateway/app.py` to identify the exact lines causing each issue
4. **Test gap analysis**: Found existing tests (`test_agent_loop_persists_tool_results_to_session_memory`) that explicitly ASSERTED the buggy behavior (tool results SHOULD be in memory), confirming the tests need to be updated alongside the fix

---

## Fixes Applied

### P1: Stop tool internals from polluting memory store
**Files:** `agent/runtime/loop.py`, `agent/runtime/session.py`

- Assistant responses with `stop_reason="tool_use"`: only persist text portion to memory, not thinking/tool_use blocks
- Tool results (`{"role": "user", "content": results}`): append to in-memory `messages` list only, skip `memory_store`
- Removed inline `append_message()`; uses `prepare_session_messages` from `session.py`

### P2: Dedup incoming messages
**File:** `agent/runtime/session.py`

- Added `_is_duplicate_of_last()` check: if a new incoming message matches the last persisted message (same `role` + same `content`), skip writing

### P3: Session rotation
**File:** `web/src/app.ts`

- `getOrCreateSessionId()` always generates a new UUID on page load (instead of reusing localStorage)
- Old conversations remain accessible via sidebar (`setActiveConversation`)

### P4: Glob safety
**File:** `agent/tools/filesystems.py`

- Added `"node_modules"` to `SKIPPED_DIRS`
- Added 8-second timeout to `run_glob()` (matches existing `run_search_text` pattern)

### P5: Empty chat.response fallback
**File:** `gateway/app.py`

- When `response_to_text` returns empty, check response content:
  - Has `tool_use` blocks but no text → `"已调用工具：{names}"`
  - `stop_reason == "max_tokens"` → prompt about truncation
  - Otherwise → keep original fallback message

### P6: Stop raw Python object leak
**Files:** `agent/runtime/loop.py`, `agent/CLI/app.py`

- `response_to_text` no longer falls back to `str(response.content)` → returns `""` instead of `[ThinkingBlock(...), ToolUseBlock(...)]`

### P7: Memory store preview safety
**File:** `agent/memory/store.py`

- `_preview_for_message` returns `"(工具调用)"` instead of `str(non_text_content)` for non-string content

---

## Test Updates
**File:** `tests/test_agent_loop.py`

- Renamed `test_agent_loop_persists_tool_results_to_session_memory` → `test_agent_loop_does_not_persist_tool_results_to_session_memory` with inverted assertions
- Renamed `test_agent_loop_serializes_non_json_sdk_blocks_before_persisting_memory` → `test_agent_loop_only_persists_text_not_thinking_blocks` with inverted assertions

**File:** `tests/test_runtime_session.py`

- Added `test_prepare_session_messages_dedup_duplicate_incoming` to verify dedup behavior

All 88 tests pass.

---

## Outcome

| Before | After |
|--------|-------|
| memory_store contains thinking + tool_use + tool_result | Only clean user/assistant text persisted |
| Same message retried → stored 3x | Auto-dedup, stored once |
| Page reload → loads all garbage history | Fresh sessionId generated |
| `glob('**/*')` traverses `node_modules`, hangs | Excluded + 8s timeout |
| Raw `[ThinkingBlock(...)]` appears as answer | Empty answer caught with meaningful fallback |
| Tool-only responses show "没有返回文本" | Shows "已调用工具：{name}" |

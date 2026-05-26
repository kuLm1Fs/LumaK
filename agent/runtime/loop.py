from pathlib import Path
from agent.tools.registry import TOOLS, execute_tool
from agent.trace.trace import make_session_id, AgentTrace, TraceHook
from agent.runtime.hooks import Hook, HookManager
from agent.memory.store import MemoryStore
import time


ROOT_DIR = Path(__file__).resolve().parents[1]


def get_default_client():
    from agent.LLM.client import get_default_client as create_default_client

    return create_default_client()

def response_to_text(response) -> str:
    texts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(texts).strip() or str(response.content)


def emit_hook(
        hook_manager: HookManager,
        event: str,
        payload: dict,
        *,
        session_id: str,
        workspace: Path,
) -> None:
    hook_manager.emit(
        event,
        payload,
        session_id=session_id,
        workspace=str(workspace),
    )

def append_message(
    messages: list,
    message: dict,
    *,
    memory_store: MemoryStore | None,
    session_id: str,) -> None:
    messages.append(message)
    if memory_store:
        memory_store.append_message(session_id, message)

def agent_loop(
        messages: list, 
        max_tokens: int = 1024, 
        workspace: Path = ROOT_DIR, 
        max_steps: int = 6,
        session_id: str | None = None,
        llm_client=None,
        hooks: list[Hook] | None = None,
        memory_store: MemoryStore | None = None,) -> list[str]:
    llm_client = llm_client or get_default_client()
    session_id = session_id or make_session_id()
    trace = AgentTrace(workspace=workspace, session_id=session_id)
    hook_manager = HookManager([TraceHook(trace), *(hooks or [])])
    incoming_messages = list(messages)
    if memory_store:
        persisted_messages = memory_store.load_messages(session_id)
        for message in incoming_messages:
            memory_store.append_message(session_id, message)
        messages = [*persisted_messages, *incoming_messages]

    emit_hook(
        hook_manager,
        "session.start",
        {"session_id": session_id},
        session_id=session_id,
        workspace=workspace,
    )

    for message in messages:
        if isinstance(message, dict):
            emit_hook(
                hook_manager,
                "message",
                {
                    "role": message.get("role", "unknow"),
                    "content": str(message.get("content", "")),
                },
                session_id=session_id,
                workspace=workspace,
            )

    for i in range(max_steps):
        emit_hook(
            hook_manager,
            "loop.iteration.start",
            {"iteration": i + 1},
            session_id=session_id,
            workspace=workspace,
        )

        request_start = time.perf_counter()
        emit_hook(
            hook_manager,
            "model.request",
            {
                "model": llm_client.default_model,
                "max_tokens": max_tokens,
                "message_count": len(messages),
                "tool_names": [tool["name"] for tool in TOOLS],
            },
            session_id=session_id,
            workspace=workspace,
        )
        response = llm_client.messages.create(
            model=llm_client.default_model,
            max_tokens=max_tokens,
            messages=messages,
            tools=TOOLS,
        )
        request_elapsed = (time.perf_counter() - request_start) * 1000
        emit_hook(
            hook_manager,
            "model.response",
            {
                "stop_reason": response.stop_reason,
                "content": response_to_text(response),
            },
            session_id=session_id,
            workspace=workspace,
        )
        emit_hook(
            hook_manager,
            "loop.model.duration",
            {
                "duration_ms": request_elapsed,
                "stop_reason": response.stop_reason,
            },
            session_id=session_id,
            workspace=workspace,
        )

        append_message(
            messages,
            {"role": "assistant", "content": response.content},
            memory_store=memory_store,
            session_id=session_id,
        )

        if response.stop_reason != "tool_use" :
            final_text = response_to_text(response)
            emit_hook(
                hook_manager,
                "session.end",
                {"final_output": final_text},
                session_id=session_id,
                workspace=workspace,
            )
            return response
        results = []
        for block in response.content:
            if block.type == "tool_use":
                emit_hook(
                    hook_manager,
                    "tool.before",
                    {
                        "tool_name": block.name,
                        "tool_input": block.input,
                        "tool_use_id": block.id,
                    },
                    session_id=session_id,
                    workspace=workspace,
                )
                tool_start = time.perf_counter()
                success = True
                output = ""
                try:
                    output = execute_tool(block.name, block.input, workspace=workspace)
                except Exception as exc:
                    output = str(exc)
                    success = False
                finally:
                    tool_elapsed = (time.perf_counter() - tool_start) * 1000
                emit_hook(
                    hook_manager,
                    "tool.after",
                    {
                        "tool_name": block.name,
                        "tool_input": block.input,
                        "tool_use_id": block.id,
                        "output": output,
                        "success": success,
                        "duration_ms": tool_elapsed,
                    },
                    session_id=session_id,
                    workspace=workspace,
                )
                print(output[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})

        append_message(
            messages,
            {"role": "user", "content": results},
            memory_store=memory_store,
            session_id=session_id,
        )

    emit_hook(
        hook_manager,
        "session.end",
        {"final_output": "max steps reached"},
        session_id=session_id,
        workspace=workspace,
    )
    return messages

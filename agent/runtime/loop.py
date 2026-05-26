from pathlib import Path
from agent.tools.registry import TOOLS, execute_tool
from agent.storage.trace import make_session_id, AgentTrace
import time


ROOT_DIR = Path(__file__).resolve().parents[1]


def get_default_client():
    from agent.LLM.client import get_default_client as create_default_client

    return create_default_client()

def response_to_text(response) -> str:
    texts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(texts).strip() or str(response.content)

def agent_loop(messages: list, 
               max_tokens: int = 1024, 
               workspace: Path = ROOT_DIR, 
               max_steps: int = 6,
               session_id: str | None = None,
               llm_client=None) -> list[str]:
    llm_client = llm_client or get_default_client()
    session_id = session_id or make_session_id()
    trace = AgentTrace(workspace=workspace, session_id=session_id)

    for message in messages:
        if isinstance(message, dict):
            trace.record_message(message.get("role", "unknow"), str(message.get("content", "")))

    for i in range(max_steps):
        trace.record_event("loop.iteration.start", {"iteration" : i + 1})

        request_start = time.perf_counter()
        response = llm_client.messages.create(
            model=llm_client.default_model,
            max_tokens=max_tokens,
            messages=messages,
            tools=TOOLS,
        )
        request_elapsed = (time.perf_counter() - request_start) * 1000
        trace.record_model_request(
            prompt=messages,
            max_tokens=max_tokens,
            tools=[tool["name"] for tool in TOOLS],
        )
        trace.record_model_response(
            stop_reason=response.stop_reason,
            content=response_to_text(response),
        )
        trace.record_event("loop.model.duration", {
            "duration_ms": request_elapsed,
            "stop_reason": response.stop_reason,
        })

        messages.append({"role" : "assistant" , "content": response.content})

        if response.stop_reason != "tool_use" :
            final_text = response_to_text(response)
            trace.record_session_end(final_text)
            return response
        results = []
        for block in response.content:
            if block.type == "tool_use":
                trace.record_event("tool.call.start", {
                    "tool_name": block.name,
                    "tool_input": block.input,
                    "tool_use_id": block.id,
                })
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
                trace.record_tool_call(
                    tool_name=block.name,
                    tool_input=block.input,
                    output=output,
                    success=success,
                    elapsed_ms=tool_elapsed,
                )
                trace.record_event("tool.call.end", {
                    "tool_name": block.name,
                    "tool_use_id": block.id,
                    "duration_ms": tool_elapsed,
                })
                print(output[:200])
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})

        messages.append({"role": "user", "content": results})

    trace.record_session_end("max steps reached")
    return messages

from pathlib import Path
from agent.LLM.client import client
from agent.tools.registry import TOOLS, execute_tool


ROOT_DIR = Path(__file__).resolve().parents[1]

def response_to_text(response) -> str:
    texts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(texts).strip() or str(response.content)

def agent_loop(messages: list, max_tokens: int = 1024, workspace: Path = ROOT_DIR, max_steps: int = 6) -> list[str]:
    for i in range(max_steps):
        response = client.messages.create(
            model=client.default_model,
            max_tokens=max_tokens,
            messages=messages,
            tools=TOOLS,
        )
        messages.append({"role" : "assistant" , "content": response.content})

        if response.stop_reason != "tool_use" :
            return response
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m$ {block.name} {block.input}\033[0m")
                output = execute_tool(block.name, block.input)
                print(output[:200])
                results.append({"type" : "tool_result", "tool_use_id" : block.id,
                                "content" : output})
        messages.append({"role": "user", "content" : results})

    return messages

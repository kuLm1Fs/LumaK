import os
import subprocess

from pathlib import Path
from agent.LLM.client import client
from agent.tools.shell import run_bash


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
        )
        messages.append({"role" : "assistant" , "content": response.content})

        if response.stop_reason != "tool_use" :
            return response
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(block.input["command"])
                print(output[:200])
                results.append({"type" : "tool_result", "tool_use_id" : block.id,
                                "content" : output})
        messages.append({"role": "user", "content" : results})

    return messages
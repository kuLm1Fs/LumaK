from __future__ import annotations

import argparse

from pathlib import Path
from agent.trace.trace import make_session_id


def response_to_text(response) -> str:
    texts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(texts).strip()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with the agent from the CLI.")
    parser.add_argument("prompt", nargs="*", help="Prompt to send once and exit.")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum tokens to request from the model.",
    )
    return parser

def run_once(prompt: str, max_tokens: int) -> None:
    from agent.runtime.agent.agent import Agent, AgentConfig

    config = AgentConfig(
        workspace=Path.cwd(),
        max_tokens=max_tokens,
        session_id=make_session_id(),
        skills_root=Path(".skills"),
    )
    cli_agent = Agent(config)
    messages = [{"role": "user", "content": prompt}]
    response = cli_agent.run(messages)
    print(response_to_text(response))


def run_chat(max_tokens: int) -> None:
    from agent.runtime.agent.agent import Agent, AgentConfig

    print("LumaK is ready. Type 'exit' or 'quit' to stop.")
    messages = []
    cli_agent = Agent(
        AgentConfig(
            workspace=Path.cwd(),
            max_tokens=max_tokens,
            skills_root=Path(".skills"),
        )
    )

    while True:
        user_input = input("you>").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})
        response = cli_agent.run(messages)
        print(f"assistant> {response_to_text(response)}")


def main() -> None:
    args = build_parser().parse_args()

    if args.prompt:
        run_once(" ".join(args.prompt), max_tokens=args.max_tokens)
        return

    run_chat(max_tokens=args.max_tokens)


if __name__ == "__main__":
    main()

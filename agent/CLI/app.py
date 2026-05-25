from __future__ import annotations

import argparse

from pathlib import Path
from agent.runtime.loop import response_to_text
from agent.runtime.agent.agent import Agent, AgentConfig
from uuid import uuid4
from agent.storage.trace import make_session_id

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with the agent from the CLI.")
    parser.add_argument("prompt", nargs="*", help="Prompt to send once and exit.")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens to request from the model.",
    )
    return parser

def run_once(prompt: str, max_tokens: int) -> None:
    config = AgentConfig(
        workspace=Path.cwd(),
        max_tokens=max_tokens,
        session_id=make_session_id(),
    )
    cli_agent = Agent(config)
    messages = [{"role": "user", "content": prompt}]
    response = cli_agent.run(messages)
    print(response_to_text(response))


def run_chat(max_tokens: int) -> None:
    print("MiniMax CLI chat ready. Type 'exit' or 'quit' to stop.")
    messages = []
    cli_agent = Agent(
        AgentConfig(
            workspace=Path.cwd(),
            max_tokens=max_tokens,
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

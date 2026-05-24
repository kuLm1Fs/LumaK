from __future__ import annotations

import argparse

from agent.runtime.loop import agent_loop, response_to_text


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
    messages = [{"role": "user", "content": prompt}]
    response = agent_loop(messages, max_tokens=max_tokens)
    print(response_to_text(response))


def run_chat(max_tokens: int) -> None:
    print("MiniMax CLI chat ready. Type 'exit' or 'quit' to stop.")
    messages: list[dict] = []

    while True:
        prompt = input("you> ").strip()
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": prompt})
        response = agent_loop(messages, max_tokens=max_tokens)
        print(f"assistant> {response_to_text(response)}")


def main() -> None:
    args = build_parser().parse_args()

    if args.prompt:
        run_once(" ".join(args.prompt), max_tokens=args.max_tokens)
        return

    run_chat(max_tokens=args.max_tokens)


if __name__ == "__main__":
    main()

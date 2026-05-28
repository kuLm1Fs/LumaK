from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import tomllib
from typing import Any

from agent.config import AnthropicConfig, DeepSeekConfig, MiniMaxConfig, OpenAIConfig
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from agent.LLM.anthropic_provider import AnthropicProvider
from agent.CLI.app import response_to_text
from agent.LLM.deepseek import DeepSeekProvider
from agent.LLM.minimax import MinimaxProvider
from agent.LLM.openai_compatible import OpenAICompatibleProvider
from agent.memory.store import MemoryStore
from agent.runtime.agent.agent import Agent, AgentConfig
from agent.trace.trace import make_session_id
from gateway.events import EventBroker, LiveEventHook
from gateway.trace_reader import read_trace_events


WORKSPACE = Path.cwd()
MEMORY_ROOT = WORKSPACE / ".memory"
TRACE_ROOT = WORKSPACE / ".trace"
SKILLS_ROOT = WORKSPACE / ".skills"

broker = EventBroker()
session_workspaces: dict[str, Path] = {}


def configure_workspace(raw_workspace: str | None = None) -> Path:
    global WORKSPACE, MEMORY_ROOT, TRACE_ROOT, SKILLS_ROOT

    workspace = resolve_workspace_path(raw_workspace or os.getenv("LUMAK_WORKSPACE", "") or str(Path.cwd()))
    WORKSPACE = workspace
    MEMORY_ROOT, TRACE_ROOT, SKILLS_ROOT = workspace_roots(workspace)
    session_workspaces.clear()
    return workspace


def workspace_for_session(session_id: str) -> Path:
    return session_workspaces.get(session_id, WORKSPACE)


def resolve_workspace_path(raw_path: str) -> Path:
    workspace = Path(raw_path).expanduser().resolve()
    if not workspace.exists():
        raise ValueError(f"workspace does not exist: {workspace}")
    if not workspace.is_dir():
        raise ValueError(f"workspace is not a directory: {workspace}")
    return workspace


def workspace_roots(workspace: Path) -> tuple[Path, Path, Path]:
    return workspace / ".memory", workspace / ".trace", workspace / ".skills"


def workspace_name(workspace: Path) -> str:
    pyproject_path = workspace / "pyproject.toml"
    if pyproject_path.exists():
        try:
            pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            name = pyproject.get("project", {}).get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        except (OSError, tomllib.TOMLDecodeError):
            pass
    return workspace.name


def build_project_detail(workspace: Path | None = None) -> dict[str, Any]:
    workspace = workspace or WORKSPACE
    return {
        "id": "current",
        "name": workspace_name(workspace),
        "path": str(workspace),
        "active": True,
        "memory_root": str(workspace / ".memory"),
        "trace_root": str(workspace / ".trace"),
        "skills_root": str(workspace / ".skills"),
    }


def build_project_list(workspace: Path | None = None) -> list[dict[str, Any]]:
    project = build_project_detail(workspace or WORKSPACE)
    return [
        {
            "id": project["id"],
            "name": project["name"],
            "path": project["path"],
            "active": project["active"],
        }
    ]


def build_request_llm_client(message: dict[str, Any]) -> object | None:
    raw_config = message.get("provider_config")
    if not isinstance(raw_config, dict):
        return None

    provider = str(raw_config.get("provider", "")).strip().lower()
    api_key = str(raw_config.get("api_key", "")).strip()
    model = str(raw_config.get("model", "")).strip()
    base_url = str(raw_config.get("base_url", "")).strip()

    if not provider or not api_key or not model:
        return None

    if provider == "minimax":
        if not base_url:
            return None
        return MinimaxProvider(MiniMaxConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "anthropic":
        return AnthropicProvider(AnthropicConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "openai":
        return OpenAICompatibleProvider(OpenAIConfig(api_key=api_key, base_url=base_url, model_id=model))
    if provider == "deepseek":
        return DeepSeekProvider(DeepSeekConfig(api_key=api_key, base_url=base_url or "https://api.deepseek.com", model_id=model))
    if provider == "custom":
        if not base_url:
            return None
        return OpenAICompatibleProvider(OpenAIConfig(api_key=api_key, base_url=base_url, model_id=model))

    supported = "anthropic, custom, deepseek, minimax, openai"
    raise ValueError(f"Unsupported request provider: {provider}. Supported: {supported}")


def dumps(message: dict[str, Any]) -> str:
    return json.dumps(message, ensure_ascii=False)


async def send_json(websocket: ServerConnection, message: dict[str, Any]) -> None:
    await websocket.send(dumps(message))


def parse_message(raw_message: str | bytes) -> dict[str, Any]:
    if isinstance(raw_message, bytes):
        raw_message = raw_message.decode("utf-8")

    message = json.loads(raw_message)
    if not isinstance(message, dict):
        raise ValueError("websocket message must be a JSON object")
    return message


async def forward_session_events(
    websocket: ServerConnection,
    session_id: str,
    event_queue: asyncio.Queue[dict[str, Any]],
) -> None:
    try:
        while True:
            event = await event_queue.get()
            await send_json(websocket, event)
    except asyncio.CancelledError:
        raise


async def run_chat(websocket: ServerConnection, message: dict[str, Any]) -> None:
    prompt = str(message.get("message", "")).strip()
    if not prompt:
        await send_json(
            websocket,
            {
                "type": "error",
                "error": "message is required",
            },
        )
        return

    session_id = str(message.get("session_id") or make_session_id())
    workspace = workspace_for_session(session_id)
    memory_root, _trace_root, skills_root = workspace_roots(workspace)
    max_tokens = int(message.get("max_tokens") or 1024)
    event_queue = broker.subscribe(session_id)
    forwarder = asyncio.create_task(forward_session_events(websocket, session_id, event_queue))

    await send_json(
        websocket,
        {
            "type": "chat.started",
            "session_id": session_id,
        },
    )

    try:
        memory_store = MemoryStore(memory_root)
        agent = Agent(
            AgentConfig(
                workspace=workspace,
                session_id=session_id,
                max_tokens=max_tokens,
                llm_client=build_request_llm_client(message),
                memory_store=memory_store,
                skills_root=skills_root,
                trace_enabled=True,
                hooks=[LiveEventHook(broker)],
            )
        )

        response = await asyncio.to_thread(
            agent.run,
            [{"role": "user", "content": prompt}],
        )

        await send_json(
            websocket,
            {
                "type": "chat.response",
                "session_id": session_id,
                "answer": response_to_text(response),
            },
        )
    except Exception as exc:
        await send_json(
            websocket,
            {
                "type": "error",
                "session_id": session_id,
                "error": str(exc),
            },
        )
    finally:
        forwarder.cancel()
        broker.unsubscribe(session_id, event_queue)
        await asyncio.gather(forwarder, return_exceptions=True)


async def send_memory(websocket: ServerConnection, message: dict[str, Any]) -> None:
    session_id = str(message.get("session_id") or "")
    if not session_id:
        await send_json(websocket, {"type": "error", "error": "session_id is required"})
        return

    workspace = workspace_for_session(session_id)
    memory_root, _trace_root, _skills_root = workspace_roots(workspace)
    store = MemoryStore(memory_root)
    await send_json(
        websocket,
        {
            "type": "memory.response",
            "session_id": session_id,
            "messages": store.load_messages(session_id),
        },
    )


async def send_conversation_list(websocket: ServerConnection) -> None:
    store = MemoryStore(MEMORY_ROOT)
    await send_json(
        websocket,
        {
            "type": "conversation.list.response",
            "conversations": store.list_sessions(),
        },
    )


async def send_conversation(websocket: ServerConnection, message: dict[str, Any]) -> None:
    session_id = str(message.get("session_id") or "")
    if not session_id:
        await send_json(websocket, {"type": "error", "error": "session_id is required"})
        return

    store = MemoryStore(MEMORY_ROOT)
    await send_json(
        websocket,
        {
            "type": "conversation.response",
            "session_id": session_id,
            "messages": store.load_messages(session_id),
        },
    )


async def send_project_list(websocket: ServerConnection) -> None:
    await send_json(
        websocket,
        {
            "type": "project.list.response",
            "projects": build_project_list(WORKSPACE),
        },
    )


async def send_project(websocket: ServerConnection, message: dict[str, Any]) -> None:
    project_id = str(message.get("project_id") or "current")
    if project_id != "current":
        await send_json(websocket, {"type": "error", "error": f"unknown project_id: {project_id}"})
        return

    await send_json(
        websocket,
        {
            "type": "project.response",
            "project": build_project_detail(WORKSPACE),
        },
    )


async def send_trace(websocket: ServerConnection, message: dict[str, Any]) -> None:
    session_id = str(message.get("session_id") or "")
    if not session_id:
        await send_json(websocket, {"type": "error", "error": "session_id is required"})
        return

    workspace = workspace_for_session(session_id)
    _memory_root, trace_root, _skills_root = workspace_roots(workspace)

    await send_json(
        websocket,
        {
            "type": "trace.response",
            "session_id": session_id,
            "events": read_trace_events(trace_root, session_id),
        },
    )


async def switch_project(websocket: ServerConnection, message: dict[str, Any]) -> None:
    session_id = str(message.get("session_id") or make_session_id())
    path = str(message.get("path") or "").strip()
    if not path:
        await send_json(websocket, {"type": "error", "session_id": session_id, "error": "path is required"})
        return

    try:
        workspace = resolve_workspace_path(path)
    except ValueError as exc:
        await send_json(websocket, {"type": "error", "session_id": session_id, "error": str(exc)})
        return

    session_workspaces[session_id] = workspace
    await send_json(
        websocket,
        {
            "type": "project.switched",
            "session_id": session_id,
            "name": workspace.name,
            "path": str(workspace),
        },
    )


async def handle_message(websocket: ServerConnection, message: dict[str, Any]) -> None:
    message_type = message.get("type")

    if message_type == "chat":
        await run_chat(websocket, message)
    elif message_type == "project.switch":
        await switch_project(websocket, message)
    elif message_type == "conversation.list":
        await send_conversation_list(websocket)
    elif message_type == "conversation.get":
        await send_conversation(websocket, message)
    elif message_type == "project.list":
        await send_project_list(websocket)
    elif message_type == "project.get":
        await send_project(websocket, message)
    elif message_type == "memory.get":
        await send_memory(websocket, message)
    elif message_type == "trace.get":
        await send_trace(websocket, message)
    elif message_type == "ping":
        await send_json(websocket, {"type": "pong"})
    else:
        await send_json(
            websocket,
            {
                "type": "error",
                "error": f"unknown message type: {message_type}",
            },
        )


async def websocket_handler(websocket: ServerConnection) -> None:
    await send_json(websocket, {"type": "gateway.ready"})

    try:
        async for raw_message in websocket:
            try:
                message = parse_message(raw_message)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                await send_json(websocket, {"type": "error", "error": str(exc)})
                continue

            await handle_message(websocket, message)
    except ConnectionClosed:
        return


async def serve_gateway(host: str = "127.0.0.1", port: int = 8765) -> None:
    async with serve(websocket_handler, host, port):
        print(f"LumaK websocket gateway listening on ws://{host}:{port}")
        await asyncio.Future()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the LumaK websocket gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--workspace",
        default=None,
        help="Project directory to use as the default workspace. Defaults to LUMAK_WORKSPACE or the current directory.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    configure_workspace(args.workspace)
    asyncio.run(serve_gateway(host=args.host, port=args.port))


if __name__ == "__main__":
    main()

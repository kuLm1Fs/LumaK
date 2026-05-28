from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socket
import subprocess
import sys
import sysconfig
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence


HELP = """LumaK

Usage:
  lumak [prompt...]
  lumak cli [prompt...]
  lumak gateway [options]
  lumak tui [options]
  lumak web

Commands:
  cli       Run the Python CLI. This is also the default when no subcommand is given.
  gateway   Run the WebSocket gateway.
  tui       Run the TypeScript terminal UI.
  web       Run the Web UI and gateway dev server.

Run "lumak <command> --help" for command-specific options.
"""


@contextmanager
def patched_argv(argv: Sequence[str]) -> Iterator[None]:
    original = sys.argv[:]
    sys.argv = list(argv)
    try:
        yield
    finally:
        sys.argv = original


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def tui_entrypoint() -> Path | None:
    candidates = [
        project_root() / "tui" / "dist" / "index.js",
        Path(sys.prefix) / "share" / "lumak" / "tui" / "dist" / "index.js",
        Path(sysconfig.get_path("data")) / "share" / "lumak" / "tui" / "dist" / "index.js",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def web_dist_dir() -> Path | None:
    candidates = [
        project_root() / "web" / "dist",
        Path(sys.prefix) / "share" / "lumak" / "web" / "dist",
        Path(sysconfig.get_path("data")) / "share" / "lumak" / "web" / "dist",
    ]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        return probe.connect_ex((host, port)) == 0


def run_cli(args: Sequence[str]) -> int:
    from agent.CLI.app import main as cli_main

    with patched_argv(["lumak", *args]):
        cli_main()
    return 0


def run_gateway(args: Sequence[str]) -> int:
    from gateway.app import main as gateway_main

    with patched_argv(["lumak gateway", *args]):
        gateway_main()
    return 0


def run_tui(args: Sequence[str]) -> int:
    node = shutil.which("node")
    if node is None:
        print("error: node is required to run `lumak tui`", file=sys.stderr)
        return 127

    tui_entry = tui_entrypoint()
    if tui_entry is None:
        print(
            "error: TypeScript TUI is not built. Run `cd tui && npm run build` first.",
            file=sys.stderr,
        )
        return 1

    return subprocess.call([node, str(tui_entry), *args])


def run_web(args: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="lumak web", description="Run the LumaK Web UI and gateway.")
    parser.add_argument("--host", default="127.0.0.1", help="Web UI host. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=4173, help="Web UI port. Default: 4173")
    parser.add_argument("--gateway-host", default="127.0.0.1", help="Gateway host. Default: 127.0.0.1")
    parser.add_argument("--gateway-port", type=int, default=8765, help="Gateway port. Default: 8765")
    parser.add_argument("--workspace", default=str(Path.cwd()), help="Gateway workspace. Default: cwd")
    parsed = parser.parse_args(list(args))

    web_root = web_dist_dir()
    if web_root is None:
        print("error: Web UI is not built. Run `cd web && npm run build` first.", file=sys.stderr)
        return 1

    gateway: subprocess.Popen[bytes] | None = None
    if is_port_open(parsed.gateway_host, parsed.gateway_port):
        print(f"[gateway] reusing existing server on ws://{parsed.gateway_host}:{parsed.gateway_port}")
    else:
        gateway = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "gateway.app",
                "--host",
                parsed.gateway_host,
                "--port",
                str(parsed.gateway_port),
                "--workspace",
                parsed.workspace,
            ]
        )

    if is_port_open(parsed.host, parsed.port):
        print(f"[web] reusing existing server on http://{parsed.host}:{parsed.port}")
        if gateway is None:
            return 0
        try:
            gateway.wait()
        except KeyboardInterrupt:
            pass
        finally:
            gateway.terminate()
        return 0

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(web_root))
    server = http.server.ThreadingHTTPServer((parsed.host, parsed.port), handler)
    print("LumaK web server")
    print(f"  Web UI:  http://{parsed.host}:{parsed.port}")
    print(f"  Gateway: ws://{parsed.gateway_host}:{parsed.gateway_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if gateway is not None:
            gateway.terminate()
            gateway.wait(timeout=5)
    return 0


def dispatch(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if args and args[0] in {"-h", "--help", "help"}:
        print(HELP)
        return 0

    if not args:
        return run_cli([])

    command, command_args = args[0], args[1:]
    if command == "cli":
        return run_cli(command_args)
    if command == "gateway":
        return run_gateway(command_args)
    if command == "tui":
        return run_tui(command_args)
    if command == "web":
        return run_web(command_args)

    return run_cli(args)


def main() -> None:
    raise SystemExit(dispatch())


if __name__ == "__main__":
    main()

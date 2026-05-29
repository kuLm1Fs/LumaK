import { spawn } from "node:child_process";
import { execFileSync } from "node:child_process";
import net from "node:net";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(webRoot, "..");
const gatewayHost = "127.0.0.1";
const gatewayPort = 8765;
const webHost = "127.0.0.1";
const webPort = 4173;

let shuttingDown = false;
const children = [];

function isPortOpen(host, port) {
  return new Promise((resolvePort) => {
    const socket = net.createConnection({ host, port });
    socket.once("connect", () => {
      socket.destroy();
      resolvePort(true);
    });
    socket.once("error", () => {
      resolvePort(false);
    });
  });
}

function isPortListed(port) {
  try {
    execFileSync("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN"], {
      stdio: "ignore",
    });
    return true;
  } catch {
    return false;
  }
}

function startProcess({ name, command, args, cwd }) {
  const child = spawn(command, args, {
    cwd,
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout.on("data", (chunk) => {
    process.stdout.write(`[${name}] ${chunk}`);
  });
  child.stderr.on("data", (chunk) => {
    process.stderr.write(`[${name}] ${chunk}`);
  });
  child.on("exit", (code, signal) => {
    if (shuttingDown) {
      return;
    }
    console.error(`[${name}] exited with ${signal ?? code}`);
    shutdown(code === null ? 1 : code);
  });

  children.push(child);
  return child;
}

function shutdown(exitCode = 0) {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  for (const child of children) {
    if (!child.killed) {
      child.kill("SIGTERM");
    }
  }
  process.exitCode = exitCode;
}

process.on("SIGINT", () => shutdown());
process.on("SIGTERM", () => shutdown());

console.log("LumaK dev server");
console.log(`  Web UI:  http://${webHost}:${webPort}`);
console.log(`  Gateway: ws://${gatewayHost}:${gatewayPort}`);

const gatewayAlreadyRunning = isPortListed(gatewayPort) || (await isPortOpen(gatewayHost, gatewayPort));
if (gatewayAlreadyRunning) {
  console.log(`[gateway] reusing existing server on ws://${gatewayHost}:${gatewayPort}`);
} else {
  startProcess({
    name: "gateway",
    command: "uv",
    args: ["run", "python", "-m", "gateway.app"],
    cwd: repoRoot,
  });
}

const webAlreadyRunning = isPortListed(webPort) || (await isPortOpen(webHost, webPort));
if (webAlreadyRunning) {
  console.log(`[web] reusing existing server on http://${webHost}:${webPort}`);
} else {
  startProcess({
    name: "web",
    command: "npm",
    args: ["run", "start", "--", "--strictPort"],
    cwd: webRoot,
  });
}

if (children.length === 0) {
  console.log("Both dev servers are already running.");
}

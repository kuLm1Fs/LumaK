import { Buffer } from "node:buffer";
import { createHash, randomBytes } from "node:crypto";
import { createConnection, type Socket } from "node:net";

type MessageListener = (message: string) => void;
type CloseListener = () => void;

export class SimpleWebSocketClient {
  private socket: Socket | null = null;
  private buffer = Buffer.alloc(0);
  private messageListeners = new Set<MessageListener>();
  private closeListeners = new Set<CloseListener>();

  static connect(rawUrl: string, timeoutMs = 500): Promise<SimpleWebSocketClient> {
    const client = new SimpleWebSocketClient();
    return client.connect(rawUrl, timeoutMs);
  }

  onMessage(listener: MessageListener): void {
    this.messageListeners.add(listener);
  }

  onClose(listener: CloseListener): void {
    this.closeListeners.add(listener);
  }

  send(message: string): void {
    if (!this.socket) {
      throw new Error("websocket is not connected");
    }
    this.socket.write(encodeClientFrame(message));
  }

  close(): void {
    this.socket?.end();
    this.socket = null;
  }

  private connect(rawUrl: string, timeoutMs: number): Promise<SimpleWebSocketClient> {
    return new Promise((resolve, reject) => {
      const url = new URL(rawUrl);
      if (url.protocol !== "ws:") {
        reject(new Error(`unsupported websocket protocol: ${url.protocol}`));
        return;
      }

      const port = Number.parseInt(url.port || "80", 10);
      const path = `${url.pathname || "/"}${url.search}`;
      const key = randomBytes(16).toString("base64");
      const socket = createConnection({ host: url.hostname, port });
      let handshakeBuffer = Buffer.alloc(0);
      let settled = false;

      const timer = setTimeout(() => {
        socket.destroy();
        reject(new Error(`connection timed out: ${rawUrl}`));
      }, timeoutMs);

      socket.once("connect", () => {
        socket.write(
          [
            `GET ${path} HTTP/1.1`,
            `Host: ${url.host}`,
            "Upgrade: websocket",
            "Connection: Upgrade",
            `Sec-WebSocket-Key: ${key}`,
            "Sec-WebSocket-Version: 13",
            "\r\n",
          ].join("\r\n"),
        );
      });

      socket.on("data", (chunk: Buffer) => {
        if (!settled) {
          handshakeBuffer = Buffer.concat([handshakeBuffer, chunk]);
          const headerEnd = handshakeBuffer.indexOf("\r\n\r\n");
          if (headerEnd === -1) {
            return;
          }
          const header = handshakeBuffer.slice(0, headerEnd).toString("utf8");
          const rest = handshakeBuffer.slice(headerEnd + 4);
          const expectedAccept = createHash("sha1")
            .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
            .digest("base64");
          if (!header.startsWith("HTTP/1.1 101") || !header.includes(`Sec-WebSocket-Accept: ${expectedAccept}`)) {
            clearTimeout(timer);
            socket.destroy();
            reject(new Error(`websocket handshake failed: ${header.split("\r\n")[0] || "no response"}`));
            return;
          }
          settled = true;
          clearTimeout(timer);
          this.socket = socket;
          socket.on("close", () => this.emitClose());
          if (rest.length > 0) {
            this.receive(rest);
          }
          resolve(this);
          return;
        }
        this.receive(chunk);
      });

      socket.once("error", (error: Error) => {
        if (!settled) {
          clearTimeout(timer);
          reject(error);
        }
      });
    });
  }

  private receive(chunk: Buffer): void {
    this.buffer = Buffer.concat([this.buffer, chunk]);
    while (true) {
      const frame = decodeServerFrame(this.buffer);
      if (!frame) {
        return;
      }
      this.buffer = this.buffer.slice(frame.bytesRead);
      if (frame.opcode === 0x1) {
        this.emitMessage(frame.payload.toString("utf8"));
      } else if (frame.opcode === 0x8) {
        this.close();
        this.emitClose();
        return;
      }
    }
  }

  private emitMessage(message: string): void {
    for (const listener of this.messageListeners) {
      listener(message);
    }
  }

  private emitClose(): void {
    for (const listener of this.closeListeners) {
      listener();
    }
  }
}

function encodeClientFrame(message: string): Buffer {
  const payload = Buffer.from(message, "utf8");
  const mask = randomBytes(4);
  const headerLength = payload.length < 126 ? 6 : payload.length <= 0xffff ? 8 : 14;
  const frame = Buffer.alloc(headerLength + payload.length);
  frame[0] = 0x81;
  if (payload.length < 126) {
    frame[1] = 0x80 | payload.length;
    mask.copy(frame, 2);
    writeMaskedPayload(frame, payload, mask, 6);
  } else if (payload.length <= 0xffff) {
    frame[1] = 0x80 | 126;
    frame.writeUInt16BE(payload.length, 2);
    mask.copy(frame, 4);
    writeMaskedPayload(frame, payload, mask, 8);
  } else {
    frame[1] = 0x80 | 127;
    frame.writeBigUInt64BE(BigInt(payload.length), 2);
    mask.copy(frame, 10);
    writeMaskedPayload(frame, payload, mask, 14);
  }
  return frame;
}

function writeMaskedPayload(frame: Buffer, payload: Buffer, mask: Buffer, offset: number): void {
  for (let index = 0; index < payload.length; index += 1) {
    frame[offset + index] = payload[index] ^ mask[index % 4];
  }
}

function decodeServerFrame(buffer: Buffer): { opcode: number; payload: Buffer; bytesRead: number } | null {
  if (buffer.length < 2) {
    return null;
  }
  const opcode = buffer[0] & 0x0f;
  let payloadLength = buffer[1] & 0x7f;
  let offset = 2;
  if (payloadLength === 126) {
    if (buffer.length < 4) {
      return null;
    }
    payloadLength = buffer.readUInt16BE(2);
    offset = 4;
  } else if (payloadLength === 127) {
    if (buffer.length < 10) {
      return null;
    }
    const bigLength = buffer.readBigUInt64BE(2);
    if (bigLength > BigInt(Number.MAX_SAFE_INTEGER)) {
      throw new Error("websocket frame is too large");
    }
    payloadLength = Number(bigLength);
    offset = 10;
  }
  const masked = (buffer[1] & 0x80) !== 0;
  const maskOffset = masked ? offset : -1;
  if (masked) {
    offset += 4;
  }
  if (buffer.length < offset + payloadLength) {
    return null;
  }
  let payload = buffer.slice(offset, offset + payloadLength);
  if (masked) {
    const mask = buffer.slice(maskOffset, maskOffset + 4);
    const unmasked = Buffer.alloc(payload.length);
    for (let index = 0; index < payload.length; index += 1) {
      unmasked[index] = payload[index] ^ mask[index % 4];
    }
    payload = unmasked;
  }
  return { opcode, payload, bytesRead: offset + payloadLength };
}

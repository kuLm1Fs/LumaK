export type ProviderConfig = {
  apiKey: string;
  baseUrl?: string;
  model: string;
  provider: string;
};

export type AttachmentText =
  | {
      content: string;
      kind: "text";
      name: string;
    }
  | {
      kind: "unsupported";
      name: string;
      reason: string;
    };

export type ChatPayload = {
  type: "chat";
  message: string;
  session_id: string;
  max_tokens: number;
  provider_config?: {
    api_key: string;
    base_url?: string;
    model: string;
    provider: string;
  };
};

export type ProjectRecord = {
  id: string;
  name: string;
  path?: string;
  updatedAt: number;
};

export function buildGatewayUrl(
  location: Pick<Location, "hostname" | "port" | "protocol" | "search">,
  gatewayPort = 8765,
  overrideUrl?: string | null,
): string {
  const cleanOverrideUrl = overrideUrl?.trim();
  if (cleanOverrideUrl?.startsWith("ws://") || cleanOverrideUrl?.startsWith("wss://")) {
    return cleanOverrideUrl;
  }

  const gatewayParam = new URLSearchParams(location.search).get("gateway")?.trim();
  if (gatewayParam?.startsWith("ws://") || gatewayParam?.startsWith("wss://")) {
    return gatewayParam;
  }

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const localHosts = new Set(["127.0.0.1", "localhost", "::1"]);

  if (localHosts.has(location.hostname)) {
    const host = location.hostname === "::1" ? "[::1]" : location.hostname;
    return `${protocol}//${host}:${gatewayPort}`;
  }

  const codespacesHost = location.hostname.match(/^(.+)-(\d+)\.(app\.github\.dev|githubpreview\.dev)$/);
  if (codespacesHost) {
    return `${protocol}//${codespacesHost[1]}-${gatewayPort}.${codespacesHost[3]}`;
  }

  if (location.port) {
    return `${protocol}//${location.hostname}:${gatewayPort}`;
  }

  return `${protocol}//${location.hostname}`;
}

export function createProjectRecord(
  input: { name: string; path?: string },
  createId: () => string,
  now: () => number = Date.now,
): ProjectRecord {
  const name = input.name.trim() || "未命名项目";
  const path = input.path?.trim();
  const project: ProjectRecord = {
    id: createId(),
    name: name.slice(0, 64),
    updatedAt: now(),
  };

  if (path) {
    project.path = path;
  }

  return project;
}

export function createProjectRecordFromPath(
  path: string,
  createId: () => string,
  now: () => number = Date.now,
): ProjectRecord | null {
  const cleanPath = path.trim();
  if (!cleanPath) {
    return null;
  }

  const segments = cleanPath.split(/[\\/]+/).filter(Boolean);
  const directoryName = segments.at(-1) || cleanPath;
  return createProjectRecord({ name: directoryName, path: cleanPath }, createId, now);
}

export function buildChatPayload(
  message: string,
  sessionId: string,
  providerConfig?: ProviderConfig,
): ChatPayload {
  const payload: ChatPayload = {
    type: "chat",
    message,
    session_id: sessionId,
    max_tokens: 1024,
  };

  if (providerConfig?.apiKey && providerConfig.model && providerConfig.provider) {
    payload.provider_config = {
      api_key: providerConfig.apiKey,
      model: providerConfig.model,
      provider: providerConfig.provider,
    };
    if (providerConfig.baseUrl) {
      payload.provider_config.base_url = providerConfig.baseUrl;
    }
  }

  return payload;
}

export function buildAttachmentPrompt(text: string, attachments: AttachmentText[]): string {
  const readableAttachments = attachments.filter(
    (attachment): attachment is Extract<AttachmentText, { kind: "text" }> => attachment.kind === "text",
  );
  const unsupportedAttachments = attachments.filter(
    (attachment): attachment is Extract<AttachmentText, { kind: "unsupported" }> =>
      attachment.kind === "unsupported",
  );

  const parts: string[] = [text || "请根据附件内容继续处理。"];

  if (readableAttachments.length > 0) {
    parts.push("", "已附加文件：", "");
    readableAttachments.forEach((attachment, index) => {
      if (index > 0) {
        parts.push("");
      }
      parts.push(`### ${attachment.name}`, "```text", attachment.content, "```");
    });
  }

  if (unsupportedAttachments.length > 0) {
    parts.push("", "### 未读取的附件");
    unsupportedAttachments.forEach((attachment) => {
      parts.push(`- ${attachment.name}：${attachment.reason}`);
    });
  }

  return parts.join("\n");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInlineMarkdown(value: string): string {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function renderParagraph(block: string): string {
  const lines = block.split("\n");
  if (lines.every((line) => line.trim().startsWith("- "))) {
    const items = lines
      .map((line) => `<li>${renderInlineMarkdown(line.trim().slice(2))}</li>`)
      .join("");
    return `<ul>${items}</ul>`;
  }

  return `<p>${renderInlineMarkdown(block).replaceAll("\n", "<br>")}</p>`;
}

export function renderMarkdownLite(markdown: string): string {
  const html: string[] = [];
  const fencePattern = /```([A-Za-z0-9_-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = fencePattern.exec(markdown)) !== null) {
    const before = markdown.slice(lastIndex, match.index).trim();
    if (before) {
      html.push(...before.split(/\n{2,}/).filter(Boolean).map(renderParagraph));
    }

    const language = match[1] || "text";
    const code = match[2]?.replace(/\n$/, "") ?? "";
    html.push(
      `<pre class="code-block language-${escapeHtml(language)}"><code>${escapeHtml(code)}</code></pre>`,
    );
    lastIndex = fencePattern.lastIndex;
  }

  const after = markdown.slice(lastIndex).trim();
  if (after) {
    html.push(...after.split(/\n{2,}/).filter(Boolean).map(renderParagraph));
  }

  return html.join("");
}

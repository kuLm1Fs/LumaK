import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({
  gfm: true,
  breaks: true,
});

function sanitize(html: string): string {
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.nodeName === "A" && node.hasAttribute("target")) {
      node.setAttribute("rel", "noopener noreferrer");
    }
  });
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      "h1", "h2", "h3", "h4", "h5", "h6",
      "p", "br", "hr",
      "ul", "ol", "li",
      "blockquote",
      "pre", "code",
      "a", "img",
      "strong", "em", "del", "s",
      "table", "thead", "tbody", "tr", "th", "td",
      "input",
      "span", "div",
    ],
    ALLOWED_ATTR: [
      "href", "src", "alt", "title",
      "class", "id",
      "type", "checked", "disabled",
      "target",
    ],
    ADD_ATTR: ["target"],
    FORCE_BODY: false,
    SANITIZE_DOM: true,
    KEEP_CONTENT: true,
  });
  DOMPurify.removeHook("afterSanitizeAttributes");
  return clean;
}

export function renderMarkdown(markdown: string): string {
  if (!markdown || typeof markdown !== "string") {
    return "";
  }

  const rawHtml = marked.parse(markdown, { async: false }) as string;
  const cleanHtml = sanitize(rawHtml);

  return `<div class="agent-message-content">${cleanHtml}</div>`;
}

/**
 * Add copy button to all code blocks within a container.
 * Call this after rendering markdown to enhance code blocks.
 */
export function addCodeCopyButtons(container: HTMLElement): void {
  container.querySelectorAll<HTMLElement>("pre > code").forEach((codeBlock) => {
    const pre = codeBlock.parentElement;
    if (!pre || pre.querySelector(".copy-code-button")) return;

    const button = document.createElement("button");
    button.className = "copy-code-button";
    button.type = "button";
    button.textContent = "复制";
    button.addEventListener("click", async () => {
      const code = codeBlock.textContent ?? "";
      try {
        await navigator.clipboard.writeText(code);
        button.textContent = "已复制";
        setTimeout(() => {
          button.textContent = "复制";
        }, 1200);
      } catch {
        button.textContent = "复制失败";
      }
    });
    pre.style.position = "relative";
    pre.append(button);
  });
}

/**
 * Create a renderer function for use in message bubbles.
 * Returns HTML string and also attaches copy buttons to the container.
 */
export function createMarkdownRenderer() {
  return function renderToHtml(markdown: string): { html: string; attachCopyButtons: (container: HTMLElement) => void } {
    const html = renderMarkdown(markdown);
    return {
      html,
      attachCopyButtons: (container: HTMLElement) => {
        addCodeCopyButtons(container);
      },
    };
  };
}
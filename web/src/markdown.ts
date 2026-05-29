/**
 * Markdown rendering utilities using marked + DOMPurify.
 * 
 * Supports full CommonMark + GFM (GitHub Flavored Markdown):
 * - Headings (# ## ### etc.)
 * - Bold, italic, strikethrough
 * - Links [text](url)
 * - Images ![alt](url)
 * - Code blocks with syntax highlighting class
 * - Tables
 * - Task lists
 * - Blockquotes
 * - Inline code
 */

import { marked } from "marked";
import DOMPurify from "dompurify";

// Configure marked for GFM support
marked.setOptions({
  gfm: true,
  breaks: true,
});

/**
 * Render markdown string to sanitized HTML.
 * 
 * @param markdown - Raw markdown text
 * @returns Sanitized HTML string safe for innerHTML
 */
export function renderMarkdown(markdown: string): string {
  if (!markdown || typeof markdown !== "string") {
    return "";
  }

  // Convert markdown to HTML
  const rawHtml = marked.parse(markdown, { async: false }) as string;

  // Sanitize to prevent XSS attacks
  // DOMPurify requires DOM context in browser, returns string
  const cleanHtml = DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: [
      "h1", "h2", "h3", "h4", "h5", "h6",
      "p", "br", "hr",
      "ul", "ol", "li",
      "blockquote",
      "pre", "code",
      "a", "img",
      "strong", "em", "del", "s",
      "table", "thead", "tbody", "tr", "th", "td",
      "input", // for task lists
      "span", "div",
    ],
    ALLOWED_ATTR: [
      "href", "src", "alt", "title",
      "class", "id",
      "type", "checked", "disabled", // for task list checkboxes
      "target", "rel",
    ],
    // Force all links to open in new tab safely
    ADD_ATTR: ["target"],
    FORCE_BODY: false,
    // Prevent DOM clobbering
    SANITIZE_DOM: true,
    KEEP_CONTENT: true,
  });

  return cleanHtml;
}

/**
 * Add copy button to all code blocks within a container.
 * Call this after rendering markdown to enhance code blocks.
 */
export function addCodeCopyButtons(container: HTMLElement): void {
  container.querySelectorAll<HTMLElement>("pre.code-block").forEach((block) => {
    // Check if button already exists
    if (block.querySelector(".copy-code-button")) {
      return;
    }

    const button = document.createElement("button");
    button.className = "copy-code-button";
    button.type = "button";
    button.textContent = "复制";
    button.addEventListener("click", async () => {
      const code = block.querySelector("code")?.textContent ?? "";
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
    block.append(button);
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
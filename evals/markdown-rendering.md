# Evaluation: Web Frontend Markdown Rendering Enhancement

## Problem

The web frontend (`web/`) renders AI assistant responses via `renderMarkdownLite()` in `web/src/app-utils.ts:212`. This is a hand-rolled, regex-based renderer that supports only a limited subset of Markdown:

**Supported:**
- HTML escaping (XSS protection)
- Fenced code blocks with language hint
- Inline code `` `code` ``
- Bold `**text**`
- Unordered lists (`- item`)
- Paragraph wrapping and `<br>` line breaks

**Missing (commonly produced by LLMs):**
- Headings (`#` through `######`)
- Links `[text](url)`
- Italic `*text*` / `_text_`
- Blockquotes (`>`)
- Ordered lists (`1. item`)
- Tables
- Strikethrough (`~~text~~`)
- Task lists (`- [ ]`)
- Horizontal rules (`---`)

Since the project is a chat UI for an AI coding assistant (LumaK), the LLM frequently emits rich Markdown that is silently dropped or rendered as plaintext, degrading readability.

The rendering entry point in `web/src/app.ts:471`:
```ts
bubble.innerHTML = renderMarkdownLite(message.text);
```

Tests exist in `web/tests/app-utils.test.mjs:135` with one test case covering HTML escaping + fenced code blocks.

---

## lumaK's Proposed Approach

Source: lumaK (AI coding assistant included in this project), via interactive chat.

### Investigation Summary

lumaK correctly identified the relevant file and function. It searched for `renderMarkdown` patterns, located `renderMarkdownLite`, and enumerated supported vs. unsupported features.

### Proposed Options

**Option A — Extend `renderMarkdownLite` in-place**
- Add regex-based parsing for each missing construct (headings, links, italic, blockquotes, ordered lists, tables, etc.)
- Keep modular: each feature as a separate function/regex
- Maintain `escapeHtml` for XSS protection
- Prioritize backward compatibility with existing output

**Option B — Introduce a library** (`marked` or `markdown-it`)
- Full GFM support out of the box
- Adds an npm dependency
- Trade-off: more bytes vs. less maintenance

### Design Principles Mentioned
1. Modularity — features decoupled for maintainability
2. Security — continue using `escapeHtml`
3. Performance — avoid unnecessary regex matching
4. Backward compatibility — don't break existing output format

lumaK then asked the user to choose between Option A and B before proceeding.

---

## Evaluation

### What lumaK Did Well

1. **Correct localization**: Accurately identified `web/src/app-utils.ts:212` and the helper `renderParagraph` + `renderInlineMarkdown`.
2. **Accurate feature audit**: The list of supported vs. missing features is correct and complete for practical LLM output.
3. **Sensible design principles**: The four principles (modularity, security, performance, backward compat) are all relevant and well-stated for a chat rendering pipeline.
4. **Appropriate hesitation**: Asking for user confirmation before changing code is good practice in an interactive coding agent.

### Issues & Omissions

1. **Misidentified `frontend/` directory**: Claimed there is a React frontend under `frontend/` with `react-markdown`. No such directory exists in this project. This indicates the file search was not verified against actual directory listings.

2. **Did not examine the test file**: The test at `web/tests/app-utils.test.mjs:135` covers `renderMarkdownLite`. Any change needs corresponding test updates. lumaK did not reference the existing test or discuss test strategy.

3. **No CSS analysis**: The stylesheet (`web/styles.css`) styles `.bubble p`, `.bubble ul`, `.bubble code`, and `.code-block` but has zero styles for headings, blockquotes, tables, or other new elements. Adding markdown features without corresponding CSS produces unstyled/unreadable output. This was not flagged.

4. **Weak `innerHTML` security analysis**: The code uses `bubble.innerHTML = renderMarkdownLite(...)` (line 471). The existing `escapeHtml` guard is only as good as the regex coverage. As more regex paths are added, the risk of a bypass grows. Switching to a battle-tested library with built-in sanitization (e.g., `dompurify` + `marked`) would be more secure. lumaK did not raise this.

5. **Option analysis is superficial**: Presenting Option A vs. B without context of the project's constraints:
   - The project already uses **Vite** (v7) with npm, so adding dependencies is trivial.
   - The bundle currently has zero runtime dependencies (only `typescript` and `vite` as devDeps). Adding `marked` (~15KB gzipped) or `markdown-it` (~20KB) is a modest cost for eliminating an entire class of regex bugs.
   - LLM output is unpredictable; a standards-compliant parser is more robust than any regex-based one.
   - A hand-rolled parser will need continuous maintenance as new markdown edge cases appear.
   - Recommendation should have favored Option B with reasoning, not just a neutral presentation.

6. **No consideration of the rendering pipeline**: Did not trace how the LLM response arrives at `renderMarkdownLite`. The `web/src/gateway-contract.ts` (message types) and the chat flow in `web/src/app.ts` were not examined. Future changes (e.g., streaming markdown rendering) require understanding this pipeline.

7. **No discussion of streaming**: LLM responses are often streamed token-by-token. The current implementation renders after the full message is received. lumaK did not consider whether the new renderer needs to support incremental rendering.

8. **Missing ordered list detection in `renderParagraph`**: The current code already has a heuristic for unordered lists (`lines.every(line => line.trim().startsWith("- "))`) but this is not extensible. Adding ordered list support would require modifying this heuristic, which lumaK did not flag.

---

### Recommendation

**Adopt Option B (library-based) with the following specifics:**

- Use **`marked`** with GFM extension (lightest, most popular, well-tested, supports all needed features)
- Wrap with a thin adapter in `app-utils.ts` (e.g., `renderMarkdown(text) => marked.parse(text)`) for testability
- Add **`dompurify`** for sanitization before `innerHTML` assignment
- Add corresponding **CSS rules** in `styles.css` for headings, blockquotes, tables, ordered lists, and code block edge cases
- **Update the test** to cover the new features (headings, links, blockquotes, tables)
- Keep `renderMarkdownLite` as a fallback for non-critical contexts or as a sync-only path if marked proves too heavy for the bundle

This trades ~20KB of bundle size for correctness, security, and zero ongoing maintenance burden.

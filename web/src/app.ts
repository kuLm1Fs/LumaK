function getElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) {
    throw new Error(`Required UI element is missing: ${selector}`);
  }

  return element;
}

const fileInput = getElement<HTMLInputElement>("#fileInput");
const attachmentRow = getElement<HTMLDivElement>("#attachmentRow");
const promptInput = getElement<HTMLTextAreaElement>("#promptInput");
const composer = getElement<HTMLFormElement>(".composer");
const messages = getElement<HTMLElement>(".messages");
const assistantAvatarSrc = "./assets/lumak-logo.png";

const selectedFiles: File[] = [];

function renderAttachments(): void {
  attachmentRow.innerHTML = "";
  attachmentRow.hidden = selectedFiles.length === 0;

  selectedFiles.forEach((file) => {
    const chip = document.createElement("div");
    chip.className = "attachment-chip";

    const icon = document.createElement("strong");
    icon.textContent = file.type.startsWith("image/") ? "IMG" : "FILE";

    const name = document.createElement("span");
    name.textContent = file.name;

    chip.append(icon, name);
    attachmentRow.append(chip);
  });
}

function appendMessage(text: string, role: "assistant" | "user"): void {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  if (role === "assistant") {
    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = assistantAvatarSrc;
    avatar.alt = "";
    avatar.setAttribute("aria-hidden", "true");
    article.append(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  bubble.append(paragraph);
  article.append(bubble);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function resizePrompt(): void {
  promptInput.style.height = "auto";
  promptInput.style.height = `${promptInput.scrollHeight}px`;
}

fileInput.addEventListener("change", () => {
  selectedFiles.splice(0, selectedFiles.length, ...Array.from(fileInput.files ?? []));
  renderAttachments();
});

promptInput.addEventListener("input", resizePrompt);

composer.addEventListener("submit", (event) => {
  event.preventDefault();

  const text = promptInput.value.trim();
  if (!text && selectedFiles.length === 0) {
    return;
  }

  const fileSummary =
    selectedFiles.length > 0
      ? `（已附加 ${selectedFiles.length} 个文件：${selectedFiles.map((file) => file.name).join("、")}）`
      : "";

  appendMessage(`${text || "已上传文件"}${fileSummary}`, "user");
  promptInput.value = "";
  selectedFiles.length = 0;
  fileInput.value = "";
  renderAttachments();
  resizePrompt();
});

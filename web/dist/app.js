"use strict";
function getElement(selector) {
    const element = document.querySelector(selector);
    if (!element) {
        throw new Error(`Required UI element is missing: ${selector}`);
    }
    return element;
}
const fileInput = getElement("#fileInput");
const attachmentRow = getElement("#attachmentRow");
const promptInput = getElement("#promptInput");
const composer = getElement(".composer");
const messages = getElement(".messages");
const providerForm = getElement("#providerForm");
const providerSelect = getElement("#providerSelect");
const apiKeyInput = getElement("#apiKeyInput");
const modelSelect = getElement("#modelSelect");
const customModelField = getElement("#customModelField");
const customModelInput = getElement("#customModelInput");
const providerState = getElement("#providerState");
const providerDialog = getElement("#providerDialog");
const openProviderDialog = getElement("#openProviderDialog");
const closeProviderDialog = getElement("#closeProviderDialog");
const assistantAvatarSrc = "./assets/lumak-logo.png";
const selectedFiles = [];
const providerStorageKey = "lumak.providerConfig";
const customModelOptions = ["custom"];
const modelOptions = {
    minimax: ["MiniMax-M2.7", "abab6.5s-chat", "custom"],
    anthropic: ["claude-sonnet-4-5", "claude-opus-4-1", "custom"],
    openai: ["gpt-5.1", "gpt-5.1-mini", "custom"],
    deepseek: ["deepseek-chat", "deepseek-reasoner", "custom"],
    custom: customModelOptions,
};
function maskApiKey(apiKey) {
    if (apiKey.length <= 8) {
        return "已保存";
    }
    return `${apiKey.slice(0, 4)}...${apiKey.slice(-4)}`;
}
function getProviderLabel(provider) {
    return providerSelect.querySelector(`option[value="${provider}"]`)?.textContent ?? provider;
}
function setModelOptions(provider, selectedModel) {
    const options = modelOptions[provider] ?? customModelOptions;
    modelSelect.innerHTML = "";
    options.forEach((model) => {
        const option = document.createElement("option");
        option.value = model;
        option.textContent = model === "custom" ? "Custom model" : model;
        modelSelect.append(option);
    });
    if (selectedModel && options.includes(selectedModel)) {
        modelSelect.value = selectedModel;
    }
    else if (selectedModel) {
        modelSelect.value = "custom";
        customModelInput.value = selectedModel;
    }
    updateCustomModelVisibility();
}
function updateCustomModelVisibility() {
    const needsCustomModel = modelSelect.value === "custom" || providerSelect.value === "custom";
    customModelField.hidden = !needsCustomModel;
}
function renderProviderState(config) {
    if (!config) {
        providerState.textContent = "未配置";
        return;
    }
    providerState.textContent = `${getProviderLabel(config.provider)} · ${config.model} · ${maskApiKey(config.apiKey)}`;
}
function loadProviderConfig() {
    const rawConfig = window.localStorage.getItem(providerStorageKey);
    setModelOptions(providerSelect.value);
    if (!rawConfig) {
        return;
    }
    const config = JSON.parse(rawConfig);
    providerSelect.value = config.provider;
    apiKeyInput.value = config.apiKey;
    setModelOptions(config.provider, config.model);
    renderProviderState(config);
}
function renderAttachments() {
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
function appendMessage(text, role) {
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
function resizePrompt() {
    promptInput.style.height = "auto";
    promptInput.style.height = `${promptInput.scrollHeight}px`;
}
fileInput.addEventListener("change", () => {
    selectedFiles.splice(0, selectedFiles.length, ...Array.from(fileInput.files ?? []));
    renderAttachments();
});
promptInput.addEventListener("input", resizePrompt);
openProviderDialog.addEventListener("click", () => {
    providerDialog.showModal();
});
closeProviderDialog.addEventListener("click", () => {
    providerDialog.close();
});
providerDialog.addEventListener("click", (event) => {
    if (event.target === providerDialog) {
        providerDialog.close();
    }
});
providerSelect.addEventListener("change", () => {
    setModelOptions(providerSelect.value);
});
modelSelect.addEventListener("change", () => {
    updateCustomModelVisibility();
    if (modelSelect.value === "custom" && !providerDialog.open) {
        providerDialog.showModal();
        customModelInput.focus();
    }
});
providerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const apiKey = apiKeyInput.value.trim();
    const model = modelSelect.value === "custom" ? customModelInput.value.trim() : modelSelect.value;
    if (!apiKey || !model) {
        renderProviderState();
        return;
    }
    const config = {
        apiKey,
        model,
        provider: providerSelect.value,
    };
    window.localStorage.setItem(providerStorageKey, JSON.stringify(config));
    renderProviderState(config);
    providerDialog.close();
});
composer.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = promptInput.value.trim();
    if (!text && selectedFiles.length === 0) {
        return;
    }
    const fileSummary = selectedFiles.length > 0
        ? `（已附加 ${selectedFiles.length} 个文件：${selectedFiles.map((file) => file.name).join("、")}）`
        : "";
    appendMessage(`${text || "已上传文件"}${fileSummary}`, "user");
    promptInput.value = "";
    selectedFiles.length = 0;
    fileInput.value = "";
    renderAttachments();
    resizePrompt();
});
loadProviderConfig();

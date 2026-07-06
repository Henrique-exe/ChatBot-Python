const messagesEl = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const clearButton = document.querySelector("#clearButton");
let suggestions = document.querySelector("#suggestions");
const sendButton = form.querySelector("button");

const emptyMessage =
  "Opa, sua mensagem veio em branco. Me diga se deseja calcular desconto, confirmar pagamento ou consultar formas de pagamento.";

const labels = {
  bot: "Financeiro",
  user: "Você",
  system: "Sistema",
};

const initials = {
  bot: "FF",
  user: "VC",
  system: "!",
};

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(sender, text) {
  const article = document.createElement("article");
  article.className = `message ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = initials[sender] || "FF";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const label = document.createElement("span");
  label.textContent = labels[sender] || "Financeiro";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  bubble.append(label, paragraph);
  article.append(avatar, bubble);
  messagesEl.append(article);
  scrollToBottom();
}

function buildSuggestions() {
  const section = document.createElement("section");
  section.className = "suggestions";
  section.id = "suggestions";
  section.setAttribute("aria-label", "Sugestões de teste");
  section.innerHTML = `
    <span>Experimente:</span>
    <p>Calcular 10% de desconto em R$ 150,00</p>
    <p>Confirmar pagamento por CPF</p>
    <p>Consultar formas de pagamento</p>
  `;
  return section;
}

function hideSuggestions() {
  suggestions?.classList.add("is-hidden");
}

function showSuggestions() {
  suggestions?.classList.remove("is-hidden");
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  sendButton.textContent = isLoading ? "Enviando..." : "Enviar";
}

async function postJson(url, payload = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

async function sendMessage(message, echoUser = true) {
  const text = message.trim();
  if (!text) {
    addMessage("system", emptyMessage);
    return;
  }

  hideSuggestions();
  if (echoUser) {
    addMessage("user", text);
  }

  setLoading(true);
  try {
    const data = await postJson("/api/message", { message: text });
    const replies = data.messages || [];
    replies.forEach((item) => addMessage(item.sender || "bot", item.text || ""));
  } catch (error) {
    addMessage("system", "Oxente, tive uma instabilidade aqui na tela. Tente novamente em instantes.");
  } finally {
    setLoading(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value;
  input.value = "";
  sendMessage(text);
});

document.querySelectorAll(".quick-action[data-message]").forEach((button) => {
  button.addEventListener("click", () => {
    button.classList.add("is-active");
    window.setTimeout(() => button.classList.remove("is-active"), 220);
    sendMessage(button.dataset.message);
  });
});

clearButton.addEventListener("click", async () => {
  setLoading(true);
  try {
    const data = await postJson("/api/clear");
    messagesEl.innerHTML = "";
    (data.messages || []).forEach((item) => addMessage(item.sender || "bot", item.text || ""));
    suggestions = buildSuggestions();
    messagesEl.append(suggestions);
    showSuggestions();
    scrollToBottom();
  } catch (error) {
    addMessage("system", "Não consegui limpar a conversa agora. Tente novamente em instantes.");
  } finally {
    setLoading(false);
    input.focus();
  }
});

input.focus();

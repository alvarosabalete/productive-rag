// Frontend mínimo. En la Fase 0 solo comprueba /api/health.
// El chat real (con auth + RAG) se conecta en fases posteriores.

const API = "/api";

async function checkHealth() {
  const el = document.getElementById("health");
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    el.textContent = `${data.status} (${data.environment})`;
  } catch {
    el.textContent = "no disponible";
  }
}

document.getElementById("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = document.getElementById("question");
  const q = input.value.trim();
  if (!q) return;
  addMessage(q, "user");
  input.value = "";
  // TODO (Fase 2/3): POST /api/chat con el token JWT.
  addMessage("El chat se habilitará al implementar el RAG y la autenticación.", "bot");
});

function addMessage(text, who) {
  const chat = document.getElementById("chat");
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

checkHealth();

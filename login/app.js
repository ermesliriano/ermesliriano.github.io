// CONFIG
const API_BASE = "https://TU_BACKEND.example.com"; // cambia al dominio real

const out = document.getElementById("out");
const loginForm = document.getElementById("loginForm");

function log(obj) {
  out.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
}

function setTokens({ access_token, refresh_token }) {
  sessionStorage.setItem("access_token", access_token);
  sessionStorage.setItem("refresh_token", refresh_token);
}

function clearTokens() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}

function authHeader() {
  const t = sessionStorage.getItem("access_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function postJSON(path, body) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

// EMAIL/PASSWORD: register + login
document.getElementById("registerBtn").addEventListener("click", async () => {
  const email = loginForm.email.value;
  const password = loginForm.password.value;
  try {
    const r = await postJSON("/api/auth/register", { email, password });
    log({ register: "ok", r });
  } catch (e) {
    log({ register: "error", message: e.message });
  }
});

loginForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const email = loginForm.email.value;
  const password = loginForm.password.value;
  try {
    const tokens = await postJSON("/api/auth/login", { email, password });
    setTokens(tokens);
    log({ login: "ok", tokens: { ...tokens, refresh_token: "***" } });
  } catch (e) {
    log({ login: "error", message: e.message });
  }
});

// GOOGLE (GIS): recibe credential (ID token JWT)
window.handleCredentialResponse = async (response) => {
  try {
    const tokens = await postJSON("/api/auth/google", { credential: response.credential });
    setTokens(tokens);
    log({ google: "ok", tokens: { ...tokens, refresh_token: "***" } });
  } catch (e) {
    log({ google: "error", message: e.message });
  }
};

window.onload = function () {
  // Inicializa GIS y pinta botón
  google.accounts.id.initialize({
    client_id: "TU_GOOGLE_WEB_CLIENT_ID.apps.googleusercontent.com",
    callback: handleCredentialResponse,
  });
  google.accounts.id.renderButton(
    document.getElementById("gsiButton"),
    { theme: "outline", size: "large" }
  );
};

// /me y logout
document.getElementById("meBtn").addEventListener("click", async () => {
  try {
    const r = await fetch(`${API_BASE}/api/users/me`, { headers: authHeader() });
    const data = await r.json();
    log(data);
  } catch (e) {
    log({ me: "error", message: e.message });
  }
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  const refresh_token = sessionStorage.getItem("refresh_token");
  if (!refresh_token) return clearTokens();
  try {
    await postJSON("/api/auth/logout", refresh_token);
  } catch (_) {}
  clearTokens();
  log("logout ok");
});
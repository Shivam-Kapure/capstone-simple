// All requests are same-origin; nginx forwards /api and /health to the backend.
const $ = (id) => document.getElementById(id);

async function api(path, options) {
  const res = await fetch(path, options);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join("; ") : body.detail;
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return body;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function loadHealth() {
  const el = $("health");
  try {
    const h = await api("/health");
    el.textContent = `Backend ${h.status} (v${h.version})`;
    el.className = "badge ok";
  } catch (e) {
    el.textContent = `Backend unreachable: ${e.message}`;
    el.className = "badge err";
  }
}

async function loadPayments() {
  const tbody = $("payments");
  try {
    const payments = await api("/api/payments");
    $("stat-count").textContent = payments.length;
    $("stat-completed").textContent = payments.filter((p) => p.status === "COMPLETED").length;
    $("stat-other").textContent = payments.filter((p) => p.status !== "COMPLETED").length;
    tbody.innerHTML = payments.length
      ? payments.map((p) => `<tr><td>${p.id}</td><td>${escapeHtml(p.payer)}</td><td>${escapeHtml(p.payee)}</td>
          <td>${escapeHtml(p.amount)} ${p.currency}</td><td><span class="status ${p.status}">${p.status}</span></td></tr>`).join("")
      : `<tr><td colspan="5">No payments yet.</td></tr>`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="error">Could not load payments: ${escapeHtml(e.message)}</td></tr>`;
  }
}

async function loadNotifications() {
  const ul = $("notifications");
  try {
    const items = await api("/api/notifications");
    ul.innerHTML = items.length
      ? items.map((n) => `<li>${escapeHtml(n.message)} <small>${n.created_at}</small></li>`).join("")
      : "<li>No notifications.</li>";
  } catch (e) {
    ul.innerHTML = `<li class="error">Could not load notifications: ${escapeHtml(e.message)}</li>`;
  }
}

$("pay-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = $("form-msg");
  const data = Object.fromEntries(new FormData(ev.target));
  try {
    const p = await api("/api/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    msg.textContent = `Payment #${p.id} created.`;
    msg.className = "msg ok";
    ev.target.reset();
    refresh();
  } catch (e) {
    msg.textContent = `Rejected: ${e.message}`;
    msg.className = "msg error";
  }
});

function refresh() {
  loadHealth();
  loadPayments();
  loadNotifications();
}

refresh();
setInterval(refresh, 15000);

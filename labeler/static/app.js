const API = "/api";

const LABELS = [
  { key: "benchmark_claim", num: "1" },
  { key: "data_quality_skepticism", num: "2" },
  { key: "architecture_analysis", num: "3" },
  { key: "trace_methodology", num: "4" },
  { key: "hype_or_reaction", num: "5" },
];

let currentItem = null;
let selectedLabel = null;
let statsTimer = null;

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res;
}

function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.style.borderColor = isError ? "var(--danger)" : "var(--border)";
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3000);
}

function showPage(name) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll("#nav button").forEach((b) => b.classList.remove("active"));
  document.getElementById(`page-${name}`).classList.add("active");
  document.querySelector(`#nav button[data-page="${name}"]`).classList.add("active");
  if (name === "annotate") loadNextItem();
  if (name === "admin") loadAdmin();
}

function fillLabelSelects() {
  const selects = [
    document.getElementById("admin-label"),
    document.querySelector("#edit-form select[name=label]"),
  ];
  selects.forEach((sel) => {
    if (!sel) return;
    const isAdmin = sel.id === "admin-label";
    sel.innerHTML = isAdmin
      ? '<option value="">All labels</option>'
      : '<option value="">—</option>';
    LABELS.forEach(({ key }) => {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = key;
      sel.appendChild(opt);
    });
  });
}

function renderLabelButtons() {
  const container = document.getElementById("label-buttons");
  container.innerHTML = "";
  LABELS.forEach(({ key, num }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = `${num}. ${key}`;
    btn.dataset.label = key;
    btn.onclick = () => selectLabel(key);
    container.appendChild(btn);
  });
}

function selectLabel(label) {
  selectedLabel = label;
  document.querySelectorAll("#label-buttons button").forEach((btn) => {
    btn.classList.toggle("selected", btn.dataset.label === label);
  });
}

async function refreshStats() {
  try {
    const s = await api("/stats");
    const grid = document.getElementById("stats-grid");
    grid.innerHTML = `
      <div class="stat-card"><div class="value">${s.total}</div><div class="label">Total</div></div>
      <div class="stat-card"><div class="value">${s.labeled}</div><div class="label">Labeled</div></div>
      <div class="stat-card"><div class="value">${s.unlabeled}</div><div class="label">Unlabeled</div></div>
      <div class="stat-card"><div class="value">${s.progress_percent}%</div><div class="label">Progress</div></div>
    `;
    const bars = document.getElementById("label-bars");
    const max = Math.max(1, ...Object.values(s.by_label));
    bars.innerHTML = LABELS.map(({ key }) => {
      const count = s.by_label[key] || 0;
      const pct = (count / max) * 100;
      return `<div class="label-bar">
        <span class="name">${key}</span>
        <div class="bar"><div class="fill" style="width:${pct}%"></div></div>
        <span class="count">${count}</span>
      </div>`;
    }).join("");
  } catch (e) {
    console.error(e);
  }
}

async function loadNextItem(afterId = 0) {
  try {
    const item = await api(`/items/next?after_id=${afterId}`);
    const empty = document.getElementById("annotate-empty");
    const panel = document.getElementById("annotate-panel");
    if (!item) {
      currentItem = null;
      empty.classList.remove("hidden");
      panel.classList.add("hidden");
      return;
    }
    currentItem = item;
    selectedLabel = null;
    empty.classList.add("hidden");
    panel.classList.remove("hidden");
    document.getElementById("annotate-text").textContent = item.text;
    document.getElementById("annotate-notes").value = item.notes || "";
    const url = item.source_url
      ? `<a href="${item.source_url}" target="_blank" rel="noopener">${item.source_url}</a>`
      : "—";
    document.getElementById("annotate-meta").innerHTML =
      `#${item.id} · ${item.community || "—"} · score ${item.score ?? "—"} · ${url}`;
    document.querySelectorAll("#label-buttons button").forEach((b) => b.classList.remove("selected"));
  } catch (e) {
    toast(e.message, true);
  }
}

async function saveAnnotation(status = "labeled") {
  if (!currentItem) return;
  if (status === "labeled" && !selectedLabel) {
    toast("Pick a label first (keys 1–5)", true);
    return;
  }
  const notes = document.getElementById("annotate-notes").value;
  const body = {
    notes,
    status,
    label: status === "labeled" ? selectedLabel : null,
  };
  try {
    await api(`/items/${currentItem.id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    toast(status === "skip" ? "Skipped" : `Labeled: ${selectedLabel}`);
    await loadNextItem(currentItem.id);
    refreshStats();
  } catch (e) {
    toast(e.message, true);
  }
}

async function loadAdmin() {
  const status = document.getElementById("admin-status").value;
  const label = document.getElementById("admin-label").value;
  const search = document.getElementById("admin-search").value;
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (label) params.set("label", label);
  if (search) params.set("search", search);
  try {
    const items = await api(`/items?${params}`);
    const tbody = document.getElementById("admin-tbody");
    tbody.innerHTML = items.map((item) => `
      <tr>
        <td>${item.id}</td>
        <td>${item.status}</td>
        <td>${item.label || "—"}</td>
        <td class="text-cell" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</td>
        <td>${item.community || "—"}</td>
        <td>
          <button class="btn secondary" data-edit="${item.id}">Edit</button>
          <button class="btn danger" data-del="${item.id}">Delete</button>
        </td>
      </tr>
    `).join("");
    tbody.querySelectorAll("[data-edit]").forEach((btn) => {
      btn.onclick = () => openEdit(Number(btn.dataset.edit), items);
    });
    tbody.querySelectorAll("[data-del]").forEach((btn) => {
      btn.onclick = () => deleteItem(Number(btn.dataset.del));
    });
  } catch (e) {
    toast(e.message, true);
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

function openEdit(id, items) {
  const item = items.find((i) => i.id === id);
  if (!item) return;
  document.getElementById("edit-id").textContent = id;
  const form = document.getElementById("edit-form");
  form.querySelector("[name=text]").value = item.text;
  form.querySelector("[name=label]").value = item.label || "";
  form.querySelector("[name=status]").value = item.status;
  form.querySelector("[name=notes]").value = item.notes || "";
  form.querySelector("[name=source_url]").value = item.source_url || "";
  form.querySelector("[name=community]").value = item.community || "";
  form.dataset.itemId = id;
  document.getElementById("edit-dialog").showModal();
}

async function deleteItem(id) {
  if (!confirm(`Delete item #${id}?`)) return;
  try {
    await api(`/items/${id}`, { method: "DELETE" });
    toast("Deleted");
    loadAdmin();
    refreshStats();
  } catch (e) {
    toast(e.message, true);
  }
}

async function previewImport() {
  const content = document.getElementById("import-content").value;
  const format = document.getElementById("import-format").value;
  try {
    const res = await api("/items/bulk", {
      method: "POST",
      body: JSON.stringify({ content, format, dry_run: true }),
    });
    document.getElementById("import-preview").textContent =
      JSON.stringify(res, null, 2);
  } catch (e) {
    toast(e.message, true);
  }
}

async function runImport() {
  const content = document.getElementById("import-content").value;
  const format = document.getElementById("import-format").value;
  try {
    const res = await api("/items/bulk", {
      method: "POST",
      body: JSON.stringify({ content, format, dry_run: false }),
    });
    toast(`Imported ${res.inserted} items`);
    document.getElementById("import-content").value = "";
    document.getElementById("import-preview").textContent = "";
    refreshStats();
  } catch (e) {
    toast(e.message, true);
  }
}

document.getElementById("nav").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-page]");
  if (btn) showPage(btn.dataset.page);
});

document.getElementById("save-next-btn").onclick = () => saveAnnotation("labeled");
document.getElementById("skip-btn").onclick = () => saveAnnotation("skip");
document.getElementById("preview-btn").onclick = previewImport;
document.getElementById("import-btn").onclick = runImport;
document.getElementById("admin-refresh").onclick = loadAdmin;
document.getElementById("admin-search").oninput = debounce(loadAdmin, 300);
document.getElementById("admin-status").onchange = loadAdmin;
document.getElementById("admin-label").onchange = loadAdmin;

document.getElementById("dedupe-btn").onclick = async () => {
  try {
    const res = await api("/deduplicate?remove=false", { method: "POST" });
    document.getElementById("dedupe-result").textContent =
      `Duplicate text groups: ${res.duplicate_text_groups}, URL groups: ${res.duplicate_url_groups}. ` +
      `Run with remove=true via API to delete duplicates.`;
  } catch (e) {
    toast(e.message, true);
  }
};

document.getElementById("single-form").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api("/items", {
      method: "POST",
      body: JSON.stringify({
        text: fd.get("text"),
        source_url: fd.get("source_url") || null,
        community: fd.get("community") || null,
        platform: fd.get("platform"),
      }),
    });
    toast("Item added");
    e.target.reset();
    refreshStats();
  } catch (err) {
    toast(err.message, true);
  }
};

document.getElementById("edit-form").onsubmit = async (e) => {
  e.preventDefault();
  const id = e.target.dataset.itemId;
  const fd = new FormData(e.target);
  const label = fd.get("label") || null;
  const status = fd.get("status");
  if (status === "labeled" && !label) {
    toast("Labeled status requires a label", true);
    return;
  }
  try {
    await api(`/items/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        text: fd.get("text"),
        label,
        status,
        notes: fd.get("notes") || null,
        source_url: fd.get("source_url") || null,
        community: fd.get("community") || null,
      }),
    });
    document.getElementById("edit-dialog").close();
    toast("Saved");
    loadAdmin();
    refreshStats();
  } catch (err) {
    toast(err.message, true);
  }
};

document.addEventListener("keydown", (e) => {
  const annotateActive = document.getElementById("page-annotate").classList.contains("active");
  if (!annotateActive || !currentItem) return;
  if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") {
    if (e.key === "Enter" && e.metaKey) saveAnnotation("labeled");
    return;
  }
  const map = { "1": 0, "2": 1, "3": 2, "4": 3, "5": 4 };
  if (map[e.key] !== undefined) {
    selectLabel(LABELS[map[e.key]].key);
    e.preventDefault();
  }
  if (e.key === "s" || e.key === "S") {
    saveAnnotation("skip");
    e.preventDefault();
  }
  if (e.key === "Enter") {
    saveAnnotation("labeled");
    e.preventDefault();
  }
});

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

fillLabelSelects();
renderLabelButtons();
refreshStats();
statsTimer = setInterval(refreshStats, 1500);

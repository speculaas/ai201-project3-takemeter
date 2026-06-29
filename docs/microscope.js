let state = {
  index: [],
  session: null,
  activeTab: "overview"
};

function $(id) {
  return document.getElementById(id);
}

function setDetail(value) {
  $("detail-json").textContent = JSON.stringify(value, null, 2);
}

function card(label, value) {
  return `<div class="card"><div class="muted">${label}</div><div>${value ?? ""}</div></div>`;
}

function renderOverview(session) {
  const api = session.api_reconstruction || TraceModel.reconstructApiCandidate(session.events || []);
  const blocks = session.content_blocks || TraceModel.flattenContentBlocks(session.events || []);
  return `
    <div class="cards">
      ${card("session_id", session.session_id)}
      ${card("model", api.model || "unknown")}
      ${card("thinkingLevel", api.thinkingLevel || "unknown")}
      ${card("num_events", (session.events || []).length)}
      ${card("num_messages", (session.messages || []).length)}
      ${card("content_blocks", blocks.length)}
    </div>
    <div class="panel" style="margin-top:16px">
      <h3>Missing API fields</h3>
      <ul>${(api.missing_fields || []).map((item) => `<li>${item}</li>`).join("")}</ul>
    </div>
  `;
}

function renderTranscript(session) {
  const messages = session.messages || TraceModel.flattenMessages(session.events || []);
  return `<div class="transcript">
    ${messages
      .map(
        (msg) => `
      <div class="panel transcript-item" data-json='${JSON.stringify(msg).replace(/'/g, "&apos;")}'>
        <div><span class="badge">${msg.role || "unknown"}</span>${(msg.content_types || [])
          .map((type) => `<span class="badge">${type}</span>`)
          .join("")}</div>
        <p>${msg.text_preview || ""}</p>
      </div>`
      )
      .join("")}
  </div>`;
}

function renderBlocks(session) {
  const blocks = session.content_blocks || TraceModel.flattenContentBlocks(session.events || []);
  return `<div class="blocks">
    ${blocks
      .map(
        (block) => `
      <div class="block block-item" data-json='${JSON.stringify(block).replace(/'/g, "&apos;")}'>
        <div><span class="badge">${block.role || "unknown"}</span><span class="badge">${block.block_type}</span></div>
        <pre>${block.text || block.thinking || JSON.stringify(block.toolCall || block.raw, null, 2)}</pre>
      </div>`
      )
      .join("")}
  </div>`;
}

function renderMermaid(session) {
  const mermaid = session.mermaid || {};
  const flowchart = mermaid.flowchart || TraceModel.generateMermaidFlowchart(session);
  const gitGraph = mermaid.gitGraph || TraceModel.generateMermaidGitGraph(session);
  const sequence = mermaid.sequenceDiagram || TraceModel.generateMermaidSequence(session);
  return `
    <div class="panel">
      <h3>Flowchart</h3>
      <pre>${flowchart}</pre>
      <div class="mermaid">${flowchart}</div>
    </div>
    <div class="panel" style="margin-top:16px">
      <h3>GitGraph</h3>
      <pre>${gitGraph}</pre>
      <div class="mermaid">${gitGraph}</div>
    </div>
    <div class="panel" style="margin-top:16px">
      <h3>Sequence</h3>
      <pre>${sequence}</pre>
      <div class="mermaid">${sequence}</div>
    </div>
  `;
}

function renderRaw(session) {
  return `<div class="panel"><pre>${JSON.stringify(session, null, 2)}</pre></div>`;
}

function renderApi(session) {
  const api = session.api_reconstruction || TraceModel.reconstructApiCandidate(session.events || []);
  return `
    <div class="panel">
      <h3>Confidence: ${api.confidence || "partial"}</h3>
      <p><strong>model:</strong> ${api.model || "unknown"}</p>
      <p><strong>thinkingLevel:</strong> ${api.thinkingLevel || "unknown"}</p>
      <h4>Candidate messages</h4>
      <pre>${JSON.stringify(api.messages_candidate || [], null, 2)}</pre>
      <h4>Notes</h4>
      <ul>${(api.notes || []).map((note) => `<li>${note}</li>`).join("")}</ul>
    </div>
  `;
}

function renderMain() {
  const panel = $("main-panel");
  if (!state.session) {
    panel.innerHTML = `<div class="panel">No session selected.</div>`;
    return;
  }

  if (state.activeTab === "overview") panel.innerHTML = renderOverview(state.session);
  if (state.activeTab === "transcript") panel.innerHTML = renderTranscript(state.session);
  if (state.activeTab === "blocks") panel.innerHTML = renderBlocks(state.session);
  if (state.activeTab === "mermaid") panel.innerHTML = renderMermaid(state.session);
  if (state.activeTab === "raw") panel.innerHTML = renderRaw(state.session);
  if (state.activeTab === "api") panel.innerHTML = renderApi(state.session);

  panel.querySelectorAll("[data-json]").forEach((node) => {
    node.addEventListener("click", () => {
      const payload = JSON.parse(node.dataset.json.replace(/&apos;/g, "'"));
      setDetail(payload);
    });
  });

  if (window.mermaid) {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
    window.mermaid.run({ nodes: panel.querySelectorAll(".mermaid") }).catch(() => {});
  }
}

function renderSessionList(items) {
  $("session-list").innerHTML = items
    .map(
      (item) => `
      <button class="session-item ${state.session && state.session.session_id === item.session_id ? "active" : ""}" data-session="${item.session_id}">
        <strong>${item.session_id}</strong><br />
        <span class="muted">${item.model || "unknown"} · ${item.thinkingLevel || "unknown"}</span>
      </button>
    `
    )
    .join("");

  document.querySelectorAll(".session-item[data-session]").forEach((node) => {
    node.addEventListener("click", async () => {
      state.session = await TraceModel.loadSession(node.dataset.session);
      renderSessionList(state.index);
      renderMain();
      setDetail(state.session);
    });
  });
}

async function init() {
  state.index = await TraceModel.loadIndex();
  state.session = await TraceModel.loadSession(state.index[0].session_id);
  renderSessionList(state.index);
  renderMain();
  setDetail(state.session);

  $("session-search").addEventListener("input", (event) => {
    const q = event.target.value.toLowerCase();
    const filtered = state.index.filter((item) =>
      [item.session_id, item.model, item.thinkingLevel].join(" ").toLowerCase().includes(q)
    );
    renderSessionList(filtered);
  });

  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      state.activeTab = button.dataset.tab;
      renderMain();
    });
  });

  $("download-json").addEventListener("click", () => {
    TraceModel.downloadJson(`${state.session.session_id}.json`, state.session);
  });

  $("download-flowchart").addEventListener("click", () => {
    const text =
      (state.session.mermaid && state.session.mermaid.flowchart) ||
      TraceModel.generateMermaidFlowchart(state.session);
    TraceModel.downloadText(`${state.session.session_id}.flowchart.mmd`, text);
  });

  $("copy-session-id").addEventListener("click", async () => {
    await navigator.clipboard.writeText(state.session.session_id);
  });
}

init().catch((error) => {
  $("main-panel").innerHTML = `<div class="panel"><h3>Failed to load microscope</h3><pre>${error.stack || error.message}</pre></div>`;
});

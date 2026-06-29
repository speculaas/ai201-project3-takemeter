// Fable trace utilities for a static GitHub Pages microscope.
// The HF pi_agent dataset is event-level, so these helpers build session-ish views.

(function () {
  function textPreview(value, maxLen = 160) {
    if (value == null) return "";
    const text = typeof value === "string" ? value : JSON.stringify(value);
    return text.length > maxLen ? `${text.slice(0, maxLen)}...` : text;
  }

  async function fetchJson(url) {
    const resp = await fetch(url);
    if (!resp.ok) {
      throw new Error(`Failed to fetch ${url}: ${resp.status} ${resp.statusText}`);
    }
    return resp.json();
  }

  async function loadIndex(url = "fable/sessions.index.json") {
    return fetchJson(url);
  }

  async function loadSession(sessionPathOrId) {
    const isPath = sessionPathOrId.includes("/") || sessionPathOrId.endsWith(".json");
    const path = isPath
      ? sessionPathOrId
      : `fable/sessions/${sessionPathOrId}.json`;
    return fetchJson(path);
  }

  function buildIdMaps(events) {
    const byId = {};
    const childrenByParent = {};
    for (const event of events || []) {
      if (event && event.id) {
        byId[event.id] = event;
      }
      const parent = event ? event.parentId : null;
      const key = parent || "__root__";
      if (!childrenByParent[key]) childrenByParent[key] = [];
      childrenByParent[key].push(event);
    }
    return {
      byId,
      childrenByParent,
      roots: childrenByParent.__root__ || []
    };
  }

  function flattenMessages(events) {
    return (events || [])
      .filter((event) => event && event.type === "message" && event.message)
      .map((event) => {
        const content = Array.isArray(event.message.content) ? event.message.content : [];
        return {
          event_id: event.id,
          parentId: event.parentId,
          role: event.message.role || null,
          content_types: content.map((block) => block.type || "unknown"),
          text_preview: textPreview(
            content.map((block) => block.text || block.thinking || JSON.stringify(block)).join(" ")
          ),
          full_content: content
        };
      });
  }

  function flattenContentBlocks(events) {
    const rows = [];
    for (const event of events || []) {
      if (!event || event.type !== "message" || !event.message) continue;
      const content = Array.isArray(event.message.content) ? event.message.content : [];
      content.forEach((block, index) => {
        rows.push({
          event_id: event.id,
          role: event.message.role || null,
          block_index: index,
          block_type: block.type || "unknown",
          text: block.text || null,
          thinking: block.thinking || null,
          toolCall: block.type === "toolCall" ? block : null,
          raw: block
        });
      });
    }
    return rows;
  }

  function reconstructApiCandidate(events) {
    const messages = flattenMessages(events);
    const modelEvent = (events || []).find((event) => event && event.type === "model_change" && event.modelId);
    const thinkingEvent = (events || []).find(
      (event) => event && event.type === "thinking_level_change" && event.thinkingLevel
    );
    return {
      confidence: "partial",
      model: modelEvent ? modelEvent.modelId : null,
      thinkingLevel: thinkingEvent ? thinkingEvent.thinkingLevel : null,
      messages_candidate: messages.map(({ role, full_content }) => ({ role, content: full_content })),
      missing_fields: [
        "max_tokens",
        "cache_control",
        "exact system",
        "exact tools schema",
        "temperature/top_p"
      ],
      notes: [
        "Reconstructed from event rows only.",
        "Treat this as an interpretive API candidate, not a ground-truth request."
      ]
    };
  }

  function generateMermaidFlowchart(sessionPackage) {
    const events = sessionPackage.events || [];
    const lines = ["flowchart TD"];
    for (const event of events) {
      const safeId = String(event.id || "unknown").replace(/[^a-zA-Z0-9_]/g, "_");
      const label = String(event.type || "event").replace(/"/g, "'");
      lines.push(`  ${safeId}["${label}"]`);
      if (event.parentId) {
        const parentId = String(event.parentId).replace(/[^a-zA-Z0-9_]/g, "_");
        lines.push(`  ${parentId} --> ${safeId}`);
      }
    }
    return lines.join("\n");
  }

  function generateMermaidGitGraph(sessionPackage) {
    const lines = ["gitGraph"];
    for (const event of sessionPackage.events || []) {
      const id = String(event.type || "event").replace(/[^a-zA-Z0-9_]/g, "_");
      lines.push(`  commit id:"${id}"`);
    }
    return lines.join("\n");
  }

  function generateMermaidSequence(sessionPackage) {
    const messages = flattenMessages(sessionPackage.events || []);
    const lines = ["sequenceDiagram", "  participant U as User", "  participant A as Assistant", "  participant T as Tool"];
    for (const msg of messages) {
      const preview = textPreview(msg.text_preview, 80).replace(/"/g, "'");
      if (msg.role === "user") {
        lines.push(`  U->>A: ${preview}`);
      } else if (msg.content_types.includes("toolCall")) {
        lines.push(`  A->>T: ${preview}`);
      } else {
        lines.push(`  A-->>U: ${preview}`);
      }
    }
    return lines.join("\n");
  }

  function downloadText(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadJson(filename, obj) {
    downloadText(filename, `${JSON.stringify(obj, null, 2)}\n`);
  }

  window.TraceModel = {
    loadIndex,
    loadSession,
    buildIdMaps,
    flattenMessages,
    flattenContentBlocks,
    reconstructApiCandidate,
    generateMermaidFlowchart,
    generateMermaidGitGraph,
    generateMermaidSequence,
    downloadText,
    downloadJson
  };
})();

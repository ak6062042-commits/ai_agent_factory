(() => {
  const app = document.querySelector("#app");
  const toastRegion = document.querySelector("#toast-region");
  const config = window.APP_CONFIG || {};
  const API = config.API_BASE_URL || "http://127.0.0.1:8001";
  const KEY_STORAGE = "agent-factory-api-key";
  const state = {
    apiKey: localStorage.getItem(KEY_STORAGE) || "",
    agents: [],
    detail: null,
    messages: [],
    sessionId: "",
    polling: null,
    selectedFiles: []
  };

  const icon = (name, size = 18) => {
    const paths = {
      spark: '<path d="m12 3-1.6 5.4L5 10l5.4 1.6L12 17l1.6-5.4L19 10l-5.4-1.6L12 3Z"/><path d="m5 3-.6 2.4L2 6l2.4.6L5 9l.6-2.4L8 6l-2.4-.6L5 3Z"/>',
      plus: '<path d="M12 5v14M5 12h14"/>',
      arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
      copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"/>',
      logout: '<path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 19h7a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-7"/>',
      document: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
      globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
      trash: '<path d="M3 6h18M8 6V4h8v2m-9 0 1 15h8l1-15M10 10v7M14 10v7"/>',
      refresh: '<path d="M20 11a8 8 0 1 0 2 5"/><path d="M20 4v7h-7"/>',
      send: '<path d="m22 2-7 20-4-9-9-4 20-7Z"/><path d="m22 2-11 11"/>',
      close: '<path d="m6 6 12 12M18 6 6 18"/>',
      chevron: '<path d="m6 9 6 6 6-6"/>'
    };
    return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || ""}</svg>`;
  };

  const escape = (value = "") => String(value).replace(/[&<>"']/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;" }[char]));
  const formatDate = value => value ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value)) : "—";
  const sourceIcon = type => icon(type === "website" ? "globe" : "document", 16);
  const status = value => `<span class="status status-${escape(value || "processing")}"><i></i>${escape(value || "processing")}</span>`;
  const uuid = () => crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

  function toast(message, kind = "success") {
    const el = document.createElement("div");
    el.className = `toast ${kind}`;
    el.textContent = message;
    toastRegion.append(el);
    setTimeout(() => el.remove(), 4200);
  }

  async function request(path, options = {}, needsKey = true) {
    const headers = new Headers(options.headers || {});
    if (needsKey && state.apiKey) headers.set("X-API-Key", state.apiKey);
    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    let response;
    try {
      response = await fetch(`${API}${path}`, { ...options, headers });
    } catch {
      throw new Error(`Cannot reach the API at ${API}. Check that the backend is running.`);
    }
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data.detail || data.message || `Request failed (${response.status})`;
      const error = new Error(typeof message === "string" ? message : JSON.stringify(message));
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function setKey(key) {
    state.apiKey = key.trim();
    localStorage.setItem(KEY_STORAGE, state.apiKey);
  }
  function clearPolling() { if (state.polling) clearInterval(state.polling); state.polling = null; }
  function navigate(hash) { clearPolling(); window.location.hash = hash; }
  function currentRoute() { return window.location.hash.replace(/^#/, "") || (state.apiKey ? "/dashboard" : "/"); }

  function appShell(content, active = "") {
    return `<aside class="sidebar">
      <a class="brand" href="#/dashboard">${icon("spark", 22)}<span>Agent<span>Factory</span></span></a>
      <div class="tenant-scope"><span class="scope-dot"></span><span>Tenant workspace</span></div>
      <nav><a class="nav-link ${active === "dashboard" ? "active" : ""}" href="#/dashboard"><span class="nav-glyph">⌘</span>All agents</a><a class="nav-link ${active === "new" ? "active" : ""}" href="#/agents/new">${icon("plus", 18)}Create agent</a></nav>
      <div class="sidebar-bottom"><div class="key-state"><span class="key-label">Connected with API key</span><code>••••••••${escape(state.apiKey.slice(-4))}</code></div><button class="quiet-button" id="disconnect">${icon("logout", 17)}Disconnect</button></div>
    </aside><main class="main-content">${content}</main>`;
  }

  function landing() {
    clearPolling();
    app.innerHTML = `<div class="entry-layout"><section class="entry-brand"><a class="brand light" href="#/">${icon("spark", 23)}<span>Agent<span>Factory</span></span></a><div class="entry-copy"><p class="eyebrow">MULTI-TENANT RAG PLATFORM</p><h1>Turn your knowledge into an agent people can trust.</h1><p>Build grounded AI agents from your website and documents, with clear source attribution in every answer.</p></div><div class="feature-list"><div>${icon("globe", 18)}<span><b>Scoped by design</b>Your content stays inside your workspace.</span></div><div>${icon("document", 18)}<span><b>Source-grounded</b>Every response brings its evidence.</span></div></div><small>Agent Factory · Your private knowledge layer</small></section><section class="entry-panel"><div class="entry-form" id="entry-form"><p class="eyebrow">GET STARTED</p><h2>Build your first agent.</h2><p class="muted">Create a tenant workspace, then bring your knowledge to life.</p><form id="signup-form"><label>Organization name<input required name="organization_name" placeholder="Acme, Inc." autocomplete="organization" /></label><label>Admin email<input required type="email" name="admin_email" placeholder="you@company.com" autocomplete="email" /></label><button class="primary wide" type="submit">Create workspace ${icon("arrow", 17)}</button></form><div class="or"><span></span>or<span></span></div><button class="text-button" id="show-key">I already have an API key</button><form id="key-form" class="hidden"><label>API key<input required name="api_key" placeholder="Paste your key here" autocomplete="off" /></label><p class="helper">Stored locally in this browser only. It is never synced.</p><button class="secondary wide" type="submit">Enter workspace ${icon("arrow", 17)}</button></form></div></section></div>`;
    document.querySelector("#signup-form").addEventListener("submit", createTenant);
    document.querySelector("#show-key").addEventListener("click", () => document.querySelector("#key-form").classList.toggle("hidden"));
    document.querySelector("#key-form").addEventListener("submit", enterKey);
  }

  async function createTenant(event) {
    event.preventDefault(); const form = event.currentTarget; const button = form.querySelector("button");
    button.disabled = true; button.textContent = "Creating workspace…";
    try { const data = await request("/tenants", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(form))) }, false); showNewKey(data); }
    catch (error) { toast(error.message, "error"); button.disabled = false; button.innerHTML = `Create workspace ${icon("arrow", 17)}`; }
  }
  function enterKey(event) { event.preventDefault(); setKey(new FormData(event.currentTarget).get("api_key")); navigate("#/dashboard"); }
  function showNewKey(tenant) {
    app.querySelector(".entry-form").innerHTML = `<p class="eyebrow success-copy">WORKSPACE CREATED</p><h2>Save your API key.</h2><p class="muted">This is the only time we can show it. Copy it now and keep it somewhere secure.</p><div class="key-reveal"><code>${escape(tenant.api_key)}</code><button class="icon-button" id="copy-key" title="Copy API key">${icon("copy", 18)}</button></div><div class="key-warning"><strong>One-time secret</strong><span>Once you leave this screen, this key cannot be shown again.</span></div><button class="primary wide" id="continue-key">I’ve saved my key ${icon("arrow", 17)}</button>`;
    document.querySelector("#copy-key").addEventListener("click", async () => { await navigator.clipboard.writeText(tenant.api_key); toast("API key copied to clipboard."); });
    document.querySelector("#continue-key").addEventListener("click", () => { setKey(tenant.api_key); navigate("#/dashboard"); });
  }

  async function dashboard() {
    app.innerHTML = appShell(`<header class="page-header"><div><p class="eyebrow">WORKSPACE</p><h1>Your agents</h1><p class="muted">Each agent is isolated to this API-key scoped tenant.</p></div><a class="primary" href="#/agents/new">${icon("plus", 17)}New agent</a></header><section id="agents-view" class="agent-grid"><div class="loading-card">Loading your agents…</div></section>`, "dashboard"); bindShell();
    try { state.agents = await request("/agents"); renderAgents(); } catch (error) { renderError("agents-view", error.message); }
  }
  function renderAgents() {
    const target = document.querySelector("#agents-view");
    if (!state.agents.length) { target.className = "empty-state"; target.innerHTML = `<div class="empty-icon">${icon("spark", 26)}</div><h2>Your factory is ready.</h2><p>Create an agent and give it a website plus documents to begin grounding responses in your own knowledge.</p><a class="primary" href="#/agents/new">${icon("plus", 17)}Create your first agent</a>`; return; }
    target.className = "agent-grid";
    target.innerHTML = state.agents.map(agent => `<a class="agent-card" href="#/agents/${encodeURIComponent(agent.agent_id)}"><div class="agent-card-top"><div class="agent-avatar">${escape((agent.agent_name || "A").slice(0, 1).toUpperCase())}</div>${status(agent.ingestion_status)}</div><h2>${escape(agent.agent_name)}</h2><div class="agent-stats"><span>${sourceIcon("document")} ${agent.sources?.length || 0} sources</span><span>${escape(agent.indexed_chunk_count ?? 0)} chunks</span></div><div class="card-footer"><span>Created ${formatDate(agent.created_at)}</span>${icon("arrow", 17)}</div></a>`).join("");
  }

  function createAgentView() {
    state.selectedFiles = [];
    app.innerHTML = appShell(`<header class="page-header compact"><div><a class="back-link" href="#/dashboard">← Back to agents</a><p class="eyebrow">NEW AGENT</p><h1>Give your knowledge a voice.</h1><p class="muted">Connect one website and one or more documents. Ingestion starts as soon as you create the agent.</p></div></header><section class="form-card"><form id="agent-form"><label>Agent name<input required name="agent_name" placeholder="e.g. Acme Support Assistant" maxlength="120" /></label><label>Website URL<input required type="url" name="website_url" placeholder="https://www.example.com" /></label><div class="upload-label">Knowledge documents <span>PDF, DOCX, TXT or CSV</span></div><label class="dropzone" for="documents"><input id="documents" required name="documents" type="file" multiple accept=".pdf,.docx,.txt,.csv" /><span class="upload-icon">${icon("document", 22)}</span><strong>Choose files or drop them here</strong><small>Add one or more files to build this agent’s knowledge base.</small></label><div id="file-chips" class="file-chips"></div><div class="form-actions"><a class="secondary" href="#/dashboard">Cancel</a><button class="primary" type="submit">Create & start ingestion ${icon("arrow", 17)}</button></div></form></section>`, "new"); bindShell();
    document.querySelector("#documents").addEventListener("change", event => { state.selectedFiles = [...event.target.files]; renderFiles(); });
    document.querySelector("#agent-form").addEventListener("submit", submitAgent);
  }
  function renderFiles() {
    const target = document.querySelector("#file-chips");
    target.innerHTML = state.selectedFiles.map((file, index) => `<span class="file-chip">${icon("document", 14)}${escape(file.name)} <small>${Math.ceil(file.size / 1024)} KB</small><button type="button" data-file-index="${index}" title="Remove ${escape(file.name)}">${icon("close", 12)}</button></span>`).join("");
    target.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
      state.selectedFiles.splice(Number(button.dataset.fileIndex), 1);
      const transfer = new DataTransfer(); state.selectedFiles.forEach(file => transfer.items.add(file));
      document.querySelector("#documents").files = transfer.files;
      renderFiles();
    }));
  }
  async function submitAgent(event) { event.preventDefault(); const form = event.currentTarget; const button = form.querySelector("button[type=submit]"); button.disabled = true; button.textContent = "Starting ingestion…"; try { const agent = await request("/agents", { method: "POST", body: new FormData(form) }); navigate(`#/agents/${encodeURIComponent(agent.agent_id)}`); } catch (error) { toast(error.message, "error"); button.disabled = false; button.innerHTML = `Create & start ingestion ${icon("arrow", 17)}`; } }

  async function detail(id) {
    app.innerHTML = appShell(`<div class="loading-detail">Loading agent workspace…</div>`, "dashboard"); bindShell();
    try { state.detail = await request(`/agents/${encodeURIComponent(id)}`); state.messages = []; state.sessionId = uuid(); renderDetail(); if (state.detail.ingestion_status === "processing") beginPolling(id); } catch (error) { app.querySelector(".main-content").innerHTML = `<div class="inline-error"><h2>We couldn’t load this agent.</h2><p>${escape(error.message)}</p><a class="secondary" href="#/dashboard">Back to dashboard</a></div>`; }
  }
  function renderDetail() {
    const agent = state.detail;
    app.querySelector(".main-content").innerHTML = `<header class="detail-header"><div><a class="back-link" href="#/dashboard">← All agents</a><div class="title-line"><h1>${escape(agent.agent_name)}</h1>${status(agent.ingestion_status)}</div><p class="muted">Created ${formatDate(agent.created_at)} · ${agent.indexed_chunk_count || 0} indexed chunks</p></div><button class="danger-button" id="delete-agent">${icon("trash", 16)}Delete agent</button></header>${agent.failure_reason ? `<div class="failure-banner"><strong>Ingestion needs attention</strong><span>${escape(agent.failure_reason)}</span></div>` : ""}<div class="detail-grid"><section class="knowledge-panel"><div class="panel-heading"><div><p class="eyebrow">KNOWLEDGE BASE</p><h2>Sources <span>${agent.sources?.length || 0}</span></h2></div></div><div class="source-list">${(agent.sources || []).length ? agent.sources.map(renderSource).join("") : `<p class="empty-copy">No sources found.</p>`}</div><form id="add-source" class="add-source"><label>Add more knowledge</label><div class="add-url"><input name="website_url" type="url" placeholder="https://another-source.com" /><button class="secondary" type="submit">Add URL</button></div><label class="mini-upload">${icon("plus", 15)}<span>Add a document</span><input type="file" name="document" accept=".pdf,.docx,.txt,.csv" /></label></form><details class="prompt-panel"><summary><span><span class="prompt-mark">{ }</span>Generated system prompt</span>${icon("chevron", 17)}</summary><pre>${escape(agent.system_prompt || "A generated prompt will appear after ingestion.")}</pre></details></section><section class="chat-panel"><div class="chat-top"><div><p class="eyebrow">LIVE CHAT</p><h2>Talk to ${escape(agent.agent_name)}</h2></div><button class="icon-text" id="new-chat">${icon("refresh", 16)}New conversation</button></div><div id="messages" class="messages">${renderMessages()}</div><form id="chat-form" class="chat-compose"><textarea name="message" rows="1" placeholder="Ask something about this knowledge base…" ${agent.ingestion_status !== "ready" ? "disabled" : ""}></textarea><button class="send-button" type="submit" title="Send message" ${agent.ingestion_status !== "ready" ? "disabled" : ""}>${icon("send", 18)}</button></form>${agent.ingestion_status !== "ready" ? `<div class="chat-not-ready">${status(agent.ingestion_status)}<span>This agent is still processing its knowledge base. Chat will unlock when it’s ready.</span></div>` : ""}</section></div>`;
    document.querySelector("#delete-agent").addEventListener("click", deleteAgent);
    document.querySelector("#add-source").addEventListener("submit", addSource);
    document.querySelector("#new-chat").addEventListener("click", newChat);
    document.querySelector("#chat-form").addEventListener("submit", sendChat);
    document.querySelectorAll(".delete-source").forEach(btn => btn.addEventListener("click", () => deleteSource(btn.dataset.sourceId)));
  }
  function renderSource(source) { const id = source.source_id || source.id; return `<article class="source-row"><span class="source-type">${sourceIcon(source.source_type)}</span><div class="source-info"><strong>${escape(source.title || source.url || "Untitled source")}</strong><span>${escape(source.source_type || "document")}${source.page ? ` · Page ${escape(source.page)}` : ""}</span>${source.error ? `<em>${escape(source.error)}</em>` : ""}</div>${status(source.status)}${id ? `<button class="source-delete delete-source" data-source-id="${escape(id)}" title="Delete source">${icon("trash", 15)}</button>` : ""}</article>`; }
  function renderMessages() { if (!state.messages.length) return `<div class="chat-intro"><div class="chat-spark">${icon("spark", 20)}</div><h3>${state.detail.ingestion_status === "ready" ? "Ask your first question" : "Your agent is being prepared"}</h3><p>${state.detail.ingestion_status === "ready" ? "Answers will be grounded in the sources listed alongside this chat." : "We’re indexing the supplied sources. This panel updates automatically."}</p></div>`; return state.messages.map(message => `<div class="message ${message.role}"><div class="bubble">${escape(message.text).replace(/\n/g, "<br>")}</div>${message.sources?.length ? `<div class="citations"><span>Sources</span>${message.sources.map(source => source.url ? `<a href="${escape(source.url)}" target="_blank" rel="noopener">${sourceIcon(source.source_type)}${escape(source.title)}</a>` : `<span>${sourceIcon(source.source_type)}${escape(source.title)}${source.page ? ` · p.${escape(source.page)}` : ""}</span>`).join("")}</div>` : ""}</div>`).join(""); }
  function refreshMessages() { const box = document.querySelector("#messages"); if (box) { box.innerHTML = renderMessages(); box.scrollTop = box.scrollHeight; } }
  function beginPolling(id) { clearPolling(); state.polling = setInterval(async () => { try { const updated = await request(`/agents/${encodeURIComponent(id)}`); state.detail = updated; renderDetail(); if (updated.ingestion_status !== "processing") { clearPolling(); toast(updated.ingestion_status === "ready" ? "Ingestion complete — chat is ready." : "Ingestion finished with an issue.", updated.ingestion_status === "ready" ? "success" : "error"); } } catch { clearPolling(); } }, 4000); }
  async function deleteAgent() { if (!confirm(`Delete “${state.detail.agent_name}”? This permanently deletes its vectors, files, and chat history.`)) return; try { await request(`/agents/${encodeURIComponent(state.detail.agent_id)}`, { method: "DELETE" }); toast("Agent deleted."); navigate("#/dashboard"); } catch (error) { toast(error.message, "error"); } }
  async function deleteSource(id) { if (!confirm("Delete this source from the knowledge base?")) return; try { await request(`/agents/${encodeURIComponent(state.detail.agent_id)}/sources/${encodeURIComponent(id)}`, { method: "DELETE" }); state.detail = await request(`/agents/${encodeURIComponent(state.detail.agent_id)}`); renderDetail(); toast("Source deleted."); } catch (error) { toast(error.message, "error"); } }
  async function addSource(event) { event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); const file = data.get("document"); const url = data.get("website_url"); if ((!file || !file.name) && !url) return toast("Add a URL or select a document first.", "error"); const button = form.querySelector("button"); button.disabled = true; try { await request(`/agents/${encodeURIComponent(state.detail.agent_id)}/sources`, { method: "POST", body: data }); state.detail = await request(`/agents/${encodeURIComponent(state.detail.agent_id)}`); renderDetail(); if (state.detail.ingestion_status === "processing") beginPolling(state.detail.agent_id); toast("Source added. Ingestion has started."); } catch (error) { toast(error.message, "error"); button.disabled = false; } }
  function newChat() { state.sessionId = uuid(); state.messages = []; refreshMessages(); toast("Started a new conversation."); }
  async function sendChat(event) { event.preventDefault(); const input = event.currentTarget.elements.message; const message = input.value.trim(); if (!message) return; state.messages.push({ role: "user", text: message }); input.value = ""; refreshMessages(); const button = event.currentTarget.querySelector("button"); button.disabled = true; try { const reply = await request(`/agents/${encodeURIComponent(state.detail.agent_id)}/chat`, { method: "POST", body: JSON.stringify({ message, session_id: state.sessionId }) }); state.sessionId = reply.session_id || state.sessionId; state.messages.push({ role: "assistant", text: reply.answer, sources: reply.sources || [] }); } catch (error) { state.messages.push({ role: "assistant", text: error.status === 409 ? "This agent is still processing its knowledge base — try again shortly." : `I couldn’t complete that request: ${error.message}` }); } finally { button.disabled = false; refreshMessages(); } }
  function renderError(id, message) { const target = document.querySelector(`#${id}`); target.className = "inline-error"; target.innerHTML = `<h2>Couldn’t load your agents.</h2><p>${escape(message)}</p><button class="secondary" onclick="location.reload()">Try again</button>`; }
  function bindShell() { document.querySelector("#disconnect")?.addEventListener("click", () => { localStorage.removeItem(KEY_STORAGE); state.apiKey = ""; navigate("#/"); }); }
  function router() { const route = currentRoute(); if (!state.apiKey && route !== "/") return landing(); if (route === "/" || !state.apiKey) return landing(); if (route === "/dashboard") return dashboard(); if (route === "/agents/new") return createAgentView(); const match = route.match(/^\/agents\/([^/]+)$/); if (match) return detail(decodeURIComponent(match[1])); navigate("#/dashboard"); }
  window.addEventListener("hashchange", router);
  router();
})();

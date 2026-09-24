# AI Agent Factory

A multi-tenant SaaS platform for building knowledge-grounded AI agents. Any organization can sign up, upload documents and/or a website URL, and get back a ready-to-use agent that answers questions strictly from that ingested content — with source citations and a hard refusal behavior when the knowledge base doesn't support an answer.

Built as an internship project. Backend and frontend are both complete and have passed a full automated test suite.

## What it does

1. A tenant signs up and receives an API key (shown once, hashed at rest).
2. The tenant creates an agent: a name, a required website URL, and any number of documents (PDF, DOCX, TXT, CSV).
3. The platform ingests every source in the background — parsing, chunking, embedding, and storing in a per-tenant/per-agent scoped vector store.
4. Once ingestion completes, an LLM generates a system prompt tailored to that agent's actual knowledge base content.
5. The tenant (or their agent's end users) can chat with the agent. Every answer is grounded in retrieved, relevant chunks — the agent explicitly says it doesn't know rather than guessing when nothing relevant is found, and cites the specific sources behind every grounded answer.
6. Tenants can add or remove individual knowledge sources from an existing agent without rebuilding it, and can delete agents entirely (which fully tears down their vectors, uploaded files, and conversation history).

## Architecture

```
backend/
└── app/
    ├── api/            tenants, agents, chat — HTTP layer
    ├── core/            shared enums, API-key security
    ├── db/              SQLAlchemy models, session handling, repositories
    ├── schemas/         Pydantic request/response contracts
    ├── storage/         uploaded-file handling
    ├── ingestion/        document parsing, chunking, website loading, pipeline orchestration
    ├── rag/              embeddings, vector store (Chroma), retriever, in-memory chat history
    ├── llm/              LLM/embedding client, prompt generator, responder
    ├── services/         business orchestration per domain (tenant/agent/ingestion/prompt/chat)
    └── main.py

frontend/
    Static single-page app consuming the API above. No backend logic lives here.
```

### Core design principles

- **Tenant isolation is enforced everywhere.** Every lookup, every vector query, every delete is scoped by `tenant_id` (and usually `agent_id` too), never trusted from client-supplied IDs alone — tenant identity always comes from the API key.
- **API keys are random, hashed, and shown once.** No reversible encoding, no plaintext storage.
- **Ingestion runs in the background**, in its own DB session, with a documented partial-failure policy: if some sources fail to ingest and at least one succeeds, the agent still becomes usable; failures are tracked per-source with their own error messages.
- **Chat is grounded, not just "RAG-flavored."** Retrieval uses an empirically calibrated cosine-distance similarity threshold — not top-k alone — so genuinely irrelevant questions get refused rather than answered from noise. The system prompt itself reinforces this as a second layer of defense. Conversational follow-ups and greetings are handled without breaking grounding for real knowledge questions.
- **External data never enters chat live.** Website ingestion (via Exa, with an HTTP/BeautifulSoup fallback and SSRF-aware URL validation) happens only at ingestion time — chat never makes an outbound web call.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy 2.0, SQLite, Pydantic v2
- **Vector store:** ChromaDB (persistent, cosine distance)
- **Embeddings / LLM:** OpenAI (`text-embedding-3-small`, `gpt-4o-mini`)
- **Ingestion:** PyMuPDF (PDF), python-docx (DOCX), stdlib `csv`, Exa + requests/BeautifulSoup (websites), tiktoken (chunking)
- **Frontend:** static HTML/CSS/JS calling the API directly

## API surface

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tenants` | Register a tenant, receive an API key |
| `POST` | `/agents` | Create an agent from a name, website URL, and documents |
| `GET` | `/agents` | List all agents for the authenticated tenant |
| `GET` | `/agents/{agent_id}` | Get one agent, including its sources and status |
| `DELETE` | `/agents/{agent_id}` | Delete an agent and everything under it |
| `POST` | `/agents/{agent_id}/sources` | Add a document and/or website to an existing agent |
| `DELETE` | `/agents/{agent_id}/sources/{source_id}` | Remove one source from an agent |
| `POST` | `/agents/{agent_id}/chat` | Chat with an agent (grounded, cited, refuses when ungrounded) |

All protected endpoints require an `X-API-Key` header.

## Running locally

```bash
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8001
```

Run from the project root (not `backend/app/`) so relative paths resolve correctly.

Environment variables needed: `OPENAI_API_KEY`, `EXA_API_KEY`.

## Testing

`run_tests.sh` is a full end-to-end smoke test covering tenant creation, agent creation and validation, multi-format ingestion, partial-failure handling, tenant isolation, source add/remove, and the full chat grounding/refusal/citation behavior. Requires `jq` and a running server.

```bash
bash run_tests.sh
```

## Known limitations / areas for further polish

- The similarity threshold was empirically calibrated against a single topic domain. Retrieval quality on multi-source agents where document lengths/content density vary significantly (e.g. a long article alongside short slide-style PDFs) can be uneven, since chunk volume imbalance across sources affects nearest-neighbor search — this is a known characteristic of the current design, not yet fully tuned for highly heterogeneous knowledge bases.
- No tenant API-key reset flow yet.
- No dedicated, line-by-line security/database review pass has been completed — the codebase has been extensively debugged through live testing rather than a formal audit.
# Architecture

## Purpose

AI Agent Factory is a multi-tenant FastAPI service for creating knowledge-grounded agents from uploaded documents and a website. A tenant receives an API key at registration; every agent lookup is then scoped to that authenticated tenant.

## Components

| Area | Responsibility |
| --- | --- |
| `backend/app/api` | FastAPI routers for tenants, agents, sources, and chat. |
| `backend/app/core` | Shared enums and API-key generation, hashing, and authentication. |
| `backend/app/db` | SQLAlchemy models, SQLite session management, and scoped repositories. |
| `backend/app/services` | Tenant creation, agent/source orchestration, background ingestion, prompt generation, and chat persistence. |
| `backend/app/ingestion` | File parsing, website fetching, chunking, and ingestion status updates. |
| `backend/app/rag` | OpenAI embeddings, Chroma persistence, tenant/agent-scoped retrieval, and in-memory chat history. |
| `backend/app/llm` | OpenAI chat completions for generated prompts and answers. |
| `backend/app/storage` | Tenant/agent-organized local upload storage. |
| `frontend` | Static HTML, CSS, and JavaScript client that calls the API. |

## Data model and isolation

```text
Tenant
  └── Agent
       ├── Source
       └── Conversation
            └── Message
```

SQLite foreign keys are enabled for application sessions. Deleting a tenant cascades to its agents, sources, conversations, and messages. Repository lookups for agents, sources, conversations, and messages include the authenticated `tenant_id`; vector queries and vector deletion are also filtered by tenant and agent.

API keys are generated with `secrets.token_urlsafe`, prefixed with `tsk_`, and persisted only as SHA-256 hashes. The raw key is returned when the tenant is created and is needed in `X-API-Key` for protected routes.

## Main flows

### Agent creation

1. The tenant submits an agent name, one website URL, and one or more uploaded documents.
2. The service creates the agent and source rows, and writes documents under `backend/data/uploads/<tenant_id>/<agent_id>/`.
3. A FastAPI background task processes each source in a separate database session.
4. Sources are parsed/fetched, chunked, embedded, and stored in Chroma with tenant, agent, source, page, and chunk metadata.
5. If at least one source succeeds, the agent is marked `ready` and receives an LLM-generated system prompt. If every source fails, it is marked `failed` with a failure reason.

### Chat

1. The API authenticates the tenant and confirms that the requested agent belongs to it and is `ready`.
2. The service retrieves tenant- and agent-scoped chunks below the configured cosine-distance threshold.
3. With no relevant chunks, the service returns its fixed refusal response. Greetings and brief conversational acknowledgements are handled separately.
4. The answer and its resolved source citations are returned and persisted with the conversation session.

See [Ingestion and retrieval](ingestion-and-rag.md) for details and [API reference](api.md) for the wire contract.

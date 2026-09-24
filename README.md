# AI Agent Factory

AI Agent Factory is a multi-tenant FastAPI application for creating knowledge-grounded AI agents. An organization registers once, receives an API key, provides documents and a website for an agent, then chats with that agent using answers grounded in the ingested material and accompanied by source citations.

This repository contains the backend, a static frontend, project documentation, and an isolated pytest suite. The application code was not changed as part of the documentation and test-suite completion.

## Capabilities

- Creates tenants and returns a one-time `tsk_` API key; only its SHA-256 hash is stored.
- Scopes agent, source, conversation, message, and vector operations to the authenticated tenant.
- Accepts PDF, DOCX, TXT, and CSV documents, plus website content.
- Processes sources in the background, tracks `processing`, `ready`, and `failed` states, and generates a per-agent system prompt after successful ingestion.
- Uses OpenAI embeddings with a Chroma vector store and a relevance threshold to ground answers.
- Returns a fixed refusal when a knowledge question has no relevant retrieved content, while keeping greetings and brief acknowledgements conversational.
- Supports adding and removing individual sources and deleting an agent with its local file and vector data.

## Requirements

- Python 3.10 or newer
- An OpenAI API key
- An Exa API key if you want Exa-backed website retrieval (the HTTP/BeautifulSoup fallback is used when it is not configured)

## Setup

1. Create the local environment and install dependencies.

   Windows:

   ```bat
   scripts\setup.bat
   ```

   Bash-compatible shell:

   ```bash
   bash scripts/setup.sh
   ```

2. Copy `.env.example` to `.env` and set your credentials:

   ```dotenv
   OPENAI_API_KEY=...
   EXA_API_KEY=...
   ```

3. Start the backend on port 8001.

   Windows:

   ```bat
   scripts\run_backend.bat
   ```

   Bash-compatible shell:

   ```bash
   bash scripts/run_backend.sh
   ```

   FastAPI's interactive API documentation is then available at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs). The current health-style response is at [http://127.0.0.1:8001/](http://127.0.0.1:8001/).

4. Optionally serve the static frontend at `http://127.0.0.1:8080`.

   Windows:

   ```bat
   scripts\run_frontend.bat
   ```

   Bash-compatible shell:

   ```bash
   bash scripts/run_frontend.sh
   ```

The frontend's API base URL is `http://127.0.0.1:8001` by default.

## API overview

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | No | Current health-style response. |
| `POST` | `/tenants` | No | Create a tenant and receive an API key. |
| `POST` | `/agents` | `X-API-Key` | Create an agent from documents and a website URL. |
| `GET` | `/agents` | `X-API-Key` | List the caller's agents. |
| `GET` | `/agents/{agent_id}` | `X-API-Key` | Get one caller-owned agent and source status. |
| `DELETE` | `/agents/{agent_id}` | `X-API-Key` | Delete one caller-owned agent and related data. |
| `POST` | `/agents/{agent_id}/sources` | `X-API-Key` | Add a document or website source. |
| `DELETE` | `/agents/{agent_id}/sources/{source_id}` | `X-API-Key` | Remove one source. |
| `POST` | `/agents/{agent_id}/chat` | `X-API-Key` | Send a message to a ready agent. |

For field-level request and response details, see [the API reference](docs/api.md).

## Testing

Run the isolated test suite with either wrapper:

```bat
scripts\run_tests.bat
```

```bash
bash scripts/run_tests.sh
```

Both commands run `pytest tests -v` only (with the cache provider disabled for restricted workspaces) and write the full output to `tests/test_log.txt`. The default suite does not make live OpenAI, Exa, Chroma, or backend-server calls.

The repository also includes an opt-in end-to-end smoke test migrated from the former Bash test script. It creates real tenant and agent data, so start a configured local backend first and opt in explicitly:

```bash
RUN_E2E=1 AGENT_FACTORY_BASE_URL=http://127.0.0.1:8001 python -m pytest tests/test_e2e_smoke.py -v
```

The default validation run currently reports **28 passed, 1 skipped**. The skipped test is the live workflow above when `RUN_E2E` is unset.

## Repository layout

```text
backend/       FastAPI application, database models, ingestion, RAG, and services
frontend/      Static browser client
docs/          Architecture, API, ingestion, testing, and operating documentation
scripts/       Setup and cross-platform launch/test wrappers
tests/         Unit/API-contract tests, fixtures, and the opt-in live smoke test
```

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [Ingestion and retrieval](docs/ingestion-and-rag.md)
- [Testing guide](docs/testing.md)
- [Operation notes and current limitations](docs/operations.md)

## Notes

The checked-in assignment brief asks for `/health`; the current implementation exposes its simple health-style response at `/`. See [operation notes](docs/operations.md) for this and other source-verified limitations, including process-local chat retrieval history and local SQLite/filesystem persistence.

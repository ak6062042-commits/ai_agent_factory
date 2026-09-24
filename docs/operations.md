# Local operation notes

## Setup and launch

Copy `.env.example` to `.env` and set at least `OPENAI_API_KEY`; set `EXA_API_KEY` to enable Exa website retrieval. Use `scripts/setup.sh` on Bash-compatible systems or `scripts/setup.bat` on Windows to create `.venv` and install `requirements.txt`.

Run the backend from the repository root:

```bash
python -m uvicorn backend.app.main:app --reload --port 8001
```

The static frontend is configured for `http://127.0.0.1:8001` in `frontend/config.js`. Serve that directory with an HTTP static-file server rather than opening its HTML file directly if the browser blocks local-origin requests.

## Local state

Runtime state is intentionally outside source code:

| Location | Contents |
| --- | --- |
| `backend/data/app.db` | SQLite tenants, agents, sources, conversations, and messages. |
| `backend/data/chroma/` | Chroma vector persistence. |
| `backend/data/uploads/` | Uploaded documents organized by tenant and agent. |
| `tests/test_log.txt` | Latest output from a test-runner wrapper. |

These paths are ignored by Git. Deleting an agent through the API removes its vector records and local upload directory; database cascade rules remove related relational records.

## Current limitations

- The assignment brief asks for `/health`, but the checked-in application currently exposes its health-style response at `/`.
- Agent creation requires both a website URL and at least one document, even though later source addition accepts either kind independently.
- Chat history used to improve retrieval is held in process memory, so it does not survive a backend restart.
- Background ingestion failure details are retained per source, but retries are manual: add a source again or recreate the agent.
- The application currently uses SQLite and local filesystem storage, which are suitable for local development rather than a horizontally scaled deployment.

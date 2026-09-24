# Testing

The test suite is under `tests/` and is run only from that directory scope. It does not require an OpenAI key, Exa key, Chroma server, or a running API for the default run.

## Default suite

```bash
python -m pytest tests -v
```

Or use the repository wrappers:

```bash
bash scripts/run_tests.sh
scripts\run_tests.bat
```

Both wrappers invoke pytest against `tests` only and copy the complete console output to `tests/test_log.txt`. They disable pytest's cache provider so a restricted workspace cannot interfere with test execution. The log is local runtime output and is ignored by Git.

The default suite uses a fresh in-memory SQLite database per test and mocks external LLM, vector, storage, and background-ingestion boundaries. It covers:

- database defaults, constraints, foreign keys, and cascade deletion;
- tenant creation, duplicate handling, API-key hashing, and authentication;
- tenant-scoped repository lookups and conversations;
- agent route validation and tenant-scoped listing/deletion contracts;
- chat persistence and citation resolution without a real LLM;
- parser, chunking, URL safety, retrieval unpacking, and prompt fallback behavior.

## Live smoke workflow

`tests/test_e2e_smoke.py` is the Python version of the former Bash smoke workflow. It exercises tenant creation, agent validation, ingestion readiness, isolation, source addition, grounded chat, conversational follow-up, refusal behavior, and cleanup against a real local server.

It is deliberately opt-in because it creates data and needs configured services, valid credentials, and network access:

```bash
RUN_E2E=1 AGENT_FACTORY_BASE_URL=http://127.0.0.1:8001 python -m pytest tests/test_e2e_smoke.py -v
```

On Windows PowerShell:

```powershell
$env:RUN_E2E = "1"
$env:AGENT_FACTORY_BASE_URL = "http://127.0.0.1:8001"
.\.venv\Scripts\python.exe -m pytest tests\test_e2e_smoke.py -v
```

Without `RUN_E2E=1`, pytest reports that module as skipped rather than attempting live calls. Start the backend separately before an opt-in run.

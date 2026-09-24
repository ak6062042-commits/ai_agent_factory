# Ingestion and retrieval

## Supported sources

Initial agent creation requires a website URL and documents. The parser currently supports PDF, DOCX, TXT, and CSV files. Documents are stored locally per tenant and agent before ingestion. A source added later can be a website or one document.

Website fetching first rejects unsafe schemes, `localhost`, and private, loopback, or link-local literal IP addresses. When `EXA_API_KEY` is configured it tries Exa first; on failure it falls back to an HTTP request parsed with BeautifulSoup. The fallback uses a ten-second timeout and removes script, style, navigation, and footer content before extracting text.

## Chunking and indexing

Text is tokenized with the `cl100k_base` encoding. The current defaults are 500-token chunks with 50-token overlap. Document chunks retain a page number where one is available; website and TXT chunks have no page number. Chroma records each chunk with tenant ID, agent ID, source ID, page, and chunk index, which allows later retrieval and cleanup to stay scoped.

The ingestion task processes all of an agent's sources. A failing source receives `failed` status and an error message. If at least one source succeeds, the agent becomes `ready`, its indexed-chunk count is updated, and an LLM summarizes retrieved sample chunks into a per-agent system prompt. If no sources succeed, the agent becomes `failed`.

## Grounded answers and citations

For a knowledge question, retrieval asks Chroma for the closest tenant/agent-scoped chunks and filters results by the configured cosine-distance threshold (`0.50`). If no chunks remain, the service returns:

```text
I cannot find that in the provided information.
```

When chunks are found, they are passed to the LLM as context together with the agent system prompt. The service maps returned `source_id` values back to caller-owned source records and exposes their type, title, optional page, and optional URL as response citations.

Conversation messages are persisted in SQLite and a short in-memory history is also used to augment follow-up retrieval. The in-memory history is process-local; restarting the service clears that retrieval aid, although persisted messages remain in the database.

## Important boundaries

- Website content is fetched at ingestion time, not during a chat request.
- Background ingestion relies on configured OpenAI/Exa credentials and reachable source URLs.
- The similarity threshold is a configured heuristic. It should be evaluated against representative tenant content before treating it as a universal relevance guarantee.

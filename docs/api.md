# API reference

The application is served by FastAPI. Interactive OpenAPI documentation is available at `/docs` while it is running. The current root health-style response is `GET /`, which returns `{"message": "Healthy"}`.

## Authentication

`POST /tenants` is public. All `/agents` routes require an `X-API-Key` request header containing the raw key returned at tenant creation. An absent header is handled by FastAPI as a validation error; an unknown key returns `401` with `{"detail": "Invalid Api key"}`.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/` | No | Returns the current health-style response. |
| `POST` | `/tenants` | No | Creates a tenant and returns its API key once. |
| `POST` | `/agents` | Yes | Creates an agent, persists its sources, and starts background ingestion. |
| `GET` | `/agents` | Yes | Lists only the caller's agents. |
| `GET` | `/agents/{agent_id}` | Yes | Returns one caller-owned agent and its sources. |
| `DELETE` | `/agents/{agent_id}` | Yes | Removes one caller-owned agent, associated vectors, and uploaded files. |
| `POST` | `/agents/{agent_id}/sources` | Yes | Adds one website URL or document to an existing caller-owned agent. |
| `DELETE` | `/agents/{agent_id}/sources/{source_id}` | Yes | Removes one caller-owned source and its associated vector/file data. |
| `POST` | `/agents/{agent_id}/chat` | Yes | Sends a message to a ready caller-owned agent. |

## Request and response examples

### Create a tenant

```http
POST /tenants
Content-Type: application/json

{
  "organization_name": "Acme Support",
  "admin_email": "admin@acme.example"
}
```

The `201` response contains `tenant_id`, `organization_name`, normalized `admin_email`, and `api_key`. Duplicate email addresses return `409`.

### Create an agent

`POST /agents` uses `multipart/form-data`:

| Field | Required | Notes |
| --- | --- | --- |
| `agent_name` | Yes | Whitespace is stripped; an empty value returns `422`. |
| `website_url` | Yes | Must be an HTTP(S) URL. |
| `documents` | Yes | One or more uploaded files; at most five are accepted. |

The `201` response includes an `agent_id`, `ingestion_status`, `indexed_chunk_count`, generated `system_prompt` when available, and source metadata. Creation returns before background ingestion is complete, so poll `GET /agents/{agent_id}` until `ingestion_status` is `ready` or `failed`.

### Add a source

`POST /agents/{agent_id}/sources` accepts multipart data with either `website_url`, `document`, or both. Supplying neither returns `400`; an invalid website URL returns `422`.

### Chat

```http
POST /agents/{agent_id}/chat
X-API-Key: tsk_...
Content-Type: application/json

{
  "message": "What does the handbook say about refunds?",
  "session_id": "support-session-42"
}
```

`message` must be non-empty and no longer than 10,000 characters. `session_id` must be non-empty. A ready agent returns `answer`, the echoed `session_id`, and zero or more `sources`. A missing/not-owned agent returns `404`; an agent still processing or failed returns `409`.

## Status values

Agents and sources use `processing`, `ready`, or `failed`. The `error` field on a source and `failure_reason` on an agent provide available failure context.

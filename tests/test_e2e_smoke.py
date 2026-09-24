"""Opt-in live smoke workflow migrated from the former scripts/run_tests.sh."""

import os
import time
import uuid

import httpx
import pytest


pytestmark = pytest.mark.integration
BASE_URL = os.getenv("AGENT_FACTORY_BASE_URL", "http://127.0.0.1:8001").rstrip("/")


def _enabled():
    return os.getenv("RUN_E2E") == "1"


def _wait_for_ready(client, agent_id, headers, timeout_seconds=45):
    deadline = time.monotonic() + timeout_seconds
    latest = None
    while time.monotonic() < deadline:
        response = client.get(f"/agents/{agent_id}", headers=headers)
        response.raise_for_status()
        latest = response.json()
        if latest["ingestion_status"] in {"ready", "failed"}:
            return latest
        time.sleep(2)
    raise AssertionError(f"Agent did not finish ingestion within {timeout_seconds}s: {latest}")


@pytest.mark.skipif(not _enabled(), reason="Set RUN_E2E=1 to run live smoke tests.")
def test_live_tenant_agent_source_chat_and_cleanup_workflow():
    suffix = uuid.uuid4().hex[:10]
    tenant_email = f"smoke-{suffix}@example.com"
    document = b"The Acme refund policy permits returns within 30 days of purchase."

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        root = client.get("/")
        assert root.status_code == 200

        tenant_response = client.post(
            "/tenants",
            json={"organization_name": "Smoke Test Org", "admin_email": tenant_email},
        )
        assert tenant_response.status_code == 201, tenant_response.text
        tenant = tenant_response.json()
        headers = {"X-API-Key": tenant["api_key"]}

        duplicate = client.post(
            "/tenants",
            json={"organization_name": "Duplicate", "admin_email": tenant_email},
        )
        assert duplicate.status_code == 409

        invalid_name = client.post(
            "/agents",
            headers=headers,
            data={"agent_name": " ", "website_url": "https://example.com"},
            files=[("documents", ("policy.txt", document, "text/plain"))],
        )
        assert invalid_name.status_code == 422

        invalid_url = client.post(
            "/agents",
            headers=headers,
            data={"agent_name": "Refund Bot", "website_url": "not-a-url"},
            files=[("documents", ("policy.txt", document, "text/plain"))],
        )
        assert invalid_url.status_code == 422

        created = client.post(
            "/agents",
            headers=headers,
            data={"agent_name": "Refund Bot", "website_url": "https://example.com"},
            files=[("documents", ("policy.txt", document, "text/plain"))],
        )
        assert created.status_code == 201, created.text
        agent_id = created.json()["agent_id"]

        details = _wait_for_ready(client, agent_id, headers)
        assert details["ingestion_status"] == "ready", details
        assert details["indexed_chunk_count"] > 0
        before_source_count = details["indexed_chunk_count"]

        other_tenant = client.post(
            "/tenants",
            json={"organization_name": "Other Org", "admin_email": f"other-{suffix}@example.com"},
        )
        assert other_tenant.status_code == 201
        other_headers = {"X-API-Key": other_tenant.json()["api_key"]}
        assert client.get(f"/agents/{agent_id}", headers=other_headers).status_code == 404

        empty_source = client.post(f"/agents/{agent_id}/sources", headers=headers)
        assert empty_source.status_code == 400

        added_source = client.post(
            f"/agents/{agent_id}/sources",
            headers=headers,
            data={"website_url": "https://example.org"},
        )
        assert added_source.status_code == 201, added_source.text
        after_source = client.get(f"/agents/{agent_id}", headers=headers)
        assert after_source.status_code == 200
        assert after_source.json()["indexed_chunk_count"] >= before_source_count

        relevant = client.post(
            f"/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "What is the return window?", "session_id": "smoke-session"},
        )
        assert relevant.status_code == 200, relevant.text
        assert relevant.json()["session_id"] == "smoke-session"
        assert relevant.json()["sources"]

        follow_up = client.post(
            f"/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "Can you summarize that?", "session_id": "smoke-session"},
        )
        assert follow_up.status_code == 200, follow_up.text

        greeting = client.post(
            f"/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "hi", "session_id": "greeting-session"},
        )
        assert greeting.status_code == 200, greeting.text

        irrelevant = client.post(
            f"/agents/{agent_id}/chat",
            headers=headers,
            json={"message": "What is the best biryani recipe?", "session_id": "refusal-session"},
        )
        assert irrelevant.status_code == 200, irrelevant.text
        assert irrelevant.json()["answer"] == "I cannot find that in the provided information."

        not_ready = client.post(
            "/agents",
            headers=headers,
            data={"agent_name": "Not Ready", "website_url": "https://example.com"},
            files=[("documents", ("policy.txt", document, "text/plain"))],
        )
        assert not_ready.status_code == 201
        not_ready_chat = client.post(
            f"/agents/{not_ready.json()['agent_id']}/chat",
            headers=headers,
            json={"message": "test", "session_id": "not-ready"},
        )
        assert not_ready_chat.status_code == 409

        deleted = client.delete(f"/agents/{agent_id}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(f"/agents/{agent_id}", headers=headers).status_code == 404
        assert client.delete(f"/agents/{agent_id}", headers=headers).status_code == 404

from fastapi.testclient import TestClient

from backend.app.api import agents
from backend.app.core.enums import IngestionStatus
from backend.app.core.security import get_current_tenant
from backend.app.db.database import get_db
from backend.app.main import app
from backend.app.schemas.agent import AgentResponse
from backend.app.services import agent_services


def _response(agent_id="agent-1", name="Support Bot"):
    return AgentResponse(
        agent_id=agent_id,
        agent_name=name,
        ingestion_status=IngestionStatus.PROCESSING,
        indexed_chunk_count=0,
        sources=[],
    )


def test_create_agent_validates_input_before_calling_service(monkeypatch, tenant):
    called = False

    def create_agent(*args, **kwargs):
        nonlocal called
        called = True
        return _response()

    monkeypatch.setattr(agent_services, "create_agent", create_agent)
    app.dependency_overrides[get_current_tenant] = lambda: tenant
    try:
        with TestClient(app) as client:
            files = [("documents", ("guide.txt", b"guide content", "text/plain"))]
            blank = client.post("/agents", data={"agent_name": " ", "website_url": "https://example.com"}, files=files)
            invalid_url = client.post("/agents", data={"agent_name": "Guide", "website_url": "not-a-url"}, files=files)

        assert blank.status_code == 422
        assert invalid_url.status_code == 422
        assert called is False
    finally:
        app.dependency_overrides.clear()


def test_create_agent_passes_valid_form_data_to_service(monkeypatch, tenant, session):
    captured = {}

    def override_db():
        yield session

    def create_agent(db, authenticated_tenant, agent_name, website_url, documents, background_tasks):
        captured.update({
            "db": db,
            "tenant": authenticated_tenant,
            "agent_name": agent_name,
            "website_url": website_url,
            "documents": documents,
        })
        return _response()

    monkeypatch.setattr(agent_services, "create_agent", create_agent)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_tenant] = lambda: tenant
    try:
        with TestClient(app) as client:
            response = client.post(
                "/agents",
                data={"agent_name": "  Guide  ", "website_url": "https://example.com/guide"},
                files=[("documents", ("guide.txt", b"guide content", "text/plain"))],
            )

        assert response.status_code == 201
        assert response.json()["agent_id"] == "agent-1"
        assert captured["db"] is session
        assert captured["tenant"].tenant_id == tenant.tenant_id
        assert captured["agent_name"] == "Guide"
        assert captured["website_url"] == "https://example.com/guide"
        assert captured["documents"][0].filename == "guide.txt"
    finally:
        app.dependency_overrides.clear()


def test_list_and_delete_routes_preserve_tenant_scope(monkeypatch, tenant, session):
    def override_db():
        yield session

    monkeypatch.setattr(agents.repositories, "get_agents_for_tenant", lambda db, tenant_id: [_response("agent-1")])
    monkeypatch.setattr(agent_services, "delete_agent", lambda db, tenant_id, agent_id: agent_id == "agent-1")
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_tenant] = lambda: tenant
    try:
        with TestClient(app) as client:
            listed = client.get("/agents")
            deleted = client.delete("/agents/agent-1")
            missing = client.delete("/agents/missing")

        assert listed.status_code == 200
        assert listed.json()[0]["agent_id"] == "agent-1"
        assert deleted.status_code == 204
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()

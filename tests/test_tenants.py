import pytest
from fastapi import HTTPException

from backend.app.core import security
from backend.app.db import repositories
from backend.app.schemas.tenant import TenantRequest
from backend.app.services import tenant_services


def test_create_tenant_normalizes_email_and_returns_raw_key(session):
    result = tenant_services.create_tenant(
        session,
        TenantRequest(organization_name="Acme", admin_email="ADMIN@ACME.EXAMPLE"),
    )

    saved = repositories.get_tenant_by_id(session, result.tenant_id)
    assert result.api_key.startswith("tsk_")
    assert result.admin_email == "admin@acme.example"
    assert saved.hashed_api_key == security.hash_api_key(result.api_key)
    assert saved.hashed_api_key != result.api_key


def test_duplicate_tenant_email_raises_domain_error(session):
    payload = TenantRequest(organization_name="Acme", admin_email="admin@acme.example")
    tenant_services.create_tenant(session, payload)

    with pytest.raises(tenant_services.TenantAlreadyExistsError):
        tenant_services.create_tenant(session, payload)


def test_api_key_hash_is_stable_after_surrounding_whitespace():
    assert security.hash_api_key("  tsk_example  ") == security.hash_api_key("tsk_example")


def test_current_tenant_accepts_known_key_and_rejects_unknown_key(session):
    key = "tsk_known"
    tenant = repositories.create_tenant(
        session,
        organization_name="Acme",
        admin_email="admin@acme.example",
        hashed_api_key=security.hash_api_key(key),
    )
    session.commit()

    assert security.get_current_tenant(db=session, x_api_key=key).tenant_id == tenant.tenant_id
    with pytest.raises(HTTPException) as error:
        security.get_current_tenant(db=session, x_api_key="tsk_unknown")
    assert error.value.status_code == 401

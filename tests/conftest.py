import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Agent, Base, Tenant


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    database_session = sessionmaker(bind=engine, expire_on_commit=False)()
    yield database_session
    database_session.close()
    engine.dispose()


def make_tenant(**overrides):
    values = {
        "organization_name": "Acme",
        "admin_email": "admin@acme.example",
        "hashed_api_key": "hash-1",
    }
    values.update(overrides)
    return Tenant(**values)


def make_agent(tenant_id, **overrides):
    values = {
        "tenant_id": tenant_id,
        "agent_name": "Support Bot",
        "website_url": "https://example.com",
    }
    values.update(overrides)
    return Agent(**values)


@pytest.fixture
def tenant(session):
    value = make_tenant()
    session.add(value)
    session.commit()
    return value

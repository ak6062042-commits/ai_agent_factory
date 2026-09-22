import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, Tenant, Agent, Source, Conversation, Message
from backend.app.core.enums import IngestionStatus, SourceType, Roles


@pytest.fixture
def session():
    """A fresh in-memory database for every test."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    yield s
    s.close()
    engine.dispose()


# ---------- helpers ----------

def make_tenant(**overrides):
    data = dict(
        organization_name="Acme",
        admin_email="a@example.com",
        hashed_api_key="hash-1",
    )
    data.update(overrides)
    return Tenant(**data)


def make_agent(tenant_id, **overrides):
    data = dict(
        agent_name="Support Bot",
        website_url="https://acme.com",
        tenant_id=tenant_id,
    )
    data.update(overrides)
    return Agent(**data)


# ---------- Tenant (unchanged, already passing) ----------

def test_insert_tenant_generates_id(session):
    t = make_tenant()
    session.add(t)
    session.commit()

    saved = session.query(Tenant).one()
    assert saved.tenant_id is not None and len(saved.tenant_id) == 36
    assert saved.admin_email == "a@example.com"


def test_duplicate_email_rejected(session):
    session.add(make_tenant())
    session.commit()

    session.add(make_tenant(hashed_api_key="hash-2"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_duplicate_api_key_hash_rejected(session):
    session.add(make_tenant())
    session.commit()

    session.add(make_tenant(admin_email="b@example.com"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_same_org_name_allowed(session):
    session.add(make_tenant())
    session.add(make_tenant(admin_email="b@example.com", hashed_api_key="hash-2"))
    session.commit()
    assert session.query(Tenant).count() == 2


# ---------- Agent: foreign key enforcement ----------

def test_agent_needs_real_tenant(session):
    """A nonexistent tenant_id must be rejected — this is what the FK pragma protects."""
    session.add(make_agent(tenant_id="does-not-exist"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_agent_defaults(session):
    t = make_tenant()
    session.add(t)
    session.commit()

    a = make_agent(t.tenant_id)
    session.add(a)
    session.commit()

    saved = session.query(Agent).one()
    assert saved.ingestion_status == IngestionStatus.PROCESSING
    assert saved.system_prompt is None
    assert saved.created_at is not None


def test_agent_name_can_repeat_across_tenants(session):
    """Two agents (even different tenants) may share a name — this was over-constrained before."""
    t1 = make_tenant()
    t2 = make_tenant(admin_email="b@example.com", hashed_api_key="hash-2")
    session.add_all([t1, t2])
    session.commit()

    session.add(make_agent(t1.tenant_id, agent_name="Support Bot"))
    session.add(make_agent(t2.tenant_id, agent_name="Support Bot"))
    session.commit()  # must NOT raise

    assert session.query(Agent).count() == 2


# ---------- Conversation: composite uniqueness + isolation ----------

def test_same_session_id_blocked_within_same_tenant_agent(session):
    t = make_tenant()
    session.add(t)
    session.commit()
    a = make_agent(t.tenant_id)
    session.add(a)
    session.commit()

    session.add(Conversation(tenant_id=t.tenant_id, agent_id=a.agent_id, session_id="s1"))
    session.commit()

    session.add(Conversation(tenant_id=t.tenant_id, agent_id=a.agent_id, session_id="s1"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_same_session_id_allowed_across_tenants(session):
    """This is the isolation guarantee: two tenants can reuse the same session_id."""
    t1 = make_tenant()
    t2 = make_tenant(admin_email="b@example.com", hashed_api_key="hash-2")
    session.add_all([t1, t2])
    session.commit()

    a1 = make_agent(t1.tenant_id)
    a2 = make_agent(t2.tenant_id)
    session.add_all([a1, a2])
    session.commit()

    session.add(Conversation(tenant_id=t1.tenant_id, agent_id=a1.agent_id, session_id="shared-id"))
    session.add(Conversation(tenant_id=t2.tenant_id, agent_id=a2.agent_id, session_id="shared-id"))
    session.commit()  # must NOT raise

    assert session.query(Conversation).count() == 2


# ---------- Source ----------

def test_source_needs_real_agent(session):
    t = make_tenant()
    session.add(t)
    session.commit()

    session.add(Source(
        tenant_id=t.tenant_id,
        agent_id="does-not-exist",
        source_type=SourceType.DOCUMENT,
        title="Handbook.pdf",
    ))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# ---------- Cascade delete ----------

def test_deleting_tenant_deletes_everything_below(session):
    t = make_tenant()
    session.add(t)
    session.commit()

    a = make_agent(t.tenant_id)
    session.add(a)
    session.commit()

    session.add(Source(tenant_id=t.tenant_id, agent_id=a.agent_id,
                        source_type=SourceType.DOCUMENT, title="doc.pdf"))
    conv = Conversation(tenant_id=t.tenant_id, agent_id=a.agent_id, session_id="s1")
    session.add(conv)
    session.commit()

    session.add(Message(tenant_id=t.tenant_id, agent_id=a.agent_id,
                         conversation_id=conv.conversation_id,
                         role=Roles.USER, content="hi"))
    session.commit()

    session.delete(t)
    session.commit()

    assert session.query(Agent).count() == 0
    assert session.query(Source).count() == 0
    assert session.query(Conversation).count() == 0
    assert session.query(Message).count() == 0
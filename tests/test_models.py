import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, Tenant


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


def make_tenant(**overrides):
    data = dict(
        organization_name="Acme",
        admin_email="a@example.com",
        hashed_api_key="hash-1",
    )
    data.update(overrides)
    return Tenant(**data)


def test_insert_tenant_generates_id(session):
    t = make_tenant()
    session.add(t)
    session.commit()

    saved = session.query(Tenant).one()
    assert saved.id is not None and len(saved.id) == 36  
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
# NOTE: Should have written it in schema but only mail and hashed key are same, company name can be same 
# run it with pytest test_models.py -v
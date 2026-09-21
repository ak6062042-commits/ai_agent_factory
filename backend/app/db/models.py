from typing import List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid

# NOTE: Base defined here because was removed from database.py and model.Base.metadata.create_all() was used in init_db
class Base(DeclarativeBase):
    pass
    

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4())) #deafult = uuid.uuid4
    organization_name: Mapped[str] = mapped_column() # TODO = Email casing: the unique constraint treats A@x.com and a@x.com as different. Lowercase the email in the tenant service
    admin_email: Mapped[str] = mapped_column(unique = True)
    hashed_api_key: Mapped[str] = mapped_column(unique = True)
    
    #agents: Mapped[List["Agent"]] = relationship(back_populates = "tenants", cascade = "all, delete-orphan")

# class Agent(Base):
#     __tablename__ = "agents"
    
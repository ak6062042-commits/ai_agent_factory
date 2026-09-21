from typing import List, Optional
from sqlalchemy import ForeignKey, Text, String, Boolean, DateTime, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import EmailStr

# TODO: REDESIGN EVERYTHING LATER

class Base(DeclarativeBase):
    pass
    

class Tenant(Base):
    __tabelname__ = "Tenanat"
    id = Column(String, primary_key = True, autoincrement = True, nullable = False)
    organization_name = Column(String, autoincrement = True)
    admin_email = Column(String, primary_key = True, autoincrement = True)
    hashed_api_key =Column(String, primary_key = True, autoincrement = True)
    
    agents: Mapped[List["Agent"]] = relationship(back_populates = "Tenant", cascade = "all, delete-orphan")

class Agent:
    __tabelname = "Agent"
    pass
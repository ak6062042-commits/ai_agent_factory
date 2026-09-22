from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import tenants, agents
from backend.app.db.database import init_db
from backend.app.core.security import get_current_tenant
from backend.app.db.models import Tenant

description = """A FastAPI-based multi-tenant SaaS platform that lets any organisation create its own AI agent in minutes.\n
A tenant is able to upload a document and paste a website URL, and the platform automatically\n
ingests both sources, builds a knowledge base, generates a tailored system prompt using an LLM,\n
and returns a ready-to-use agent that answers questions grounded in that content (RAG).\n
Each tenant's data, agents and conversations are strictly isolated from every other tenant.\n"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI AGENT FACTORY", description=description, version="0.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

app.include_router(tenants.router)
app.include_router(agents.router)

# @app.get ("/whoami")
# def whoami(tenant: Tenant = Depends(get_current_tenant)):
#     return{
#         "tenant_id": tenant.tenant_id,
#         "organization": tenant.organization_name
#     }  add a feature like this

@app.get('/')
def root() -> dict:
    return {"message": "Healthy"}
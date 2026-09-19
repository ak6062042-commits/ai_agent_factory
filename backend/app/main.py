from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

description = """A FastAPI-based multi-tenant SaaS platform that lets any organisation create its own AI agent in minutes.\n
A tenant is able to upload a document and paste a website URL, and the platform automatically\n
ingests both sources, builds a knowledge base, generates a tailored system prompt using an LLM,\n
and returns a ready-to-use agent that answers questions grounded in that content (RAG).\n
Each tenant's data, agents and conversations are strictly isolated from every other tenant.\n"""

app = FastAPI(title = "AI AGENT FACTORY", description = description, version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

#app.include_router(...) -> place holder for router

@app.get('/')
def root() -> dict:
    return {"message": "Healthy"}
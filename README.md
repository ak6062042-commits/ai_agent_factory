So what are we even building?
* We are building a Fast API based multi Tenant sass platform that let's any organization create it's own AI agent in minutes!!!
NOTE: what does this even mean (this means that we will have fun all through out the weekend!)

Basic Features:
* A Tenant/User  -> gives a link some content run ingestion, and  create embedding and, orchestrate the AI agent with the organization specific content
auto-generate prompts for the Tenant specific agent behavior.
* extremely important: No tenant can access the other tenant's content 

WARNINGS:
* (Do not spend time on front-end at all)
* (Do not over engineered)
* Keep latency very low

INTENDED TECH STACK:
* Fast-API
* Python
* FAISS
* SQL-lite
* OPENAI_API_KEY
* EVA_API_KEY
(To be further decided!)

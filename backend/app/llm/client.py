# NOTE: IS TO BE REVIEW EXTENSIVELY ALOT, MOSTLY IN THE WEBSEARCHER


from openai import OpenAI
import backend.app.config as config
from exa_py import Exa
from exa_py.api import SearchResponse
from pydantic import AnyHttpUrl
from pathlib import Path

class LLMClient:
    def __init__(self, model: str = config.MODEL_VERSION):
        self.client = OpenAI(api_key = config.OPENAI_API_KEY)
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = config.MAX_TOKEN, temperature: float = config.TEMPERATURE, top_P: float = config.TOP_P, top_k: float = config.TOP_K):
        try:
            response = self.client.chat.completions.create( 
                model = self.model, messages = prompt, 
                max_completion_tokens = max_tokens , temperature = temperature, top_p = top_P)
            return response.choices[0].message.content.strip()
    
        except Exception as e:
            print(f"llm generation failed: {e}")
            raise
        

class EmbeddingClient:
    def __init__(self, embedding_model: str = config.EMBEDDING_CLIENT):
        self.client = OpenAI(api_key = config.OPENAI_API_KEY)
        self.model = embedding_model
    
    def embed(self, text: str):
        response = self.client.embeddings.create(model = self.model, input = text)
        return response.data[0].embedding

    def embedBatch(self, texts: list):
        reponse = self.client.embeddings.create(model = self.model, input = texts)
        return [r.embedding for r in reponse.data]

class WebSearchClient:
    def __init__(self):
        self.web_searcher = Exa(api_key = config.EXA_API_KEY)
    def get_content(self, url: AnyHttpUrl, search_similar: bool = False):
        primary_page = self.web_searcher.get_contents(urls = url, text = {"max_characters": 1000000})
        if search_similar:
            # TODO: FIGURE OUT WHAT TYPE TO KEEP LATER
            craw_links = self.web_searcher.search(query = url, type = "fast", num_results = config.MAX_SIMILAR_URLS)
            discovered_urls = [results.url for results in craw_links.results]
            deep_content = self.web_searcher.get_contents(urls = discovered_urls, text = {"max_characters": 1000000})
            
            return primary_page + "\n" + deep_content
        return primary_page
        
    def convert_to_markdown(self, Tenant_name: str, search_reponse: SearchResponse):
        if not Path(config.DATA_DIR / "WebSearches").exists():
            Path(config.DATA_DIR / "WebSearches").mkdir(parents = True, exist_ok = True)
        md_file = Tenant_name + "_WebSearch.md"
        file_path = Path(config.DATA_DIR / "WebSearches" / md_file)
        
        with open(file_path = file_path, mode = "w", encoding = 'utf-8') as f:
            f.write("# Web search content form Tenant provided URL and or similar URL content\n\n")
            f.write("---\n\n")
            f.write("# CONTENT")
            for content in search_reponse.results:
                f.write(f"### {content.title}\n")
                f.write(f"**URL:** [{content.url}]({content.url})\n\n")
                f.write(f"{content.text}\n\n")
        

if __name__ == "__main__":
    web_searcher = Exa(api_key = config.EXA_API_KEY)
    print(type(web_searcher.get_contents(urls = "https://en.wikipedia.org/wiki/Proximal_policy_optimization", text = {"max_characters": 100})))
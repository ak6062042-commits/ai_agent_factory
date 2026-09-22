from openai import OpenAI
from backend.app.config import OPENAI_API_KEY, MODEL_VERSION, EMBEDDING_CLIENT, MAX_TOKEN, TEMPERATURE, TOP_P


class LLMClient:
    def __init__(self, model: str = MODEL_VERSION):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def generate(self, messages: list, max_tokens: int = MAX_TOKEN, temperature: float = TEMPERATURE, top_p: float = TOP_P) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages,
            max_completion_tokens=max_tokens, temperature=temperature, top_p=top_p,
        )
        return response.choices[0].message.content.strip()


class EmbeddingClient:
    def __init__(self, model: str = EMBEDDING_CLIENT):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [r.embedding for r in response.data]
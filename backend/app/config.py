from pathlib import Path
from os import getenv
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
WORKSPACE = BACKEND_DIR.parent
ENV_PATH = WORKSPACE / ".env"

if not Path(BACKEND_DIR / "data").exists():
    Path(BACKEND_DIR / "data").mkdir(parents = True, exist_ok = True)
    

DATA_DIR = BACKEND_DIR / "data"

EMBEDDING_CLIENT = "text-embedding-3-small"
MODEL_VERSION = "gpt-4o-mini"
MAX_SIMILAR_URLS = 5


load_dotenv(ENV_PATH)
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
EXA_API_KEY = getenv("EXA_API_KEY")
DATABASE_URL = getenv("DATABASE_URL")

MAX_UPLOADS = 5
MAX_TOKEN = 1500
TEMPERATURE  = 0.3
REASONING_EFFOR = ["minimal", "low", "medium"]
TOP_P = 0.9
TOP_K = 0

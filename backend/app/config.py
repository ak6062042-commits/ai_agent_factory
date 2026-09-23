from pathlib import Path
from os import getenv
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
WORKSPACE = BACKEND_DIR.parent
ENV_PATH = WORKSPACE / ".env"

if not Path(BACKEND_DIR / "data").exists():
    from backend.log.logger import Logger
    logger = Logger()
    logger.log(f"Creating a data directory at path: {Path(BACKEND_DIR / 'data')}")
    Path(BACKEND_DIR / "data").mkdir(parents=True, exist_ok=True)


DATA_DIR = BACKEND_DIR / "data"

EMBEDDING_CLIENT = "text-embedding-3-small"
MODEL_VERSION = "gpt-4o-mini"
MAX_SIMILAR_URLS = 5

load_dotenv(ENV_PATH)
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
EXA_API_KEY = getenv("EXA_API_KEY")
DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"
MASTER_KEY = getenv("MASTER_KEY")

MAX_UPLOADS = 5
MAX_TOKEN = 1500
TEMPERATURE = 0.3
REASONING_EFFOR = ["minimal", "low", "medium"]
TOP_P = 0.9
TOP_K = 0
SIMILARITY_THRESHOLD = 0.65 # Place holder will figure out a sweet spot later after tests (is done not a place holder anymore)

KEEP_CHAT_SESSION = 10
CHUNK_SIZE = 500
OVERLAP = 50
VECTOR_DB_PATH = str(DATA_DIR / "chroma")
COLLECTION_NAME = "agent_knowledge"
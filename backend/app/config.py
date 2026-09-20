from pathlib import Path
from os import getenv
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
WORKSPACE = BACKEND_DIR.parent
ENV_PATH = WORKSPACE / ".env"
DATA_DIR = BACKEND_DIR / "data"
MODEL_VERSION = "gpt-4o-mini"


load_dotenv(ENV_PATH)
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
EXA_API_KEY = getenv("EXA_API_KEY")
DATABASE_URL = getenv("DATABASE_URL")

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "interview_accelerator.db"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMENI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")

class Config:
    DB_PATH = DB_PATH
    GEMINI_API_KEY = GEMINI_API_KEY
    OPENAI_API_KEY = OPENAI_API_KEY
    LLM_PROVIDER = LLM_PROVIDER
    DEFAULT_MODEL = DEFAULT_MODEL

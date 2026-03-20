import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env.bot.secret if it exists, otherwise fall back to .env.bot.example
_env_secret = Path(__file__).parent.parent / ".env.bot.secret"
_env_example = Path(__file__).parent.parent / ".env.bot.example"

if _env_secret.exists():
    load_dotenv(_env_secret)
elif _env_example.exists():
    load_dotenv(_env_example)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LMS_API_URL = os.getenv("LMS_API_URL", "http://localhost:42002")
LMS_API_KEY = os.getenv("LMS_API_KEY", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "http://localhost:42005/v1")
LLM_API_MODEL = os.getenv("LLM_API_MODEL", "coder-model")

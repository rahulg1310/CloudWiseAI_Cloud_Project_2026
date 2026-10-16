import os
import secrets
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cloudwise")

# In production always set JWT_SECRET. If it's missing we generate one,
# which means every login is invalidated whenever the server restarts.
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    JWT_SECRET = secrets.token_hex(32)
    print("WARNING: JWT_SECRET not set - using a temporary secret (logins reset on restart).")

JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = int(os.environ.get("TOKEN_EXPIRE_HOURS", "24"))

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174").split(",") if o.strip()]

# ---- AI assistant (LLM) -------------------------------------------------------
# LLM_PROVIDER: "anthropic" (Claude), "openai" or "ollama" (a local model, no key needed).
# Anthropic and OpenAI are disabled until LLM_API_KEY is set.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()

_DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini", "ollama": "llama3.1:8b"}
_DEFAULT_URLS = {"anthropic": "https://api.anthropic.com", "openai": "https://api.openai.com",
                 "ollama": "http://localhost:11434"}

LLM_MODEL = os.environ.get("LLM_MODEL", "").strip() or _DEFAULT_MODELS.get(LLM_PROVIDER, "")
LLM_BASE_URL = (os.environ.get("LLM_BASE_URL", "").strip() or _DEFAULT_URLS.get(LLM_PROVIDER, "")).rstrip("/")
# A local model can take a minute to load on the first question, so Ollama gets a longer default.
LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "120" if LLM_PROVIDER == "ollama" else "40"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "700"))

# Ollama's default context window (2048-4096 tokens) is smaller than our data snapshot, and it
# silently drops the overflow. This sets a window big enough for snapshot + history + reply.
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))


def llm_is_configured():
    """Ollama runs locally and needs no key; the hosted providers do."""
    return LLM_PROVIDER == "ollama" or bool(LLM_API_KEY)

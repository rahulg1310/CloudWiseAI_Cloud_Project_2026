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

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

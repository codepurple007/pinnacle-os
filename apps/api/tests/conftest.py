import os
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[2]
key = os.environ.get("TOKEN_ENCRYPTION_KEY")
if not key:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TOKEN_ENCRYPTION_KEY="):
                key = line.split("=", 1)[1].strip()
                break
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", key or Fernet.generate_key().decode())
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://pinnacle:pinnacle@localhost:5432/pinnacleos",
)
os.environ.setdefault("DEV_INGEST_ENABLED", "true")

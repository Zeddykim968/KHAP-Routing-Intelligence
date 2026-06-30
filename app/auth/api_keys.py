"""
API key generation and validation using local PostgreSQL.
Format: khap_<32 hex chars>
"""

import secrets
import hashlib
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.services.db import query_one

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
KEY_PREFIX = "khap_"


def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, hashed_key). Store hash; give raw to client."""
    raw = KEY_PREFIX + secrets.token_hex(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def validate_api_key(key: str = Security(API_KEY_HEADER)):
    """FastAPI dependency — validates API key against local DB."""
    if not key:
        return None
    hashed = hashlib.sha256(key.encode()).hexdigest()
    try:
        row = query_one(
            "SELECT * FROM api_keys WHERE key_hash=%s AND is_active=TRUE", [hashed]
        )
        if row:
            return row
    except Exception:
        pass
    raise HTTPException(status_code=401, detail="Invalid API key")

"""
V3 Auth API — login, token refresh, API key management.
Uses JWT for session tokens. API keys stored in local PostgreSQL.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel, EmailStr
from app.auth.jwt import create_access_token, get_current_user
from app.auth.passwords import hash_password, verify_password
from app.auth.api_keys import generate_api_key
from app.services.db import query_one, execute
from app.cache.rate_limit import limiter

router = APIRouter(prefix="/api/v3/auth", tags=["V3 · Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    """
    Demo login — returns a JWT. For a real deployment wire this to
    Supabase Auth or your own users table with hashed passwords.
    """
    # In a full deployment: verify against a `users` table with hashed passwords.
    # Here we issue a token with the email as sub so the API is testable.
    token = create_access_token({
        "sub": body.email,
        "email": body.email,
        "role": "user",
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": body.email, "role": "user"},
        "note": "Demo mode — integrate with your auth provider for production.",
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}


@router.post("/api-keys")
def create_api_key(
    name: str = Body(..., embed=True),
    user: dict = Depends(get_current_user),
):
    raw, hashed = generate_api_key()
    try:
        execute(
            "INSERT INTO api_keys (user_id, name, key_hash, is_active) VALUES (%s,%s,%s,%s)",
            [user.get("sub"), name, hashed, True],
        )
    except Exception as e:
        raise HTTPException(500, f"Could not save API key: {e}")
    return {
        "api_key": raw,
        "note": "Store this key safely — it will not be shown again.",
        "name": name,
    }


@router.delete("/api-keys/{key_name}")
def revoke_api_key(key_name: str, user: dict = Depends(get_current_user)):
    execute(
        "UPDATE api_keys SET is_active=FALSE WHERE user_id=%s AND name=%s",
        [user.get("sub"), key_name],
    )
    return {"message": f"API key '{key_name}' revoked"}

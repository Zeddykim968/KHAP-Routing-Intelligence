"""
Rate limiting using slowapi (Starlette-compatible limiter).
Default: 60 requests/minute per IP for public endpoints.
Authenticated endpoints get 300 requests/minute.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

PUBLIC_LIMIT = "60/minute"
AUTH_LIMIT = "300/minute"
ANALYTICS_LIMIT = "30/minute"

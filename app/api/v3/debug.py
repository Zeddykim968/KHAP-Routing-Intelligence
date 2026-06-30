"""Temporary debug endpoint — remove after testing."""
from fastapi import APIRouter
import socket, os, httpx

router = APIRouter(prefix="/api/v3/debug", tags=["Debug"])

@router.get("/dns")
async def test_dns():
    host = os.getenv("SUPABASE_URL", "").replace("https://", "").split("/")[0]
    results = {}
    try:
        ip = socket.getaddrinfo(host, 443, socket.AF_INET)[0][4][0]
        results["socket_dns"] = f"OK: {ip}"
    except Exception as e:
        results["socket_dns"] = f"FAIL: {e}"
    try:
        async with httpx.AsyncClient() as c:
            key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
            r = await c.get(
                f"https://{host}/rest/v1/facilities",
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
                params={"select": "county", "limit": "2"},
                timeout=10,
            )
            results["httpx_async"] = f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        results["httpx_async"] = f"FAIL: {e}"
    return results

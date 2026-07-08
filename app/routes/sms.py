"""
SMS handler compatible with Africa's Talking (AT) SMS callbacks.

AT sends incoming SMS as a form-encoded POST:
  from=+254700000000&text=FIND+NAIROBI&date=...&id=...&linkId=...&to=KHAP

Commands:
  HELP / HI / HELLO / START   — usage instructions
  FIND [county]               — list facilities in a county
  FIND [county] [type]        — filter by type (HOSPITAL, CLINIC, DISPENSARY, MATERNITY, DENTAL, LAB)
"""

from fastapi import APIRouter, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.services.supabase_service import fetch_all

router = APIRouter(prefix="/sms", tags=["SMS"])

TYPE_MAP = {
    "HOSPITAL":   "District Hospital",
    "CLINIC":     "Medical Clinic",
    "DISPENSARY": "Dispensary",
    "MATERNITY":  "Maternity Home",
    "DENTAL":     "Dental Clinic",
    "CENTRE":     "Health Centre",
    "CENTER":     "Health Centre",
    "LAB":        "Laboratory (Stand-alone)",
    "EYE":        "Eye Centre",
}

HELP_TEXT = (
    "KHAP Facility Finder:\n"
    "FIND [county] - list facilities\n"
    "FIND [county] [type] - filter type\n"
    "Types: HOSPITAL CLINIC DISPENSARY MATERNITY DENTAL LAB\n"
    "Example: FIND NAIROBI HOSPITAL\n"
    "Web: kenya-health-access.vercel.app"
)


def _process(text: str, phone: str = "") -> dict:
    """Parse command text and return a response dict."""
    parts = text.strip().upper().split()
    cmd = parts[0] if parts else ""

    if not cmd or cmd in ("HELP", "HI", "HELLO", "START", "MENU"):
        return {"to": phone, "message": HELP_TEXT, "sender": "KHAP"}

    if cmd == "FIND" and len(parts) >= 2:
        county = parts[1].title()
        facility_type = TYPE_MAP.get(parts[2]) if len(parts) >= 3 else None

        filters: dict = {"operational_status": "Operational", "county": county}
        if facility_type:
            filters["type"] = facility_type

        rows = fetch_all(columns="name,nearest_town,type", filters=filters)

        if not rows:
            return {
                "to": phone,
                "message": f"No facilities found in {county}. Check spelling or try: FIND NAIROBI",
                "sender": "KHAP",
            }

        label = f"{facility_type or 'All'} in {county}"
        lines = [f"KHAP — {label} ({len(rows)} found):"]
        for f in rows[:4]:
            town = f.get("nearest_town", "")
            name = f.get("name", "")
            lines.append(f"• {name}" + (f", {town}" if town else ""))
        if len(rows) > 4:
            lines.append(f"...and {len(rows) - 4} more.")
        lines.append("Reply HELP for commands.")

        return {"to": phone, "message": "\n".join(lines), "sender": "KHAP"}

    return {
        "to": phone,
        "message": "Unknown command. Reply HELP for instructions.\nKHAP - Kenya Health Access Platform",
        "sender": "KHAP",
    }


# ── Africa's Talking webhook (form-encoded) ───────────────────────────────────

@router.post("/webhook", summary="Africa's Talking SMS callback (form-encoded POST)")
def sms_webhook_at(
    From: str  = Form(..., alias="from"),
    text: str  = Form(""),
    date: str  = Form(""),
    id:   str  = Form(""),
    linkId: str = Form(""),
    to:   str  = Form(""),
):
    """
    Receives incoming SMS from Africa's Talking.
    AT sends: from, text, date, id, linkId, to — all form-encoded.
    Returns JSON with `to`, `message`, `sender` for the Django platform
    to forward back via the AT SDK.
    """
    return _process(text, From)


# ── JSON API (for Django platform / direct calls) ────────────────────────────

class SMSRequest(BaseModel):
    message: str
    phone: str = ""


@router.post("", summary="SMS command handler (JSON body)")
def handle_sms(payload: SMSRequest = Body(...)):
    """
    JSON variant — used by the Django platform or direct API calls.
    Body: {"message": "FIND NAIROBI HOSPITAL", "phone": "+254700000000"}
    """
    return _process(payload.message, payload.phone)

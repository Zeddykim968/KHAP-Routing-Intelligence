from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.services.supabase_service import fetch_all
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/sms", tags=["SMS"])


class SMSRequest(BaseModel):
    message: str
    phone: str = ""


def build_sms_response(facilities, county: str = None):
    if not facilities:
        return "No facilities found. Try a different county or service type. Reply HELP for instructions."

    lines = [f"KHAP - Top facilities{' in ' + county if county else ''}:"]
    for i, (score, dist, f) in enumerate(facilities[:4], 1):
        dist_text = f" ~{dist}km" if dist else ""
        lines.append(f"{i}. {f['name']}{dist_text} - {f.get('nearest_town', '')}")
    lines.append("Reply with a number for more details. khap.co.ke")
    return "\n".join(lines)


@router.post("")
def handle_sms(payload: SMSRequest = Body(...)):
    message = payload.message.strip().upper()
    parts = message.split()

    if message in ("HELP", "HI", "HELLO", "START"):
        return {
            "response": (
                "KHAP Help:\n"
                "FIND [county] - List facilities in a county\n"
                "FIND [county] [type] - Filter by type\n"
                "Types: HOSPITAL, CLINIC, DISPENSARY, MATERNITY, DENTAL\n"
                "Example: FIND NAIROBI HOSPITAL"
            )
        }

    if parts and parts[0] == "FIND" and len(parts) >= 2:
        county = parts[1].title()
        facility_type = None

        type_map = {
            "HOSPITAL":   "District Hospital",
            "CLINIC":     "Medical Clinic",
            "DISPENSARY": "Dispensary",
            "MATERNITY":  "Maternity Home",
            "DENTAL":     "Dental Clinic",
            "CENTRE":     "Health Centre",
            "CENTER":     "Health Centre",
            "LAB":        "Laboratory (Stand-alone)",
        }

        if len(parts) >= 3:
            facility_type = type_map.get(parts[2].upper())

        filters: dict = {"operational_status": "Operational", "county": county}
        if facility_type:
            filters["type"] = facility_type

        facilities = fetch_all(filters=filters)

        if not facilities:
            return {"response": f"No facilities found in {county}. Check spelling and try again."}

        result_list = [(0, 0, f) for f in facilities[:4]]
        return {"response": build_sms_response(result_list, county)}

    return {
        "response": "Unknown command. Reply HELP for instructions. KHAP - Kenya Health Access Platform"
    }


@router.post("/webhook")
def sms_webhook(payload: dict = Body(...)):
    text = payload.get("text", payload.get("message", "")).strip().upper()
    phone = payload.get("from", payload.get("phone", ""))

    fake_request = SMSRequest(message=text, phone=phone)
    result = handle_sms(fake_request)

    return {
        "to": phone,
        "message": result["response"],
        "sender": "KHAP",
    }

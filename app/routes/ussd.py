from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse
from app.services.supabase_service import supabase
from app.services.location_service import resolve_location
from app.recommendation_engine import calculate_score

router = APIRouter(prefix="/ussd", tags=["USSD"])

COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo Marakwet", "Embu",
    "Garissa", "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho",
    "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui",
    "Kwale", "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera",
    "Marsabit", "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi",
    "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua", "Nyeri",
    "Samburu", "Siaya", "Taita Taveta", "Tana River", "Tharaka Nithi",
    "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot",
]

SERVICES = [
    "Any Facility",
    "Hospital",
    "Health Centre",
    "Medical Clinic",
    "Dispensary",
    "Maternity Home",
    "Dental Clinic",
    "Eye Centre",
    "Laboratory",
]

SERVICE_TYPE_MAP = {
    "1": None,
    "2": "District Hospital",
    "3": "Health Centre",
    "4": "Medical Clinic",
    "5": "Dispensary",
    "6": "Maternity Home",
    "7": "Dental Clinic",
    "8": "Eye Centre",
    "9": "Laboratory (Stand-alone)",
}

PAGE_SIZE = 10


def county_page_menu(page: int) -> str:
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(COUNTIES))
    lines = ["CON Select your county:"]
    for i in range(start, end):
        lines.append(f"{i + 1}. {COUNTIES[i]}")
    if end < len(COUNTIES):
        lines.append("98. Next page")
    if page > 0:
        lines.append("97. Prev page")
    return "\n".join(lines)


def service_menu(prefix: str) -> str:
    lines = [f"CON {prefix}\nSelect service type:"]
    for i, svc in enumerate(SERVICES, 1):
        lines.append(f"{i}. {svc}")
    return "\n".join(lines)


@router.post("", response_class=PlainTextResponse)
def ussd_handler(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
):
    parts = [p for p in text.split("*") if p] if text else []
    level = len(parts)

    # ── Level 0 — Welcome ────────────────────────────────────────────────────
    if level == 0:
        return (
            "CON Welcome to KHAP\n"
            "Kenya Health Access Platform\n\n"
            "1. Find nearby facility\n"
            "2. Search by county\n"
            "99. Exit"
        )

    # ── Level 1 — Main menu choice ───────────────────────────────────────────
    if level == 1:
        choice = parts[0]
        if choice == "1":
            return (
                "CON Enter your town or area name:\n"
                "e.g. Westlands, Kisumu, Eldoret,\n"
                "Nakuru, Mombasa, Thika..."
            )
        elif choice == "2":
            return county_page_menu(0)
        elif choice == "99":
            return "END Thank you for using KHAP.\nStay healthy!"
        else:
            return "CON Invalid choice.\n1. Find nearby facility\n2. Search by county\n99. Exit"

    # ── NEARBY FLOW (parts[0] == "1") ────────────────────────────────────────

    # Level 2 — location name entered, resolve it
    if level == 2 and parts[0] == "1":
        location_name = parts[1].strip()
        resolved = resolve_location(location_name)
        if not resolved:
            return (
                "CON Location not found.\n"
                "Please try a nearby town:\n"
                "e.g. Westlands, Kisumu, Thika"
            )
        return service_menu(f"Location: {resolved['label']}")

    # Level 3 — service selected, return results
    if level == 3 and parts[0] == "1":
        location_name = parts[1].strip()
        resolved = resolve_location(location_name)
        if not resolved:
            return "END Location not found. Dial again and try a different town."

        lat, lon = resolved["latitude"], resolved["longitude"]
        service_choice = parts[2]
        facility_type = SERVICE_TYPE_MAP.get(service_choice)

        query = supabase.table("facilities").select("*").eq("operational_status", "Operational")
        if facility_type:
            query = query.eq("type", facility_type)
        response = query.execute()
        facilities = [f for f in response.data if f.get("latitude") and f.get("longitude")]

        scored = []
        for f in facilities:
            score, dist = calculate_score(f, lat, lon)
            if dist <= 50:
                scored.append((score, dist, f))
        scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)

        if not scored:
            return "END No facilities found within 50km.\nTry a different service type."

        lines = [f"END Nearest to {resolved['label']}:"]
        for _, dist, f in scored[:4]:
            lines.append(f"- {f['name']} ({dist}km)")
            if f.get("nearest_town"):
                lines.append(f"  {f['nearest_town']}")
        return "\n".join(lines)

    # ── COUNTY FLOW (parts[0] == "2") ────────────────────────────────────────

    # Level 2 — county or page navigation
    if level == 2 and parts[0] == "2":
        choice = parts[1]
        if choice == "98":
            return county_page_menu(1)
        if choice == "97":
            return county_page_menu(0)
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(COUNTIES):
                raise ValueError
            county = COUNTIES[idx]
        except Exception:
            return "END Invalid county selection. Please try again."
        return service_menu(f"County: {county}")

    # Level 3 — service selected, return county results
    if level == 3 and parts[0] == "2":
        try:
            idx = int(parts[1]) - 1
            county = COUNTIES[idx]
        except Exception:
            return "END Invalid county selection."

        service_choice = parts[2]
        facility_type = SERVICE_TYPE_MAP.get(service_choice)

        query = (
            supabase.table("facilities")
            .select("name,nearest_town,type")
            .eq("operational_status", "Operational")
            .eq("county", county)
        )
        if facility_type:
            query = query.eq("type", facility_type)
        response = query.execute()
        facilities = response.data

        if not facilities:
            return f"END No facilities found in {county}.\nTry a different service type."

        lines = [f"END Facilities in {county}:"]
        for f in facilities[:5]:
            town = f.get("nearest_town", "")
            lines.append(f"- {f['name']}")
            if town:
                lines.append(f"  {town}")
        if len(facilities) > 5:
            lines.append(f"...and {len(facilities) - 5} more.")
        return "\n".join(lines)

    return "END Session ended.\nDial *384*43149# to start again."

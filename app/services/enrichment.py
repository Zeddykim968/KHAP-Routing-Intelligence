"""
Derives enrichment fields (insurance, financial level, emergency capabilities)
from existing facility data since the source CSV does not carry these fields.
"""

INSURANCE_BY_OWNER = {
    "government":  ["NHIF", "SHA"],
    "ministry":    ["NHIF", "SHA"],
    "county":      ["NHIF", "SHA"],
    "mission":     ["NHIF", "SHA", "CIC", "Jubilee", "AAR"],
    "church":      ["NHIF", "SHA", "CIC", "Jubilee"],
    "catholic":    ["NHIF", "SHA", "CIC", "Jubilee", "AAR"],
    "protestant":  ["NHIF", "SHA", "CIC"],
    "episcopal":   ["NHIF", "SHA", "CIC"],
    "adventist":   ["NHIF", "SHA", "CIC", "Jubilee"],
    "aga khan":    ["NHIF", "SHA", "AAR", "Jubilee", "APA", "CIC", "Madison", "Resolution", "Britam", "UAP", "Medigold"],
    "ngo":         ["NHIF", "SHA"],
    "private":     ["NHIF", "SHA", "AAR", "Jubilee", "APA", "CIC", "Madison", "Resolution", "Britam", "UAP", "Medigold"],
}

FINANCIAL_LEVELS = {
    "government": "Low",
    "ministry":   "Low",
    "county":     "Low",
    "ngo":        "Free/Subsidized",
    "mission":    "Medium",
    "church":     "Medium",
    "catholic":   "Medium",
    "protestant": "Medium",
    "episcopal":  "Medium",
    "adventist":  "Medium",
    "private":    "High",
    "aga khan":   "High",
}

# Emergency type → preferred facility types (ordered by suitability)
EMERGENCY_CAPABILITIES = {
    "cardiac": {
        "label":           "Cardiac / Heart Attack",
        "preferred_types": ["Provincial General Hospital", "National Referral Hospital", "District Hospital", "Sub-District Hospital", "Medical Centre"],
        "type_score":      100,
        "requires_24h":    True,
        "min_beds":        20,
        "icon":            "❤️",
    },
    "trauma": {
        "label":           "Trauma / Road Accident",
        "preferred_types": ["District Hospital", "Provincial General Hospital", "National Referral Hospital", "Sub-District Hospital", "Other Hospital"],
        "type_score":      100,
        "requires_24h":    True,
        "min_beds":        10,
        "icon":            "🚑",
    },
    "maternity": {
        "label":           "Maternity / Childbirth",
        "preferred_types": ["Maternity Home", "District Hospital", "Health Centre", "Sub-District Hospital", "Medical Centre"],
        "type_score":      100,
        "requires_24h":    False,
        "min_beds":        2,
        "icon":            "🤰",
    },
    "pediatric": {
        "label":           "Pediatric / Child Emergency",
        "preferred_types": ["District Hospital", "Health Centre", "Medical Centre", "Provincial General Hospital"],
        "type_score":      100,
        "requires_24h":    True,
        "min_beds":        5,
        "icon":            "👶",
    },
    "mental_health": {
        "label":           "Mental Health Crisis",
        "preferred_types": ["District Hospital", "Medical Centre", "Health Centre", "Provincial General Hospital"],
        "type_score":      80,
        "requires_24h":    False,
        "min_beds":        10,
        "icon":            "🧠",
    },
    "dental": {
        "label":           "Dental Emergency",
        "preferred_types": ["Dental Clinic", "District Hospital", "Medical Centre", "Health Centre"],
        "type_score":      100,
        "requires_24h":    False,
        "min_beds":        0,
        "icon":            "🦷",
    },
    "eye": {
        "label":           "Eye Emergency",
        "preferred_types": ["Eye Centre", "District Hospital", "Medical Centre"],
        "type_score":      100,
        "requires_24h":    False,
        "min_beds":        0,
        "icon":            "👁️",
    },
    "general": {
        "label":           "General Emergency",
        "preferred_types": None,
        "type_score":      50,
        "requires_24h":    False,
        "min_beds":        0,
        "icon":            "🏥",
    },
}

ALL_INSURANCE_PROVIDERS = sorted({
    ins
    for providers in INSURANCE_BY_OWNER.values()
    for ins in providers
})


def get_insurance_providers(owner: str) -> list[str]:
    """Return list of insurance providers accepted by this facility."""
    o = (owner or "").lower()
    for key, providers in INSURANCE_BY_OWNER.items():
        if key in o:
            return providers
    return ["NHIF", "SHA"]


def get_financial_level(owner: str) -> str:
    """Return estimated financial tier: Low / Medium / High / Free/Subsidized."""
    o = (owner or "").lower()
    for key, level in FINANCIAL_LEVELS.items():
        if key in o:
            return level
    return "Medium"


def enrich_facility(facility: dict) -> dict:
    """Add insurance_providers and financial_level to a facility dict."""
    owner = facility.get("owner", "")
    facility["insurance_providers"] = get_insurance_providers(owner)
    facility["financial_level"]     = get_financial_level(owner)
    return facility


def emergency_type_score(facility: dict, emergency_type: str) -> float:
    """
    Returns 0–100 score for how well this facility matches the given emergency type.
    """
    if emergency_type not in EMERGENCY_CAPABILITIES:
        return 50

    cfg = EMERGENCY_CAPABILITIES[emergency_type]
    ftype = facility.get("type", "")
    preferred = cfg["preferred_types"]

    if preferred is None:
        base = 60
    elif ftype == preferred[0]:
        base = 100
    elif ftype in preferred:
        idx = preferred.index(ftype)
        base = max(40, 100 - idx * 15)
    else:
        base = 10

    if cfg["requires_24h"] and facility.get("open_24_hours"):
        base += 10

    beds = (facility.get("beds") or 0) + (facility.get("cots") or 0)
    if cfg["min_beds"] > 0 and beds < cfg["min_beds"]:
        base *= 0.6

    return min(100, base)

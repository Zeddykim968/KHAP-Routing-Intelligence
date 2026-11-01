"""
Seed the KHAP database with reference service/insurance catalogues and a
representative set of Kenyan health facilities.

Run:  python manage.py seed_facilities
Idempotent — records are matched by (name, town) and updated in place.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from facilities.models import Facility, Insurance, Service

# ── Service catalogue ─────────────────────────────────────────────────────────
SERVICES = [
    ("outpatient", "Outpatient Services", "stethoscope", "care", 1),
    ("inpatient", "Inpatient Ward", "bed", "care", 2),
    ("emergency", "24h Emergency Unit", "siren", "care", 3),
    ("maternity", "Maternity & Delivery", "baby", "specialist", 4),
    ("surgery", "Surgical Theatre", "scissors", "specialist", 5),
    ("pharmacy", "Pharmacy & Dispensary", "pill", "care", 6),
    ("laboratory", "Laboratory & Testing", "flask-conical", "diagnostics", 7),
    ("imaging", "X-Ray & Imaging", "scan-line", "diagnostics", 8),
    ("ultrasound", "Ultrasound Scan", "waves", "diagnostics", 9),
    ("icu", "Intensive Care (ICU)", "heart-pulse", "care", 10),
    ("dental", "Dental Clinic", "smile", "specialist", 11),
    ("eye", "Eye Clinic", "eye", "specialist", 12),
    ("pediatric", "Children's Unit", "baby-face", "specialist", 13),
    ("family_planning", "Family Planning", "calendar-heart", "care", 14),
    ("vaccination", "Vaccination & Immunization", "syringe", "care", 15),
    ("physiotherapy", "Physiotherapy", "accessibility", "specialist", 16),
    ("dialysis", "Dialysis & Kidney Care", "droplets", "specialist", 17),
    ("oncology", "Cancer Care (Oncology)", "ribbon", "specialist", 18),
    ("mental_health", "Mental Health Services", "brain", "specialist", 19),
    ("hiv_tb", "HIV & TB Clinic", "virus", "care", 20),
    ("ncd", "Chronic Disease Clinic", "activity-heartbeat", "care", 21),
    ("mch", "Mother & Child Health", "heart-handshake", "care", 22),
    ("ambulance", "Ambulance Services", "truck", "support", 23),
    ("telemedicine", "Telemedicine", "video", "support", 24),
]

# ── Insurance catalogue ───────────────────────────────────────────────────────
INSURERS = [
    ("sha", "Social Health Authority (SHA)", "public", 1),
    ("nhif", "NHIF (Legacy scheme)", "public", 2),
    ("self", "Cash / Self-pay", "self", 3),
    ("jubilee", "Jubilee Afya", "private", 4),
    ("aar", "AAR Insurance", "private", 5),
    ("madison", "Madison Insurance", "private", 6),
    ("britam", "Britam Health Protect", "private", 7),
    ("resolution", "Resolution Health", "private", 8),
    ("cic", "CIC Health Insurance", "private", 9),
    ("uap", "UAP Old Mutual Health", "private", 10),
]

# Convenience service bundles --------------------------------------------------
HOSPITAL_CORE = [
    "outpatient", "inpatient", "emergency", "maternity", "surgery", "pharmacy",
    "laboratory", "imaging", "ultrasound", "icu", "pediatric", "vaccination",
    "physiotherapy", "ambulance", "mch",
]
HOSPITAL_EXTRA = ["dental", "eye", "dialysis", "oncology", "mental_health", "hiv_tb", "ncd", "family_planning"]
CLINIC_SVCS = ["outpatient", "pharmacy", "laboratory", "vaccination", "family_planning", "ncd", "hiv_tb", "mch", "telemedicine"]
HEALTH_CENTRE_SVCS = ["outpatient", "maternity", "pharmacy", "laboratory", "ultrasound", "vaccination", "family_planning", "mch"]
DISPENSARY_SVCS = ["outpatient", "pharmacy", "vaccination", "family_planning"]
PHARMACY_SVCS = ["pharmacy", "vaccination", "laboratory", "telemedicine"]

PRIVATE_ALL = ["sha", "jubilee", "aar", "madison", "britam", "resolution", "cic", "uap", "self"]
GOVERNMENT = ["sha", "nhif", "self"]
MISSION = ["sha", "nhif", "jubilee", "aar", "madison", "britam", "self"]

# ── Facilities ────────────────────────────────────────────────────────────────
# Representative dataset: real facility names with approximate coordinates,
# services and accepted insurers for demonstration of the KHAP workflow.
FACILITIES = [
    # ── Nairobi ───────────────────────────────────────────────────────────────
    dict(
        name="Kenyatta National Hospital", type="hospital",
        operator="Government — National Referral", phone="+254 20 271 4400",
        website="https://www.knh.ac.ke", address="Hospital Road, Upper Hill",
        town="Nairobi", county="Nairobi", emergency="yes", hours="24/7",
        wheelchair="limited", lat=-1.3012, lon=36.8065,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA + ["family_planning"],
        ins=GOVERNMENT + ["jubilee", "aar", "madison", "britam", "cic", "uap"],
    ),
    dict(
        name="Aga Khan University Hospital", type="hospital",
        operator="Aga Khan Health Service", phone="+254 20 366 2000",
        website="https://www.aku.edu", address="3rd Parklands Avenue",
        town="Nairobi", county="Nairobi", emergency="yes", hours="24/7",
        wheelchair="yes", lat=-1.2617, lon=36.8037,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA,
        ins=["sha", "self", "jubilee", "aar", "madison", "britam", "resolution", "cic", "uap"],
    ),
    dict(
        name="The Nairobi Hospital", type="hospital",
        operator="Nairobi Hospital Ltd", phone="+254 20 271 5600",
        address="Argwings Kodhek Road, Upper Hill", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-1.2837, lon=36.8170,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA,
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="MP Shah Hospital", type="hospital",
        operator="Jubilee Insurance Hospitals", phone="+254 20 271 0000",
        address="Desai Road, Parklands", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-1.2757, lon=36.8085,
        sv=HOSPITAL_CORE + ["dental", "eye", "mental_health", "ncd"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="The Karen Hospital", type="hospital",
        operator="The Karen Hospital Ltd", phone="+254 20 271 2000",
        website="https://www.karenhospital.org", address="Karen Road, Karen",
        town="Nairobi", county="Nairobi", emergency="yes", hours="24/7",
        wheelchair="yes", lat=-1.3217, lon=36.7099,
        sv=HOSPITAL_CORE + ["dental", "eye", "oncology", "mental_health"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Nairobi Women's Hospital — Kilimani", type="hospital",
        operator="Nairobi Women's Hospital", phone="+254 709 050 000",
        address="Ring Road, Kilimani", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-1.2947, lon=36.7847,
        sv=["outpatient", "inpatient", "emergency", "maternity", "surgery", "pharmacy",
            "laboratory", "ultrasound", "pediatric", "family_planning", "vaccination", "mch"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Mbagathi County Referral Hospital", type="hospital",
        operator="Nairobi County Government", phone="+254 20 272 5711",
        address="Mbagathi Way, Kibera", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.3105, lon=36.7905,
        sv=HOSPITAL_CORE + ["hiv_tb", "ncd", "mental_health"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Gertrude's Children's Hospital", type="hospital",
        operator="Gertrude's Hospital Foundation", phone="+254 20 720 6000",
        address="Muthaiga Road, Muthaiga", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Su 08:00-20:00", wheelchair="yes",
        lat=-1.2543, lon=36.8056,
        sv=["outpatient", "inpatient", "pharmacy", "laboratory", "imaging", "ultrasound",
            "icu", "pediatric", "vaccination", "emergency"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Kikuyu Mission Hospital", type="hospital",
        operator="PCEA — Church", phone="+254 720 600 000",
        website="https://www.kikuyumissionhospital.org", address="Kikuyu Town, Waiyaki Way",
        town="Kikuyu", county="Kiambu", emergency="yes", hours="24/7",
        wheelchair="limited", lat=-1.2432, lon=36.6984,
        sv=HOSPITAL_CORE + ["dental", "hiv_tb", "mental_health"],
        ins=MISSION,
    ),
    dict(
        name="PCEA Kikuyu Hospital", type="hospital",
        operator="PCEA — Church", phone="+254 720 600 100",
        address="Kikuyu Town", town="Kikuyu", county="Kiambu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.2474, lon=36.6990,
        sv=HOSPITAL_CORE + ["eye", "dental", "hiv_tb"],
        ins=MISSION,
    ),
    dict(
        name="St. Mary's Mission Hospital Langata", type="hospital",
        operator="Catholic Archdiocese of Nairobi", phone="+254 20 530 000",
        address="Langata Road", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.3463, lon=36.7489,
        sv=HOSPITAL_CORE + ["hiv_tb", "ncd"],
        ins=MISSION,
    ),
    dict(
        name="Mathare National Teaching & Referral Hospital", type="hospital",
        operator="Government — National Referral", phone="+254 20 675 000",
        address="Mathare North Road", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.2695, lon=36.8656,
        sv=["outpatient", "inpatient", "emergency", "pharmacy", "laboratory", "icu",
            "mental_health", "hiv_tb", "ncd", "ambulance"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Mama Lucy Kibaka Hospital", type="hospital",
        operator="Nairobi County Government", phone="+254 700 000 000",
        address="Umoja Outer Ring Road", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.2607, lon=36.8891,
        sv=HOSPITAL_CORE + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Ruaraka Uhai Neema Hospital", type="hospital",
        operator="Neema Hospital Foundation", phone="+254 709 800 000",
        address="Outer Ring Road, Ruaraka", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-1.2477, lon=36.8550,
        sv=HOSPITAL_CORE + ["dental", "hiv_tb"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Mater Misericordiae Hospital", type="hospital",
        operator="Sisters of Mercy", phone="+254 20 693 0000",
        address="Dunga Road, South B", town="Nairobi", county="Nairobi",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.3047, lon=36.8236,
        sv=HOSPITAL_CORE + ["dental", "eye", "oncology"],
        ins=MISSION + ["cic", "uap", "resolution"],
    ),
    dict(
        name="Kenyatta University Teaching, Referral & Research Hospital",
        type="hospital", operator="Government — National Referral",
        phone="+254 20 880 000", website="https://www.kutr.go.ke",
        address="Kenyatta University Campus Road", town="Ruiru", county="Kiambu",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-1.1806, lon=37.0190,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA,
        ins=GOVERNMENT + ["jubilee", "aar", "madison", "cic", "uap"],
    ),
    dict(
        name="Pumwani Maternity Hospital", type="maternity",
        operator="Nairobi County Government", phone="+254 20 676 000",
        address="Mumias Road, Eastleigh", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Su 00:00-24:00", wheelchair="limited",
        lat=-1.2567, lon=36.8419,
        sv=["maternity", "mch", "ultrasound", "outpatient", "pharmacy", "laboratory", "family_planning", "vaccination"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Avenue Healthcare — Kilimani", type="clinic",
        operator="Avenue Healthcare", phone="+254 709 900 000",
        address="Ring Road, Kilimani", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Su 08:00-19:00", wheelchair="yes",
        lat=-1.2928, lon=36.7844,
        sv=CLINIC_SVCS + ["ultrasound", "surgery"],
        ins=PRIVATE_ALL,
    ),
    dict(
        name="Riverside Medical Centre", type="clinic",
        operator="Riverside Healthcare", phone="+254 709 910 000",
        address="Riara Road, Riverside", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 08:00-18:00; Sa 08:00-14:00", wheelchair="yes",
        lat=-1.2197, lon=36.8075,
        sv=CLINIC_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison", "britam"],
    ),
    dict(
        name="Kibera South Health Centre", type="health_centre",
        operator="Nairobi County Government", phone="+254 700 100 000",
        address="Kibera Drive", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Fr 08:00-17:00; Sa 08:00-13:00",
        wheelchair="limited", lat=-1.3134, lon=36.7901,
        sv=HEALTH_CENTRE_SVCS + ["hiv_tb", "ncd"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Mukuru Health Centre", type="health_centre",
        operator="Nairobi County Government", phone="+254 700 100 100",
        address="Mukuru Kwa Njenga", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Fr 08:00-17:00; Sa 08:00-13:00",
        wheelchair="no", lat=-1.3175, lon=36.8866,
        sv=HEALTH_CENTRE_SVCS,
        ins=GOVERNMENT,
    ),
    dict(
        name="Kayole Sub-County Health Centre", type="health_centre",
        operator="Nairobi County Government", phone="+254 700 100 200",
        address="Kayole Spine Road", town="Nairobi", county="Nairobi",
        emergency="limited", hours="Mo-Fr 08:00-17:00; Sa 08:00-13:00",
        wheelchair="limited", lat=-1.2783, lon=36.8766,
        sv=HEALTH_CENTRE_SVCS,
        ins=GOVERNMENT,
    ),
    dict(
        name="Ngando Health Dispensary", type="dispensary",
        operator="Nairobi County Government", phone="+254 700 100 300",
        address="Ngando Road", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 08:00-17:00", wheelchair="no",
        lat=-1.3239, lon=36.7911,
        sv=DISPENSARY_SVCS,
        ins=GOVERNMENT,
    ),
    dict(
        name="Good Life Pharmacy — Westlands", type="pharmacy",
        operator="Good Life Pharmacy", phone="+254 700 200 000",
        address="Sankara Road, Westlands", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Su 08:00-21:00", wheelchair="yes",
        lat=-1.2635, lon=36.8030,
        sv=PHARMACY_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison", "britam", "cic"],
    ),
    dict(
        name="Haltons Pharmacy — Kilimani", type="pharmacy",
        operator="Haltons Pharmacy", phone="+254 700 200 100",
        address="Ring Road, Kilimani", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Su 08:00-20:00", wheelchair="yes",
        lat=-1.2914, lon=36.7829,
        sv=PHARMACY_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison"],
    ),
    dict(
        name="Good Life Pharmacy — Kenyatta Avenue", type="pharmacy",
        operator="Good Life Pharmacy", phone="+254 700 200 200",
        address="Kenyatta Avenue", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Su 08:00-22:00", wheelchair="yes",
        lat=-1.2833, lon=36.8219,
        sv=PHARMACY_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison", "britam"],
    ),
    dict(
        name="Lancet Clinical Laboratories — Kenyatta Avenue", type="laboratory",
        operator="Lancet Laboratories Kenya", phone="+254 20 221 4444",
        website="https://www.lancet.co.ke", address="Kenyatta Avenue",
        town="Nairobi", county="Nairobi", emergency="no",
        hours="Mo-Su 07:00-20:00", wheelchair="yes",
        lat=-1.2846, lon=36.8216,
        sv=["laboratory", "imaging", "ultrasound", "telemedicine"],
        ins=["sha", "self", "jubilee", "aar", "madison", "britam", "cic", "uap"],
    ),
    dict(
        name="Pathologists Lancet Kenya — Parklands", type="laboratory",
        operator="Lancet Laboratories Kenya", phone="+254 20 374 0000",
        address="Parklands Road", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 07:00-19:00; Sa 07:00-14:00", wheelchair="yes",
        lat=-1.2631, lon=36.8060,
        sv=["laboratory", "telemedicine"],
        ins=["sha", "self", "jubilee", "aar", "madison", "resolution"],
    ),
    dict(
        name="Smile Hub Dental Clinic — Kilimani", type="dentist",
        operator="Smile Hub Dental", phone="+254 700 300 000",
        address="Ring Road, Kilimani", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 08:00-18:00; Sa 09:00-14:00", wheelchair="yes",
        lat=-1.2902, lon=36.7864,
        sv=["dental", "pharmacy"],
        ins=["sha", "self", "jubilee", "aar", "madison", "britam"],
    ),
    dict(
        name="Dental Point — Westlands", type="dentist",
        operator="Dental Point Ltd", phone="+254 700 300 100",
        address="Wabera Street, Westlands", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 08:30-18:00; Sa 09:00-15:00", wheelchair="yes",
        lat=-1.2651, lon=36.8068,
        sv=["dental"],
        ins=["sha", "self", "jubilee", "madison"],
    ),
    dict(
        name="The Eye Foundation Kenya — Nairobi", type="eye_clinic",
        operator="The Eye Foundation", phone="+254 700 400 000",
        address="Moi Avenue", town="Nairobi", county="Nairobi",
        emergency="no", hours="Mo-Fr 08:00-17:00; Sa 09:00-13:00", wheelchair="yes",
        lat=-1.2957, lon=36.8173,
        sv=["eye", "outpatient", "laboratory"],
        ins=["sha", "self", "jubilee", "aar", "madison", "britam", "cic"],
    ),

    # ── Mombasa ───────────────────────────────────────────────────────────────
    dict(
        name="Coast General Teaching & Referral Hospital", type="hospital",
        operator="Government — County Referral", phone="+254 41 231 2300",
        address="Kisauni Road, Port Reitz", town="Mombasa", county="Mombasa",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-4.0633, lon=39.6597,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Aga Khan Hospital Mombasa", type="hospital",
        operator="Aga Khan Health Service", phone="+254 41 222 5000",
        address="Sovereign Road, Seafront", town="Mombasa", county="Mombasa",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-4.0519, lon=39.6649,
        sv=HOSPITAL_CORE + ["dental", "eye", "oncology", "mental_health"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="The Mombasa Hospital", type="hospital",
        operator="The Mombasa Hospital Ltd", phone="+254 41 223 2000",
        address="Mwembe Tayari", town="Mombasa", county="Mombasa",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-4.0542, lon=39.6617,
        sv=HOSPITAL_CORE + ["dental", "ncd"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Pandya Memorial Hospital", type="hospital",
        operator="Pandya Memorial Hospital Trust", phone="+254 41 223 7000",
        address="Mwembe Tayari", town="Mombasa", county="Mombasa",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-4.0445, lon=39.6601,
        sv=HOSPITAL_CORE + ["hiv_tb", "ncd"],
        ins=MISSION,
    ),
    dict(
        name="Jocham Hospital", type="hospital",
        operator="Jocham Hospital Ltd", phone="+254 41 231 6000",
        address="Mwembe Tayari", town="Mombasa", county="Mombasa",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-4.0640, lon=39.6740,
        sv=["outpatient", "inpatient", "emergency", "maternity", "surgery", "pharmacy",
            "laboratory", "ultrasound", "pediatric", "icu"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Good Life Pharmacy — Nyali", type="pharmacy",
        operator="Good Life Pharmacy", phone="+254 700 200 300",
        address="Nyali Road", town="Mombasa", county="Mombasa",
        emergency="no", hours="Mo-Su 08:00-21:00", wheelchair="yes",
        lat=-4.0563, lon=39.7087,
        sv=PHARMACY_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison"],
    ),
    dict(
        name="Port Reitz Sub-County Health Centre", type="health_centre",
        operator="Mombasa County Government", phone="+254 41 200 000",
        address="Port Reitz Road", town="Mombasa", county="Mombasa",
        emergency="limited", hours="Mo-Fr 08:00-17:00; Sa 08:00-13:00",
        wheelchair="no", lat=-4.0751, lon=39.6486,
        sv=HEALTH_CENTRE_SVCS + ["hiv_tb"],
        ins=GOVERNMENT,
    ),

    # ── Kisumu ────────────────────────────────────────────────────────────────
    dict(
        name="Jaramogi Oginga Odinga Teaching & Referral Hospital",
        type="hospital", operator="Government — Nyanza Referral",
        phone="+254 57 202 0000", website="https://www.jootrh.go.ke",
        address="Jomo Kenyatta Highway", town="Kisumu", county="Kisumu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.0874, lon=34.7683,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Aga Khan Hospital Kisumu", type="hospital",
        operator="Aga Khan Health Service", phone="+254 57 202 2400",
        address="Jomo Kenyatta Highway", town="Kisumu", county="Kisumu",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=-0.0932, lon=34.7516,
        sv=HOSPITAL_CORE + ["dental", "eye", "ncd"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Maseno Mission Hospital", type="hospital",
        operator="Africa Inland Church", phone="+254 57 202 5000",
        address="Maseno Town", town="Maseno", county="Kisumu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.0924, lon=34.6046,
        sv=HOSPITAL_CORE + ["hiv_tb"],
        ins=MISSION,
    ),
    dict(
        name="Kondele Sub-County Hospital", type="hospital",
        operator="Kisumu County Government", phone="+254 57 202 7000",
        address="Kondele Junction", town="Kisumu", county="Kisumu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.1021, lon=34.7364,
        sv=["outpatient", "inpatient", "emergency", "maternity", "pharmacy",
            "laboratory", "vaccination", "hiv_tb", "ambulance"],
        ins=GOVERNMENT,
    ),

    # ── Nakuru ────────────────────────────────────────────────────────────────
    dict(
        name="Nakuru County Level 5 Hospital", type="hospital",
        operator="Nakuru County Government", phone="+254 51 221 2000",
        address="Kenyatta Avenue", town="Nakuru", county="Nakuru",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.2854, lon=36.0683,
        sv=HOSPITAL_CORE + ["dental", "hiv_tb", "ncd"],
        ins=GOVERNMENT,
    ),
    dict(
        name="AIC War Memorial Hospital", type="hospital",
        operator="Africa Inland Church", phone="+254 51 221 5000",
        address="Geoffrey Kamau Avenue", town="Nakuru", county="Nakuru",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.2806, lon=36.0796,
        sv=HOSPITAL_CORE + ["dental", "eye"],
        ins=MISSION,
    ),
    dict(
        name="Good Life Pharmacy — Nakuru", type="pharmacy",
        operator="Good Life Pharmacy", phone="+254 700 200 400",
        address="Kenyatta Avenue", town="Nakuru", county="Nakuru",
        emergency="no", hours="Mo-Su 08:00-21:00", wheelchair="yes",
        lat=-0.2869, lon=36.0768,
        sv=PHARMACY_SVCS,
        ins=["sha", "self", "jubilee", "aar", "madison"],
    ),

    # ── Eldoret ───────────────────────────────────────────────────────────────
    dict(
        name="Moi Teaching and Referral Hospital", type="hospital",
        operator="Government — National Referral", phone="+254 53 203 3471",
        website="https://www.mtrh.go.ke", address="Nandi Road, Eldoret",
        town="Eldoret", county="Uasin Gishu", emergency="yes", hours="24/7",
        wheelchair="limited", lat=0.5153, lon=35.2794,
        sv=HOSPITAL_CORE + HOSPITAL_EXTRA + ["hiv_tb"],
        ins=GOVERNMENT + ["jubilee", "aar", "cic", "uap"],
    ),
    dict(
        name="Elgon View Hospital", type="hospital",
        operator="Elgon View Hospital Ltd", phone="+254 53 202 0000",
        address="Elgon View Drive", town="Eldoret", county="Uasin Gishu",
        emergency="yes", hours="24/7", wheelchair="yes",
        lat=0.5205, lon=35.2746,
        sv=["outpatient", "inpatient", "maternity", "surgery", "pharmacy",
            "laboratory", "ultrasound", "emergency", "ncd"],
        ins=PRIVATE_ALL + ["nhif"],
    ),
    dict(
        name="Medincell Hospital Eldoret", type="hospital",
        operator="Medincell Ltd", phone="+254 53 206 0000",
        address="Kipkaren Road", town="Eldoret", county="Uasin Gishu",
        emergency="yes", hours="Mo-Su 00:00-24:00", wheelchair="limited",
        lat=0.5076, lon=35.2727,
        sv=["outpatient", "inpatient", "maternity", "surgery", "pharmacy",
            "laboratory", "imaging", "emergency"],
        ins=PRIVATE_ALL + ["nhif"],
    ),

    # ── Other counties ────────────────────────────────────────────────────────
    dict(
        name="Nyeri County Referral Hospital", type="hospital",
        operator="Nyeri County Government", phone="+254 61 203 2000",
        address="Kenyatta Avenue", town="Nyeri", county="Nyeri",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.4178, lon=36.9470,
        sv=HOSPITAL_CORE + ["dental", "hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Thika Level 5 Hospital", type="hospital",
        operator="Kiambu County Government", phone="+254 67 520 000",
        address="Hospital Road, Thika", town="Thika", county="Kiambu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.0330, lon=37.0692,
        sv=HOSPITAL_CORE + ["hiv_tb", "ncd"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Machakos Level 5 Hospital", type="hospital",
        operator="Machakos County Government", phone="+254 45 120 000",
        address="Machakos Town", town="Machakos", county="Machakos",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.5177, lon=37.2634,
        sv=HOSPITAL_CORE + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Kakamega County General Hospital", type="hospital",
        operator="Kakamega County Government", phone="+254 56 202 000",
        address="Kakamega Town", town="Kakamega", county="Kakamega",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=0.2826, lon=34.7526,
        sv=HOSPITAL_CORE + ["hiv_tb", "ncd"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Kericho County Referral Hospital", type="hospital",
        operator="Kericho County Government", phone="+254 52 202 000",
        address="Kericho Town", town="Kericho", county="Kericho",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-0.3686, lon=35.2864,
        sv=HOSPITAL_CORE + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
    dict(
        name="Kiambu Level 5 Hospital", type="hospital",
        operator="Kiambu County Government", phone="+254 20 200 000",
        address="Kiambu Town", town="Kiambu", county="Kiambu",
        emergency="yes", hours="24/7", wheelchair="limited",
        lat=-1.1714, lon=36.8278,
        sv=HOSPITAL_CORE + ["hiv_tb"],
        ins=GOVERNMENT,
    ),
]


class Command(BaseCommand):
    help = "Seed service/insurance catalogues and representative health facilities."

    @transaction.atomic
    def handle(self, *args, **options):
        # ── Services ──────────────────────────────────────────────────────────
        for slug, name, icon, category, order in SERVICES:
            Service.objects.update_or_create(
                slug=slug,
                defaults=dict(name=name, icon=icon, category=category, order=order),
            )
        self.stdout.write(f"  services:    {Service.objects.count()}")

        # ── Insurers ──────────────────────────────────────────────────────────
        for slug, name, kind, order in INSURERS:
            Insurance.objects.update_or_create(
                slug=slug,
                defaults=dict(name=name, kind=kind, order=order),
            )
        self.stdout.write(f"  insurers:    {Insurance.objects.count()}")

        services_by_slug = {s.slug: s for s in Service.objects.all()}
        insurers_by_slug = {i.slug: i for i in Insurance.objects.all()}

        created = updated = 0
        for row in FACILITIES:
            sv_slugs = {s for s in row["sv"] if s in services_by_slug}
            ins_slugs = {s for s in row["ins"] if s in insurers_by_slug}
            assert sv_slugs, f"unknown services in {row['name']}"
            assert ins_slugs, f"unknown insurers in {row['name']}"

            defaults = dict(
                facility_type=row["type"],
                operator=row["operator"],
                phone=row["phone"],
                website=row.get("website", ""),
                address=row.get("address", ""),
                county=row.get("county", ""),
                emergency=row["emergency"],
                opening_hours=row["hours"],
                wheelchair=row["wheelchair"],
                latitude=row["lat"],
                longitude=row["lon"],
            )

            obj, was_created = Facility.objects.update_or_create(
                name=row["name"],
                town=row.get("town", ""),
                defaults=defaults,
            )
            obj.services.set(services_by_slug[s] for s in sv_slugs)
            obj.insurances.set(insurers_by_slug[s] for s in ins_slugs)
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"  facilities:  {len(FACILITIES)} total "
                f"({created} created, {updated} updated) → "
                f"{Facility.objects.count()} in database"
            )
        )
        self.stdout.write(self.style.SUCCESS("Seed complete."))

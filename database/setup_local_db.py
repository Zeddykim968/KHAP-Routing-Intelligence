"""
One-time script: creates the facilities table in the local Replit PostgreSQL
and seeds it from the CSV file.
Run: python database/setup_local_db.py
"""

import os
import csv
import psycopg2
from psycopg2.extras import execute_batch

DATABASE_URL = os.getenv("DATABASE_URL", "")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "attached_assets", "facilities_dataset_1779119899366.csv")

DDL = """
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP TABLE IF EXISTS public.facilities CASCADE;
CREATE TABLE public.facilities (
    facility_id       INTEGER PRIMARY KEY,
    facility_code     INTEGER,
    name              TEXT NOT NULL,
    county            TEXT,
    district          TEXT,
    type              TEXT,
    owner             TEXT,
    nearest_town      TEXT,
    beds              INTEGER DEFAULT 0,
    cots              INTEGER DEFAULT 0,
    open_24_hours     BOOLEAN DEFAULT FALSE,
    open_weekends     BOOLEAN DEFAULT FALSE,
    operational_status TEXT DEFAULT 'Operational',
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    geom              GEOGRAPHY(POINT, 4326)
);

CREATE INDEX IF NOT EXISTS idx_facilities_county   ON public.facilities(county);
CREATE INDEX IF NOT EXISTS idx_facilities_type     ON public.facilities(type);
CREATE INDEX IF NOT EXISTS idx_facilities_status   ON public.facilities(operational_status);
CREATE INDEX IF NOT EXISTS idx_facilities_geom     ON public.facilities USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_facilities_name_trgm ON public.facilities USING GIN(name gin_trgm_ops);

DROP TABLE IF EXISTS public.api_keys CASCADE;
CREATE TABLE public.api_keys (
    id         SERIAL PRIMARY KEY,
    user_id    TEXT,
    name       TEXT NOT NULL,
    key_hash   TEXT UNIQUE NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    last_used  TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON public.api_keys(key_hash);

DROP TABLE IF EXISTS public.import_logs CASCADE;
CREATE TABLE public.import_logs (
    id             SERIAL PRIMARY KEY,
    stage          TEXT,
    source         TEXT,
    total_records  INTEGER,
    loaded_records INTEGER,
    error_records  INTEGER,
    imported_at    TIMESTAMPTZ DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO public.facilities
    (facility_id, facility_code, name, county, district, type, owner,
     nearest_town, beds, cots, open_24_hours, open_weekends,
     operational_status, latitude, longitude, geom)
VALUES
    (%(facility_id)s, %(facility_code)s, %(name)s, %(county)s, %(district)s,
     %(type)s, %(owner)s, %(nearest_town)s, %(beds)s, %(cots)s,
     %(open_24_hours)s, %(open_weekends)s, %(operational_status)s,
     %(latitude)s, %(longitude)s,
     CASE WHEN %(latitude)s IS NOT NULL AND %(longitude)s IS NOT NULL
          THEN ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326)::geography
          ELSE NULL END)
ON CONFLICT (facility_id) DO UPDATE SET
    name = EXCLUDED.name,
    county = EXCLUDED.county,
    type = EXCLUDED.type,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    geom = EXCLUDED.geom;
"""


def parse_bool(v):
    return v.strip().lower() in ("t", "true", "1", "yes")


def parse_int(v, default=0):
    try:
        return int(float(v.strip())) if v.strip() else default
    except Exception:
        return default


def parse_float(v):
    try:
        f = float(v.strip())
        return f if f != 0.0 else None
    except Exception:
        return None


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("Creating schema…")
    cur.execute(DDL)
    conn.commit()

    print("Loading CSV…")
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            lat = parse_float(r.get("latitude", ""))
            lon = parse_float(r.get("longitude", ""))
            rows.append({
                "facility_id":       parse_int(r.get("facility_id", ""), 0),
                "facility_code":     parse_int(r.get("facility_code", ""), None),
                "name":              r.get("name", "").strip(),
                "county":            r.get("county", "").strip(),
                "district":          r.get("district", "").strip(),
                "type":              r.get("type", "").strip(),
                "owner":             r.get("owner", "").strip(),
                "nearest_town":      r.get("nearest_town", "").strip(),
                "beds":              parse_int(r.get("beds", ""), 0),
                "cots":              parse_int(r.get("cots", ""), 0),
                "open_24_hours":     parse_bool(r.get("open_24_hours", "f")),
                "open_weekends":     parse_bool(r.get("open_weekends", "f")),
                "operational_status": r.get("operational_status", "Operational").strip(),
                "latitude":          lat,
                "longitude":         lon,
            })

    print(f"Inserting {len(rows)} facilities…")
    execute_batch(cur, INSERT_SQL, rows, page_size=500)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM public.facilities;")
    count = cur.fetchone()[0]
    print(f"Done — {count} facilities in database.")
    conn.close()


if __name__ == "__main__":
    main()

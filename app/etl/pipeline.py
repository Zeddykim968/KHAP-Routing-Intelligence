"""
ETL pipeline for health facility data.
Uses local PostgreSQL via app/services/db.py.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict

from app.etl.validators import validate_batch
from app.services.db import execute, execute_returning

logger = logging.getLogger(__name__)


def _clean(record: Dict) -> Dict:
    cleaned = {}
    for k, v in record.items():
        cleaned[k] = v.strip() if isinstance(v, str) else v
    for field in ("latitude", "longitude"):
        if cleaned.get(field) is not None:
            try:
                cleaned[field] = float(cleaned[field])
            except (ValueError, TypeError):
                cleaned[field] = None
    for field in ("beds", "cots"):
        if cleaned.get(field) is not None:
            try:
                cleaned[field] = int(cleaned[field])
            except (ValueError, TypeError):
                cleaned[field] = None
    name = cleaned.get("name", "")
    cleaned["name"] = " ".join(name.split())
    return cleaned


def _transform(record: Dict) -> Dict:
    if not record.get("operational_status"):
        record["operational_status"] = "Operational"
    return record


def _log_import(stage, total, loaded, errors, source):
    try:
        execute(
            """INSERT INTO import_logs
               (stage, source, total_records, loaded_records, error_records, imported_at)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            [stage, source, total, loaded, errors, datetime.now(timezone.utc)],
        )
    except Exception as e:
        logger.warning(f"Could not write import log: {e}")


def run_pipeline(records: List[Dict], source: str = "manual", dry_run: bool = False) -> Dict:
    start = datetime.now(timezone.utc)
    validation = validate_batch(records)
    valid_records = validation["valid_records"]
    cleaned = [_clean(r) for r in valid_records]
    transformed = [_transform(r) for r in cleaned]

    loaded = 0
    load_errors = []

    if not dry_run:
        for record in transformed:
            try:
                execute(
                    """INSERT INTO facilities
                       (facility_id, name, county, type, latitude, longitude,
                        operational_status, beds, cots, open_24_hours, open_weekends)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (facility_id) DO UPDATE SET
                           name=EXCLUDED.name, county=EXCLUDED.county,
                           type=EXCLUDED.type, latitude=EXCLUDED.latitude,
                           longitude=EXCLUDED.longitude""",
                    [
                        record.get("facility_id"), record.get("name"),
                        record.get("county"), record.get("type"),
                        record.get("latitude"), record.get("longitude"),
                        record.get("operational_status", "Operational"),
                        record.get("beds", 0), record.get("cots", 0),
                        record.get("open_24_hours", False),
                        record.get("open_weekends", False),
                    ],
                )
                loaded += 1
            except Exception as e:
                load_errors.append({"record": record.get("name"), "error": str(e)})

        _log_import("full_pipeline", len(records), loaded, len(load_errors), source)

    duration_s = (datetime.now(timezone.utc) - start).total_seconds()
    return {
        "source": source, "dry_run": dry_run,
        "duration_seconds": round(duration_s, 2),
        "stages": {
            "extract": len(records),
            "validate": {"valid": validation["valid"], "invalid": validation["invalid"]},
            "clean_transform": len(transformed),
            "load": {"loaded": loaded, "errors": len(load_errors)},
        },
        "load_errors": load_errors[:10],
        "status": "completed",
    }

"""
KHAP — Django project settings.

Environment-driven configuration:
  - Reads .env from the repository root and from backend/.
  - Uses PostgreSQL via DATABASE_URL when set, and fails fast with the
    database driver's own error if that server cannot be reached; SQLite is
    only used when DATABASE_URL is unset.
  - OpenRouteService is the only routing engine (ORS_URL / ORS_API_KEY).
"""
import os
from pathlib import Path
from urllib.parse import urlsplit

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load environment files: repo root first, then backend/ overrides it.
load_dotenv(REPO_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-insecure-khap-secret-key-change-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")
    if h.strip()
]

# ── Applications ──────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    # Local
    "facilities",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "khap.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "khap.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
# DATABASE_URL=postgresql://user:pass@host:5432/khap  → PostgreSQL
# (unset)                                            → local SQLite
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ── Database reachability check ───────────────────────────────────────────────
# There is deliberately no SQLite fallback: if DATABASE_URL points at
# PostgreSQL, that database must answer. A failed connection raises
# ImproperlyConfigured carrying the driver's original error (e.g. Supabase
# "(EAUTHQUERY) authentication query failed") so the real cause is visible
# instead of being silently masked by a different database.
def _describe_target(cfg: dict) -> str:
    """Human-readable host/database for error messages (never the password)."""
    host = cfg.get("HOST") or "localhost"
    port = cfg.get("PORT") or 5432
    name = cfg.get("NAME") or ""
    user = cfg.get("USER") or ""
    return f"{user}@{host}:{port}/{name}" if user else f"{host}:{port}/{name}"


def _check_postgres(cfg: dict, timeout: int) -> None:
    """Open (and immediately close) one connection, raising on failure."""
    params = {
        "host": cfg.get("HOST") or "localhost",
        "port": cfg.get("PORT") or 5432,
        "user": cfg.get("USER") or "",
        "password": cfg.get("PASSWORD") or "",
        "dbname": cfg.get("NAME") or "",
        "connect_timeout": timeout,
    }
    sslmode = (cfg.get("OPTIONS") or {}).get("sslmode")
    if sslmode:
        params["sslmode"] = sslmode

    target = _describe_target(cfg)
    driver = None
    for driver, connect in _iter_postgres_drivers():
        try:
            connect(**params).close()
            return
        except Exception as exc:  # surface the driver's real message
            raise ImproperlyConfigured(
                f"Could not connect to the configured PostgreSQL database "
                f"({_describe_target(cfg)}) using {driver}: {exc}. "
                "Django will not fall back to SQLite; fix DATABASE_URL "
                "(or unset it to use the local SQLite development database)."
            ) from exc

    raise ImproperlyConfigured(
        f"DATABASE_URL points at PostgreSQL ({target}) but no PostgreSQL driver "
        "is installed. Install psycopg[binary] or psycopg2-binary, or unset "
        "DATABASE_URL to use the local SQLite development database."
    )


def _iter_postgres_drivers():
    """Yield (label, connect) for whichever libpq driver is importable."""
    try:
        import psycopg

        yield "psycopg", psycopg.connect
    except ImportError:
        pass
    try:
        import psycopg2

        yield "psycopg2", psycopg2.connect
    except ImportError:
        pass


_db_cfg = DATABASES["default"]
if "postgresql" in str(_db_cfg.get("ENGINE", "")):
    try:
        _db_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
    except ValueError:
        _db_timeout = 5
    _check_postgres(_db_cfg, _db_timeout)

# ── Password validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalization ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
    if DEBUG
    else ["rest_framework.renderers.JSONRenderer"],
}

# ── CORS ──────────────────────────────────────────────────────────────────────
# The Next.js dev server proxies /api/* itself, but CORS is opened for
# direct browser → Django access during development.
_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
if _cors:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]
else:
    CORS_ALLOW_ALL_ORIGINS = True

# ── KHAP settings ─────────────────────────────────────────────────────────────
# OpenRouteService (sole routing engine): directions + travel-distance matrix.
# ORS_API_KEY is required — there is no fallback engine or straight-line ranking,
# so routing requests fail with an explicit error when it is missing or ORS
# is unreachable.
ORS_URL = os.environ.get("ORS_URL", "https://api.openrouteservice.org").rstrip("/")
ORS_API_KEY = os.environ.get("ORS_API_KEY", "").strip()
ORS_PROFILE = os.environ.get("ORS_PROFILE", "driving-car").strip() or "driving-car"
ORS_TIMEOUT = float(os.environ.get("ORS_TIMEOUT", "20"))
# How many candidate facilities are sent to the ORS matrix per nearest query
# (ORS plans cap matrix requests at 50 locations; the source counts as one).
ORS_MATRIX_CANDIDATES = max(1, int(os.environ.get("ORS_MATRIX_CANDIDATES", "25")))
ORS_MATRIX_BATCH = max(1, min(int(os.environ.get("ORS_MATRIX_BATCH", "25")), 49))

APP_NAME = "KHAP — Kenya Health Access Platform"
APP_VERSION = "2.0.0"

# Approximate bounding box used to sanity-check coordinate inputs (Kenya).
KENYA_BOUNDS = {
    "lat_min": -5.0,
    "lat_max": 5.5,
    "lon_min": 33.5,
    "lon_max": 42.5,
}

import os

RESTAURANT_NAME = os.environ.get("RESTAURANT_NAME", "thirdrestaurant")
RESTAURANT_TAGLINE = os.environ.get("RESTAURANT_TAGLINE", "Italian Restaurant & Café")
POLL_INTERVAL_SECONDS = 3
VAT_RATE = float(os.environ.get("VAT_RATE", "0.07"))
SERVICE_CHARGE_RATE = float(os.environ.get("SERVICE_CHARGE_RATE", "0.10"))

# Firebase Authentication (Login, Register, password reset email)
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")

# Upstash Redis REST (application data)
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "").rstrip("/")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
UPSTASH_KEY_PREFIX = os.environ.get("UPSTASH_KEY_PREFIX", "thirdrestaurant")

# First-run admin bootstrap; never commit its value.
BOOTSTRAP_SECRET = os.environ.get("BOOTSTRAP_SECRET", "")
LOCAL_AUTH_SECRET = os.environ.get("LOCAL_AUTH_SECRET", "change-me-in-local-env")
LOCAL_DB_PATH = os.environ.get("LOCAL_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "database.json"))

ALLOWED_ROLES = {"admin", "staff", "customer"}


def is_configured():
    return bool(FIREBASE_API_KEY and UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)


def is_local_mode():
    return not bool(FIREBASE_API_KEY and UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)

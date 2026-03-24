import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = BASE_DIR.parent

# Prefer backend-local environment variables and allow overriding shell values.
load_dotenv(BASE_DIR / ".env", override=True)
# Workspace-level .env acts only as fallback.
load_dotenv(WORKSPACE_DIR / ".env", override=False)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
STT_API = os.getenv("STT_API", "http://localhost:9000")
TTS_API = os.getenv("TTS_API", "http://localhost:9001")
LLM_API = os.getenv("LLM_API", "http://localhost:9002")


def _as_bool(value: str, default: bool = False) -> bool:
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "y", "on"}


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_PUBLIC_BASE_URL = os.getenv("TWILIO_PUBLIC_BASE_URL", "")
SMS_DEFAULT_COUNTRY_CODE = os.getenv("SMS_DEFAULT_COUNTRY_CODE", "+91")
SMS_DRY_RUN = _as_bool(os.getenv("SMS_DRY_RUN", "false"))
QR_IMAGE_DIR = Path(os.getenv("QR_IMAGE_DIR", str(BASE_DIR / "data" / "qr")))
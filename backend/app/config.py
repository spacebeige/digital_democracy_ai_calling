import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = BASE_DIR.parent

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
STT_API = os.getenv("STT_API", "http://localhost:9000")
TTS_API = os.getenv("TTS_API", "http://localhost:9001")
LLM_API = os.getenv("LLM_API", "http://localhost:9002")

# ─────────────────────────────────────────────────────────────────────
# Layer 3: NLP + Sarvam API Configuration
# ─────────────────────────────────────────────────────────────────────

# IMPORTANT: Never hardcode API keys. Always use environment variables.
# Set in .env or export before running:
#   export SARVAM_API_KEY="sk_your_key_here"
#   (Keep this key secret in .env, never commit or share!)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", None)

# Warn if API key is not set (will use mock/dev mode)
if not SARVAM_API_KEY:
    logger.warning(
        "SARVAM_API_KEY not set. NLP classifier will use mock mode. "
        "Set SARVAM_API_KEY environment variable for production."
    )

SARVAM_API_ENDPOINT = os.getenv(
    "SARVAM_API_ENDPOINT", 
    "https://api.sarvam.ai/v1/chat/completions"
)
SARVAM_TIMEOUT = float(os.getenv("SARVAM_TIMEOUT", "10.0"))
SARVAM_MAX_RETRIES = int(os.getenv("SARVAM_MAX_RETRIES", "3"))

# NLP Classifier mode (use mock for dev/testing, real for production)
USE_MOCK_NLP = os.getenv("USE_MOCK_NLP", "false").lower() in ("true", "1", "yes")
if USE_MOCK_NLP:
    logger.info("NLP Classifier running in MOCK mode (for development)")
else:
    logger.info("NLP Classifier running in PRODUCTION mode")


# ─────────────────────────────────────────────────────────────────────
# Twilio SMS Configuration
# ─────────────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────────────
# AWS S3 Configuration (for QR Code Storage)
# ─────────────────────────────────────────────────────────────────────

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "us-east-1")
AWS_S3_UPLOAD_DIR = os.getenv("AWS_S3_UPLOAD_DIR", "qr-codes")  # Prefix in S3

# Determine if S3 is enabled
USE_S3_FOR_QR = (
    _as_bool(os.getenv("USE_S3_FOR_QR", "false"))
    and AWS_ACCESS_KEY_ID
    and AWS_SECRET_ACCESS_KEY
    and AWS_S3_BUCKET_NAME
)
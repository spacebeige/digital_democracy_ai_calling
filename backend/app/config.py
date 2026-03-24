import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
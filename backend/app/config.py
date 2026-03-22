import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
STT_API = os.getenv("STT_API", "http://localhost:9000")
TTS_API = os.getenv("TTS_API", "http://localhost:9001")
LLM_API = os.getenv("LLM_API", "http://localhost:9002")

# Layer 3: Call Router Configuration
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", None)
SARVAM_API_ENDPOINT = os.getenv(
    "SARVAM_API_ENDPOINT", 
    "https://api.sarvam.ai/classify"
)
SARVAM_TIMEOUT = int(os.getenv("SARVAM_TIMEOUT", "10"))
SARVAM_MAX_RETRIES = int(os.getenv("SARVAM_MAX_RETRIES", "3"))
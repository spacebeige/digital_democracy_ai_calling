import os
import json
import logging

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a government scheme classification engine.

Your task is to analyze input text describing a government scheme and assign structured labels.

Do NOT hallucinate. Only infer from the text.

Return output in strict JSON format.

---

CLASSIFICATION DIMENSIONS:

1. domain (multiple allowed):
[healthcare, education, agriculture, transport, housing, employment, finance, social_welfare, energy, digital_services]

2. beneficiary_groups (multiple allowed):
[general, ews, obc, sc, st, minority, women, children, students, farmers, senior_citizens, disabled, entrepreneurs, workers_unorganized]

3. benefit_type (multiple allowed):
[subsidy, scholarship, loan, insurance, cash_transfer, training, employment_support, food_security, housing_support, pension, health_coverage]

4. access_mode (one or more):
[online, offline, assisted]

5. geography:
[central, state, district]

6. urgency:
[active, new, expiring, discontinued]

---

RULES:

- Handle multilingual and code-mixed input (Hindi, English, Tamil, Telugu, Bengali, etc.)
- Normalize all outputs into English labels only
- If uncertain, return "unknown"
- Do not invent categories outside the list

---

OUTPUT FORMAT:

{
  "scheme_name": "",
  "domain": [],
  "beneficiary_groups": [],
  "benefit_type": [],
  "access_mode": [],
  "geography": "",
  "urgency": "",
  "confidence": 0.0
}"""

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None and GROQ_AVAILABLE:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            _groq_client = Groq(api_key=api_key)
    return _groq_client

_groq_client_async = None

def get_groq_client_async():
    global _groq_client_async
    if _groq_client_async is None and GROQ_AVAILABLE:
        from groq import AsyncGroq
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            _groq_client_async = AsyncGroq(api_key=api_key)
    return _groq_client_async

async def classify_scheme_async(text: str) -> dict:
    """
    Classifies a government scheme or related query using the LLM asynchronously.
    Returns the parsed JSON dictionary.
    """
    client = get_groq_client_async()
    if not client:
        logger.error("Async Groq client not initialized. Check API key and library.")
        return get_fallback_classification()
        
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to classify scheme: {e}")
        return get_fallback_classification()

def classify_scheme(text: str) -> dict:
    """
    Classifies a government scheme or related query using the LLM.
    Returns the parsed JSON dictionary.
    """
    client = get_groq_client()
    if not client:
        logger.error("Groq client not initialized. Check API key and library.")
        return get_fallback_classification()
        
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to classify scheme: {e}")
        return get_fallback_classification()

def get_fallback_classification():
    return {
      "scheme_name": "unknown",
      "domain": [],
      "beneficiary_groups": [],
      "benefit_type": [],
      "access_mode": [],
      "geography": "unknown",
      "urgency": "unknown",
      "confidence": 0.0
    }

if __name__ == "__main__":
    import sys
    import dotenv
    from pathlib import Path
    
    env_path = Path('.env')
    if env_path.exists():
        dotenv.load_dotenv(dotenv_path=env_path)
        
    test_text = "मुझे प्रधानमंत्री किसान सम्मान निधि योजना के बारे में जानना है। इसमें किसानों को 6000 रुपये मिलते हैं।"
    if len(sys.argv) > 1:
        test_text = sys.argv[1]
        
    print(f"Testing with: {test_text}")
    print(json.dumps(classify_scheme(test_text), indent=2))

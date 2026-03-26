#!/usr/bin/env python3
"""
Generate and play TTS for native script sentences in 40+ Indian languages using Sarvam/Ritu voice.
Format and output matches user request.
"""
import os
import sys
import time
from pathlib import Path
import tempfile

sys.path.insert(0, os.path.abspath("./awaaz"))
sys.path.insert(0, os.path.abspath("./awaaz/src"))
sys.path.insert(0, os.path.abspath("./awaaz/src/pipeline"))

from src.pipeline.tts import _sarvam_tts, SARVAM_SPEAKER_MAP, SARVAM_LANG_MAP

# List of languages and sentences (add more as needed)
LANG_SENTENCES = [
    ("Hindi", "हिंदी", "hi", "आज का दिन बहुत अच्छा है"),
    ("Marathi", "मराठी", "mr", "आजचा दिवस खूप छान आहे"),
    ("Gujarati", "ગુજરાતી", "gu", "આજનો દિવસ બહુ સારો છે"),
    ("Punjabi", "ਪੰਜਾਬੀ", "pa", "ਅੱਜ ਦਾ ਦਿਨ ਬਹੁਤ ਵਧੀਆ ਹੈ"),
    ("Bengali", "বাংলা", "bn", "আজকের দিনটা খুব ভালো"),
    ("Tamil", "தமிழ்", "ta", "இன்று ஒரு சிறந்த நாள்"),
    ("Telugu", "తెలుగు", "te", "ఈ రోజు చాలా మంచి రోజు"),
    ("Kannada", "ಕನ್ನಡ", "kn", "ಇಂದು ಬಹಳ ಒಳ್ಳೆಯ ದಿನ"),
    ("Malayalam", "മലയാളം", "ml", "ഇന്ന് ഒരു നല്ല ദിവസം ആണ്"),
    ("Odia", "ଓଡ଼ିଆ", "or", "ଆଜି ଦିନଟି ବହୁତ ଭଲ"),
    ("Assamese", "অসমীয়া", "as", "আজি এটা বহুত ভাল দিন"),
    ("Maithili", "मैथिली", "mai", "आजुक दिन बहुत नीक अछि"),
    ("Sanskrit", "संस्कृत", "sa", "अद्य उत्तमः दिवसः अस्ति"),
    ("Konkani", "कोंकणी", "kok", "आजो दिवस खूब चांगलो आसा"),
    ("Dogri", "डोगरी", "doi", "अज्ज दा दिन बहुत चंगा ऐ"),
    ("Manipuri / Meitei", "ꯃꯤꯇꯩꯂꯣꯟ", "mni", "ꯑꯣꯖꯥ ꯅꯨꯡꯁꯤ ꯃꯇꯝ ꯑꯃ ꯌꯥꯝꯅ ꯍꯥꯏ"),
    ("Bodo", "बड़ो", "brx", "दानो दिनखौ गासै गोबां"),
    ("Santali", "ᱥᱟᱱᱛᱟᱲᱤ", "sat", "ᱟᱡ ᱫᱤᱱ ᱵᱟᱹᱲᱤᱭᱟ"),
    ("Kashmiri", "कॉशुर", "ks", "اَز چھُ اَکھ گاش دِن"),
    ("Sindhi", "سنڌي", "sd", "اڄ جو ڏينهن تمام سٺو آهي"),
    ("Tulu", "ತುಳು", "tcy", "ಇಂದು ಒಂಜಿ ಚಂದ ದಿನ"),
    ("Khasi", "Ka Ktien Khasi", "kha", "Ka sngi mynta ka long kaba bha"),
    ("Garo", "A·chik", "grt", "Da·ni sal ong·a namgipa sal"),
    ("Mizo", "Mizo ṭawng", "lus", "Tunlai hi ni ṭha a ni"),
    ("Nyishi", "Arunachal Pradesh", "njz", "Aji ami din bo loma"),
    ("Ao", "Naga language", "njo", "Aji dangtsu ya temsu"),
    ("Angami", "Naga language", "njm", "Kezie kevi pfutsie"),
    ("Sema / Sumi", "Naga language", "sumi", "Aji no kupe lo"),
    ("Lepcha", "ᰛᰩᰵᰛᰧᰵ", "lep", "ᰀᰵᰲ ᰛᰧᰵ ᰛᰩᰵ"),
    ("Bhili", "भीली", "bhil", "आज नो दिन खूब सारो छे"),
    ("Gondi", "गोण्डी", "gon", "आज दिना बहोत नीक"),
    ("Kurukh / Oraon", "कुड़ुख", "kru", "आज दिन बहुत अच्छा"),
    ("Ho", "Warang Citi / Latin mix", "hoc", "Aj din bahut badiya"),
    ("Korku", "कोरकू", "korku", "आज दिन खूप चांगला"),
    ("Kodava", "Kodagu / Coorgi", "kod", "Ivattu dina tumba olle"),
    ("Badaga", "ಬಡಗ", "badaga", "Ivattu dina olle iddu"),
    ("Pahari", "Himachali", "pah", "आज दा दिन बड़ा वधिया ऐ"),
    ("Chhattisgarhi", "छत्तीसगढ़ी", "hne", "आज के दिन बहुते बढ़िया हवय"),
    ("Magahi", "मगही", "mag", "आज के दिन बहुत बढ़िया ह"),
    ("Bhojpuri", "भोजपुरी", "bho", "आज के दिन बहुत बढ़िया बा"),
]

def print_sentence(idx, lang_name, native_name, sentence):
    print(f"{idx}. **{lang_name} ({native_name})**\n   👉 {sentence}\n")

def synthesize_and_play(sentence, lang_code, idx):
    # Only synthesize if Sarvam supports the language
    sarvam_code = SARVAM_LANG_MAP.get(lang_code, None)
    if not sarvam_code:
        print(f"   [SKIP] Sarvam TTS not supported for: {lang_code}\n")
        return
    # Always use Ritu
    out_path = Path(tempfile.gettempdir()) / f"tts_{lang_code}_{idx}.wav"
    try:
        _sarvam_tts(sentence, lang_code, str(out_path))
        print(f"   [AUDIO] Saved: {out_path}")
        # Play audio on macOS
        if sys.platform == "darwin":
            os.system(f"afplay '{out_path}' 2>/dev/null")
    except Exception as e:
        print(f"   [ERROR] TTS failed: {e}\n")

if __name__ == "__main__":
    print("\n================= MULTILINGUAL TTS DEMO (RITU/SARVAM) ================\n")
    for idx, (lang_name, native_name, lang_code, sentence) in enumerate(LANG_SENTENCES, 1):
        print_sentence(idx, lang_name, native_name, sentence)
        synthesize_and_play(sentence, lang_code, idx)
        time.sleep(0.5)
    print("\n================= END OF DEMO =================\n")

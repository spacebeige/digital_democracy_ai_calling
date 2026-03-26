"""
Language Segmenter Module
Splits text into language-homogeneous segments.
"""
from dataclasses import dataclass
import os

FASTTEXT_MODEL_PATH = os.environ.get("FASTTEXT_MODEL_PATH", "/tmp/lid.176.bin")
MIN_SEGMENT_WORDS = 2
MERGE_THRESHOLD = 0.15

@dataclass
class TextSegment:
    text: str
    lang: str
    confidence: float
    is_mixed: bool
    word_count: int

class LanguageSegmenter:
    def __init__(self):
        self.model = None

    def segment(self, text: str, fallback_lang: str = "hi") -> list[TextSegment]:
        import re
        MAX_CHARS = 400
        segments = []

        def flush_chunk(chunk_text: str):
            c = (chunk_text or "").strip()
            if not c:
                return
            segments.append(
                TextSegment(
                    text=c,
                    lang=fallback_lang,
                    confidence=0.8,
                    is_mixed=False,
                    word_count=len(c.split()),
                )
            )

        def split_oversized_text(long_text: str) -> list[str]:
            words = (long_text or "").split()
            out = []
            buf = ""
            for w in words:
                candidate = f"{buf} {w}".strip() if buf else w
                if len(candidate) > MAX_CHARS and buf:
                    out.append(buf.strip())
                    buf = w
                else:
                    buf = candidate
            if buf.strip():
                out.append(buf.strip())
            return out
        
        # Split by typical sentence boundaries, keeping delimiters
        sentences = re.split(r'([.।!?])', text)
        buffer = ""
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i]
            delim = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = sentence + delim
            
            if len(buffer) + len(full_sentence) > MAX_CHARS and buffer:
                flush_chunk(buffer)
                buffer = full_sentence
            else:
                buffer += " " + full_sentence if buffer else full_sentence
                
        # Handle the last part if odd length or remaining buffer
        if len(sentences) % 2 != 0:
            last_part = sentences[-1]
            if len(buffer) + len(last_part) > MAX_CHARS and buffer:
                flush_chunk(buffer)
                buffer = last_part
            else:
                buffer += " " + last_part if buffer else last_part

        if buffer.strip():
            if len(buffer.strip()) <= MAX_CHARS:
                flush_chunk(buffer)
            else:
                for piece in split_oversized_text(buffer):
                    flush_chunk(piece)
            
        return segments

_global_segmenter = None

def get_segmenter() -> LanguageSegmenter:
    global _global_segmenter
    if not _global_segmenter:
        _global_segmenter = LanguageSegmenter()
    return _global_segmenter

def segment_text(text: str, fallback_lang: str = "hi") -> list[TextSegment]:
    s = get_segmenter()
    return s.segment(text, fallback_lang)


def detect_segment_boundaries(text: str, primary_lang: str = "hi") -> list[tuple[str, str]]:
    """Compatibility API: returns list of (segment_text, lang_code)."""
    primary = (primary_lang or "hi").split("-")[0]
    segments = segment_text(text, fallback_lang=primary)
    return [(seg.text, seg.lang) for seg in segments if seg.text.strip()]

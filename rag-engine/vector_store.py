import faiss
import numpy as np
import json
from pathlib import Path

dimension = 768
index = faiss.IndexFlatL2(dimension)

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
INDEX_PATH = ARTIFACTS_DIR / "kb.index"
DOCS_PATH = ARTIFACTS_DIR / "kb_docs.json"


def ensure_artifacts_dir() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def add_vector(vector):
    index.add(np.array([vector]))

def search_vector(query_vector):
    distances, indices = index.search(
        np.array([query_vector]), 5
    )
    return distances, indices


def reset_index() -> None:
    global index
    index = faiss.IndexFlatL2(dimension)


def save_index() -> None:
    ensure_artifacts_dir()
    faiss.write_index(index, str(INDEX_PATH))


def load_index() -> bool:
    global index
    if not INDEX_PATH.exists():
        return False
    index = faiss.read_index(str(INDEX_PATH))
    return True


def save_documents(documents: list[dict]) -> None:
    ensure_artifacts_dir()
    DOCS_PATH.write_text(json.dumps(documents, indent=2), encoding="utf-8")


def load_documents() -> list[dict]:
    if not DOCS_PATH.exists():
        return []
    return json.loads(DOCS_PATH.read_text(encoding="utf-8"))
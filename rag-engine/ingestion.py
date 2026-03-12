import hashlib
from pathlib import Path

import numpy as np

from vector_store import add_vector, reset_index, save_documents, save_index


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_SOURCE = DATA_DIR / "knowledge_base.txt"
CHUNK_SEPARATOR = "\n"
VECTOR_DIMENSION = 768


def chunk_text(text: str) -> list[str]:
	chunks = [line.strip() for line in text.split(CHUNK_SEPARATOR) if line.strip()]
	return chunks


def embed_text(text: str, dimension: int = VECTOR_DIMENSION) -> np.ndarray:
	# Deterministic lightweight embedding for MVP; replace with real embedding model later.
	vector = np.zeros(dimension, dtype="float32")
	tokens = text.lower().split()
	if not tokens:
		return vector

	for token in tokens:
		digest = hashlib.sha256(token.encode("utf-8")).digest()
		bucket = int.from_bytes(digest[:4], byteorder="big") % dimension
		vector[bucket] += 1.0

	norm = np.linalg.norm(vector)
	if norm > 0:
		vector /= norm
	return vector


def ingest(source_path: Path = DEFAULT_SOURCE) -> dict:
	if not source_path.exists():
		raise FileNotFoundError(f"Knowledge source not found: {source_path}")

	text = source_path.read_text(encoding="utf-8")
	chunks = chunk_text(text)

	reset_index()
	documents: list[dict] = []

	for chunk_id, chunk in enumerate(chunks):
		vector = embed_text(chunk)
		add_vector(vector)
		documents.append({"id": chunk_id, "text": chunk, "source": str(source_path.name)})

	save_index()
	save_documents(documents)

	return {
		"status": "ok",
		"source": str(source_path),
		"chunks_indexed": len(documents),
	}


if __name__ == "__main__":
	result = ingest()
	print(result)

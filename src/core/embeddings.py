from sentence_transformers import SentenceTransformer
from typing import List

# Load model once (MiniLM = fast, powerful, free)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convert list of texts into embeddings using SentenceTransformer.
    Completely free, no API key needed.
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()

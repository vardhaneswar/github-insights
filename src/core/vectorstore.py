from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

from src.core.embeddings import embed_texts

# Vector DB stored locally
CHROMA_DB_DIR = "data/chroma"
COLLECTION_NAME = "github_activity"


def get_client() -> chromadb.ClientAPI:
    """
    Create a persistent Chroma client.
    This stores embeddings on disk.
    """
    client = chromadb.PersistentClient(
        path=CHROMA_DB_DIR,
        settings=Settings(allow_reset=True)
    )
    return client


def get_collection():
    """
    Create or load the vector collection used for GitHub RAG.
    """
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for HF embeddings
    )


def upsert_documents(
    ids: List[str],
    texts: List[str],
    metadatas: List[Dict[str, Any]],
):
    """
    Add or update documents in Chroma using HF embeddings.
    """
    if not ids:
        return

    if not (len(ids) == len(texts) == len(metadatas)):
        raise ValueError("ids, texts, metadatas must have same length")

    # Convert text → vector embeddings locally (free)
    embeddings = embed_texts(texts)

    collection = get_collection()

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def query_similar(
    repo_full_name: str,
    query_text: str,
    k: int = 10,
):
    """
    Retrieve top-k most relevant documents for the repo based on the question.
    """
    collection = get_collection()

    # Embed the question
    query_embedding = embed_texts([query_text])[0]

    # Query Chroma using metadata filter
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where={"repo": repo_full_name},
    )

    return results

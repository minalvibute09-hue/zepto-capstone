from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "zepto_policies"


class PolicyRetriever:
    def __init__(self):
        self.embedder = SentenceTransformer(MODEL_NAME)

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR)
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self._build_index()

    def _build_index(self):
        documents = []
        ids = []
        metadatas = []

        for path in sorted(DOCS_DIR.glob("doc_*.txt")):
            text = path.read_text(encoding="utf-8").strip()

            if not text:
                continue

            documents.append(text)
            ids.append(path.stem)
            metadatas.append({"source": path.name})

        if not documents:
            raise RuntimeError("No policy documents found in support_assistant/docs.")

        embeddings = self.embedder.encode(
            documents,
            normalize_embeddings=True,
        ).tolist()

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def retrieve(self, query: str, top_k: int = 3):
        query_embedding = self.embedder.encode(
            [query],
            normalize_embeddings=True,
        ).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []

        for i, document in enumerate(results["documents"][0]):
            retrieved.append(
                {
                    "text": document,
                    "source": results["metadatas"][0][i]["source"],
                    "distance": results["distances"][0][i],
                }
            )

        return retrieved
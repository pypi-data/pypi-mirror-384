import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def encode_batch(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Encode texts in batches, return L2 normalized embeddings."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            emb = self.model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
            embeddings.append(emb)
        return np.vstack(embeddings) if embeddings else np.empty((0, self.dim))

    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text, L2 normalized."""
        return self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
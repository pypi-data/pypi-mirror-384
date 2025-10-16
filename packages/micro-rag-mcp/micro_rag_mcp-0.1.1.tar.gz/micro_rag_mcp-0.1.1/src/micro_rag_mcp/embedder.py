import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Optional


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"[DEBUG] Embedder.__init__ starting (lazy loading enabled)", file=sys.stderr, flush=True)
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._dim: Optional[int] = None
        print(f"[DEBUG] Embedder.__init__ completed (model will load on first use)", file=sys.stderr, flush=True)
    
    def _ensure_model_loaded(self):
        """Lazy load the model on first use."""
        if self._model is None:
            print(f"[DEBUG] Loading sentence-transformers model: {self.model_name}", file=sys.stderr, flush=True)
            self._model = SentenceTransformer(self.model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
            print(f"[DEBUG] Model loaded successfully, dim={self._dim}", file=sys.stderr, flush=True)
    
    @property
    def model(self) -> SentenceTransformer:
        """Get the model, loading it if necessary."""
        self._ensure_model_loaded()
        return self._model
    
    @property
    def dim(self) -> int:
        """Get the embedding dimension, loading model if necessary."""
        self._ensure_model_loaded()
        return self._dim

    def encode_batch(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Encode texts in batches, return L2 normalized embeddings."""
        self._ensure_model_loaded()
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            emb = self._model.encode(batch, convert_to_numpy=True, normalize_embeddings=True)
            embeddings.append(emb)
        return np.vstack(embeddings) if embeddings else np.empty((0, self._dim))

    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text, L2 normalized."""
        self._ensure_model_loaded()
        return self._model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
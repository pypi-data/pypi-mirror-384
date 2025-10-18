import sys
import threading
import numpy as np
from typing import List, Optional, TYPE_CHECKING, Any
if TYPE_CHECKING:
    SentenceTransformer = Any


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print(f"[DEBUG] Embedder.__init__ starting (background loading enabled)", file=sys.stderr, flush=True)
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._dim: Optional[int] = None
        self._loaded = threading.Event()

        def _load_model():
            print(f"[DEBUG] Loading sentence-transformers model: {self.model_name}", file=sys.stderr, flush=True)
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dim = self._model.get_sentence_embedding_dimension()
                print(f"[DEBUG] Model loaded successfully, dim={self._dim}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"[ERROR] Model loading failed: {e}", file=sys.stderr, flush=True)
            finally:
                self._loaded.set()

        threading.Thread(target=_load_model, daemon=True).start()
        print(f"[DEBUG] Embedder.__init__ completed (model loading started in background)", file=sys.stderr, flush=True)

    def _ensure_model_loaded(self):
        """Ensure the model is loaded, waiting if necessary."""
        self._loaded.wait()

    def wait_until_loaded(self, timeout: float = None) -> bool:
        """
        Wait until the model is loaded, with optional timeout.
        Returns True if loaded, False if timeout.
        """
        result = self._loaded.wait(timeout)
        if not result:
            print(f"[DEBUG] wait_until_loaded: model not ready after {timeout}s", file=sys.stderr, flush=True)
        return result

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded (non-blocking)."""
        return self._loaded.is_set()

    @property
    def model(self) -> Any:
        """Get the model, loading it if necessary."""
        self._ensure_model_loaded()
        assert self._model is not None
        return self._model

    @property
    def dim(self) -> int:
        """Get the embedding dimension, loading model if necessary."""
        self._ensure_model_loaded()
        assert self._dim is not None
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
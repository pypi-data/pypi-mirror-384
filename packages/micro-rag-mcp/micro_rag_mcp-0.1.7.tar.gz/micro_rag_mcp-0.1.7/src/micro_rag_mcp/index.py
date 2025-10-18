import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
import numpy as np
from typing import Any
from .types import ChunkRecord, FileRecord, Config
from .embedder import Embedder
from .ingest import process_file
from .utils import get_file_mtime, walk_files, acquire_lock, release_lock, compute_checksum


class IndexManager:
    def __init__(self, config: Config, embedder: Embedder):
        print("[DEBUG] IndexManager.__init__ starting...", file=sys.stderr, flush=True)
        self.config = config
        self.embedder = embedder
        self.index_path = Path(config.index_folder) / "faiss.index"
        self.manifest_path = Path(config.index_folder) / "manifest.jsonl"
        self.files_path = Path(config.index_folder) / "files.json"
        self.lock_path = Path(config.index_folder) / "index.lock"
        self.version_path = Path(config.index_folder) / "version"
        self.index: Optional[Any] = None  # faiss.Index, but avoid import at module load
        self.manifest: Dict[int, ChunkRecord] = {}
        self.files: Dict[str, FileRecord] = {}
        self.next_id = 0
        self.load_or_create()

    def load_or_create(self):
        """Load existing index or create new."""
        print("[DEBUG] IndexManager.load_or_create starting...", file=sys.stderr, flush=True)
        Path(self.config.index_folder).mkdir(parents=True, exist_ok=True)
        if self.index_path.exists() and self.manifest_path.exists():
            print("[DEBUG] Loading existing index...", file=sys.stderr, flush=True)
            self.load_index()
            print("[DEBUG] Index loaded successfully", file=sys.stderr, flush=True)
        else:
            print("[DEBUG] Creating new index (will initialize on first use)...", file=sys.stderr, flush=True)
            # Don't create index yet - will be created on first reindex/search
            self.index = None
            print("[DEBUG] Index initialization deferred", file=sys.stderr, flush=True)

    def load_index(self):
        """Load FAISS index and manifest."""
        import faiss
        self.index = faiss.read_index(str(self.index_path))
        with open(self.manifest_path, 'r') as f:
            for line in f:
                record = ChunkRecord(**json.loads(line))
                self.manifest[record.id] = record
                self.next_id = max(self.next_id, record.id + 1)
        if self.files_path.exists():
            with open(self.files_path, 'r') as f:
                data = json.load(f)
                self.files = {k: FileRecord(**v) for k, v in data.items()}

    def save_index(self):
        """Save FAISS index and manifest."""
        import faiss
        faiss.write_index(self.index, str(self.index_path))
        with open(self.manifest_path, 'w') as f:
            for record in self.manifest.values():
                f.write(record.model_dump_json() + '\n')
        with open(self.files_path, 'w') as f:
            json.dump({k: v.model_dump() for k, v in self.files.items()}, f, indent=2)
        self.version_path.write_text("1.0")

    def reindex(self, force: bool = False, path_glob: Optional[str] = None) -> dict:
        """Incremental reindex."""
        if not acquire_lock(self.lock_path):
            print("Reindex already in progress", file=sys.stderr)
            raise RuntimeError("Reindex already in progress")
        try:
            start_time = time.time()
            current_files = set()
            if path_glob:
                # Filter by glob
                all_files = walk_files(Path(self.config.data_folder), self.config.exts)
                current_files = {f for f in all_files if path_glob in str(f)}
                print(f"Reindexing with glob filter: {path_glob}, found {len(current_files)} files", file=sys.stderr)
            else:
                current_files = set(walk_files(Path(self.config.data_folder), self.config.exts))
                print(f"Reindexing all files, found {len(current_files)} files", file=sys.stderr)

            added, updated, removed = 0, 0, 0
            for file_path in current_files:
                rel_path = str(file_path.relative_to(Path(self.config.data_folder)))
                mtime = get_file_mtime(file_path)
                existing = self.files.get(rel_path)
                if existing and existing.mtime == mtime and not force:
                    continue
                chunks = process_file(file_path)
                if not chunks:
                    continue
                checksum = chunks[0][3]  # all chunks have same checksum
                if existing and existing.checksum == checksum and not force:
                    continue
                # Remove old chunks
                if existing:
                    for cid in existing.chunk_ids:
                        if cid in self.manifest:
                            self.manifest[cid].deleted = True
                    updated += 1
                else:
                    added += 1
                # Add new chunks
                chunk_ids = []
                texts = []
                for i, (text, start, end, _) in enumerate(chunks):
                    record = ChunkRecord(
                        id=self.next_id,
                        path=rel_path,
                        ext=file_path.suffix,
                        mtime=mtime,
                        checksum=checksum,
                        chunk_index=i,
                        char_start=start,
                        char_end=end,
                        text=text,
                        embedding_dim=self.embedder.dim
                    )
                    self.manifest[self.next_id] = record
                    chunk_ids.append(self.next_id)
                    texts.append(text)
                    self.next_id += 1
                # Initialize index if needed
                if self.index is None:
                    print("[DEBUG] Initializing index on first reindex...", file=sys.stderr, flush=True)
                    import faiss
                    self.index = faiss.IndexFlatIP(self.embedder.dim)
                
                embeddings = self.embedder.encode_batch(texts)
                self.index.add(embeddings)
                self.files[rel_path] = FileRecord(
                    path=rel_path,
                    mtime=mtime,
                    checksum=checksum,
                    chunk_ids=chunk_ids,
                    ext=file_path.suffix
                )
            # Mark removed files
            for rel_path in list(self.files.keys()):
                if Path(self.config.data_folder) / rel_path not in current_files:
                    for cid in self.files[rel_path].chunk_ids:
                        if cid in self.manifest:
                            self.manifest[cid].deleted = True
                    del self.files[rel_path]
                    removed += 1
            self.save_index()
            elapsed = int((time.time() - start_time) * 1000)
            result = {
                "files_added": added,
                "files_updated": updated,
                "files_removed": removed,
                "chunks_total": len([r for r in self.manifest.values() if not r.deleted]),
                "elapsed_ms": elapsed
            }
            print(f"Reindex completed: {result}", file=sys.stderr)
            return result
        finally:
            release_lock(self.lock_path)

    def search(self, query: str, top_k: int = 5, score_threshold: float = 0.2) -> List[dict]:
        """Search the index, waiting up to 5s for model readiness if needed."""
        # Wait up to 5s for model readiness
        if not self.embedder.wait_until_loaded(timeout=5):
            print("[DEBUG] Model not ready after 5s in search; returning empty results", file=sys.stderr, flush=True)
            return []
        # Initialize index if needed
        if self.index is None:
            print("[DEBUG] Initializing index on first search...", file=sys.stderr, flush=True)
            import faiss
            self.index = faiss.IndexFlatIP(self.embedder.dim)
            self.save_index()
        if self.index.ntotal == 0:
            print("Search: index empty", file=sys.stderr)
            return []
        query_emb = self.embedder.encode_single(query).reshape(1, -1)
        scores, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or score < score_threshold:
                continue
            record = self.manifest.get(idx)
            if record and not record.deleted:
                from .utils import extract_snippet
                snippet = extract_snippet(record.text, query)
                results.append({
                    "path": record.path,
                    "score": float(score),
                    "snippet": snippet,
                    "chunk_index": record.chunk_index,
                    "char_start": record.char_start,
                    "char_end": record.char_end,
                    "mtime": record.mtime,
                    "ext": record.ext
                })
        print(f"Search '{query}' returned {len(results)} results", file=sys.stderr)
        return results
import hashlib
import os
import re
from pathlib import Path
from typing import List, Tuple


def compute_checksum(text: str) -> str:
    """Compute SHA256 checksum of normalized text."""
    normalized = normalize_text(text)
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def normalize_text(text: str) -> str:
    """Normalize text for consistent checksums: strip, normalize newlines."""
    return re.sub(r'\s+', ' ', text.strip())


def get_file_mtime(path: Path) -> float:
    """Get file modification time."""
    return path.stat().st_mtime


def extract_snippet(text: str, query: str, max_length: int = 200) -> str:
    """Extract a snippet around the query in the text."""
    query_lower = query.lower()
    text_lower = text.lower()
    idx = text_lower.find(query_lower)
    if idx == -1:
        return text[:max_length] + "..." if len(text) > max_length else text
    start = max(0, idx - max_length // 2)
    end = min(len(text), idx + len(query) + max_length // 2)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def walk_files(folder: Path, exts: List[str]) -> List[Path]:
    """Walk folder and return files with matching extensions."""
    files = []
    for ext in exts:
        files.extend(folder.rglob(f"*{ext}"))
    return sorted(set(files))  # dedupe and sort


def acquire_lock(lock_path: Path) -> bool:
    """Try to acquire a file lock. Returns True if acquired."""
    try:
        lock_path.touch(exist_ok=False)
        return True
    except FileExistsError:
        return False


def release_lock(lock_path: Path):
    """Release the file lock."""
    lock_path.unlink(missing_ok=True)
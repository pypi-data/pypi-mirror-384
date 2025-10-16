from pydantic import BaseModel
from typing import List, Optional


class ChunkRecord(BaseModel):
    id: int
    path: str
    ext: str
    mtime: float
    checksum: str
    chunk_index: int
    char_start: int
    char_end: int
    text: str
    embedding_dim: int
    deleted: bool = False


class FileRecord(BaseModel):
    path: str
    mtime: float
    checksum: str
    chunk_ids: List[int]
    ext: str


class SearchResult(BaseModel):
    path: str
    score: float
    snippet: str
    chunk_index: int
    char_start: int
    char_end: int
    mtime: float
    ext: str


class ReindexResult(BaseModel):
    files_added: int
    files_updated: int
    files_removed: int
    chunks_total: int
    elapsed_ms: int


class Config(BaseModel):
    data_folder: str
    index_folder: str
    exts: List[str]
    rebuild_threshold: Optional[int] = None
import re
from pathlib import Path
from typing import List, Tuple, Optional
from pypdf import PdfReader
from docx import Document
from charset_normalizer import detect
from .utils import compute_checksum, normalize_text


def read_file(path: Path) -> Optional[str]:
    """Read file content based on extension."""
    try:
        if path.suffix.lower() in ['.txt', '.md']:
            return read_text_file(path)
        elif path.suffix.lower() == '.pdf':
            return read_pdf_file(path)
        elif path.suffix.lower() == '.docx':
            return read_docx_file(path)
        else:
            return None
    except Exception as e:
        print(f"Error reading {path}: {e}", file=__import__('sys').stderr)
        return None


def read_text_file(path: Path) -> str:
    """Read text file with charset detection."""
    with open(path, 'rb') as f:
        raw = f.read()
    detected = detect(raw)
    encoding = detected.get('encoding', 'utf-8')
    return raw.decode(encoding, errors='replace')


def read_pdf_file(path: Path) -> str:
    """Extract text from PDF."""
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def read_docx_file(path: Path) -> str:
    """Extract text from DOCX."""
    doc = Document(path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n\n"
    return text.strip()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Tuple[str, int, int]]:
    """Chunk text into overlapping segments, preserving paragraphs."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Try to break at paragraph boundary
            para_end = text.rfind('\n\n', start, end)
            if para_end > start + chunk_size // 2:
                end = para_end + 2
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, start, end))
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def process_file(path: Path) -> List[Tuple[str, int, int, str]]:
    """Process file: read, chunk, return (text, start, end, checksum)."""
    content = read_file(path)
    if content is None:
        return []
    checksum = compute_checksum(content)
    chunks = chunk_text(content)
    return [(text, start, end, checksum) for text, start, end in chunks]
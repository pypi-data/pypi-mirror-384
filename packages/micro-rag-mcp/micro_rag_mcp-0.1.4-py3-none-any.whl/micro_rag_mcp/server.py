import sys
from typing import Optional
from fastmcp import FastMCP
from .types import Config, ReindexResult, SearchResult
from .embedder import Embedder
from .index import IndexManager
import asyncio


class MicroRAGServer:
    def __init__(self, config: Config):
        print("[DEBUG] MicroRAGServer.__init__ starting...", file=sys.stderr, flush=True)
        self.config = config
        print("[DEBUG] Creating Embedder...", file=sys.stderr, flush=True)
        self.embedder = Embedder()
        print("[DEBUG] Creating IndexManager...", file=sys.stderr, flush=True)
        self.index_manager = IndexManager(config, self.embedder)
        print("[DEBUG] Creating FastMCP instance...", file=sys.stderr, flush=True)
        self.mcp = FastMCP("micro-rag-mcp")
        print("[DEBUG] Registering tools...", file=sys.stderr, flush=True)

        @self.mcp.tool()
        async def search(query: str, top_k: int = 5, score_threshold: float = 0.2) -> list[SearchResult]:
            """Search the document index for relevant chunks."""
            results = self.index_manager.search(query, top_k, score_threshold)
            return [SearchResult(**r) for r in results]

        @self.mcp.tool()
        async def reindex(force: bool = False, path_glob: Optional[str] = None) -> ReindexResult:
            """Reindex documents incrementally."""
            result = self.index_manager.reindex(force, path_glob)
            return ReindexResult(**result)
        
        print("[DEBUG] Tools registered successfully", file=sys.stderr, flush=True)

    def run(self):
        print("[DEBUG] Starting MCP server run()...", file=sys.stderr, flush=True)
        self.mcp.run()
import sys
from typing import Optional
from fastmcp import FastMCP
from .types import Config, ReindexResult, SearchResult
from .embedder import Embedder
from .index import IndexManager
import asyncio


class MicroRAGServer:
    def __init__(self, config: Config):
        import threading
        print(f"[DEBUG][{config.title}|{config.inst}] MicroRAGServer.__init__ starting...", file=sys.stderr, flush=True)
        self.config = config
        print(f"[DEBUG][{config.title}|{config.inst}] Creating Embedder...", file=sys.stderr, flush=True)
        self.embedder = Embedder()
        print(f"[DEBUG][{config.title}|{config.inst}] Creating IndexManager...", file=sys.stderr, flush=True)
        self.index_manager = IndexManager(config, self.embedder)
        print(f"[DEBUG][{config.title}|{config.inst}] Creating FastMCP instance...", file=sys.stderr, flush=True)
        self.mcp = FastMCP(name=config.title, instructions=config.inst)
        print(f"[DEBUG][{config.title}|{config.inst}] Registering tools...", file=sys.stderr, flush=True)

        # Background thread: wait for model, then reindex once
        def _background_initial_reindex():
            print(f"[DEBUG][{config.title}|{config.inst}] Waiting for model readiness before initial reindex...", file=sys.stderr, flush=True)
            self.embedder.wait_until_loaded()
            print(f"[DEBUG][{config.title}|{config.inst}] Model ready, starting initial background reindex...", file=sys.stderr, flush=True)
            try:
                self.index_manager.reindex(force=False)
                print(f"[DEBUG][{config.title}|{config.inst}] Initial background reindex completed.", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"[ERROR][{config.title}|{config.inst}] Initial background reindex failed: {e}", file=sys.stderr, flush=True)

        threading.Thread(target=_background_initial_reindex, daemon=True).start()

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
        print(f"[DEBUG][{self.config.title}|{self.config.inst}] Starting MCP server run()...", file=sys.stderr, flush=True)
        self.mcp.run()
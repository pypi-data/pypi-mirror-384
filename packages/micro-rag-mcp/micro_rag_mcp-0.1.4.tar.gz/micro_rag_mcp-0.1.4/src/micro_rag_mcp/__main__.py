import argparse
import sys
from pathlib import Path
from .types import Config
from .server import MicroRAGServer


def main():
    import sys
    print("[DEBUG] Starting micro_rag_mcp server...", file=sys.stderr, flush=True)
    parser = argparse.ArgumentParser(description="Micro RAG MCP Server")
    parser.add_argument(
        "--data-folder",
        required=True,
        help="Path to the folder containing documents to index"
    )
    parser.add_argument(
        "--index-folder",
        help="Path to store the index (default: <data-folder>/index)"
    )
    parser.add_argument(
        "--exts",
        default=".txt,.md,.pdf,.docx",
        help="Comma-separated list of file extensions to index (default: .txt,.md,.pdf,.docx)"
    )
    parser.add_argument(
        "--rebuild-threshold",
        type=int,
        help="Optional threshold for full rebuild (not implemented yet)"
    )

    args = parser.parse_args()

    print(f"[DEBUG] Parsed arguments, data_folder={args.data_folder}", file=sys.stderr, flush=True)
    
    data_folder = Path(args.data_folder).resolve()
    if not data_folder.is_dir():
        print(f"Error: {data_folder} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"[DEBUG] Data folder validated: {data_folder}", file=sys.stderr, flush=True)

    index_folder = Path(args.index_folder) if args.index_folder else data_folder / "index"
    index_folder = index_folder.resolve()

    exts = [ext.strip() for ext in args.exts.split(",")]

    config = Config(
        data_folder=str(data_folder),
        index_folder=str(index_folder),
        exts=exts,
        rebuild_threshold=args.rebuild_threshold
    )

    print("[DEBUG] Creating MicroRAGServer instance...", file=sys.stderr, flush=True)
    server = MicroRAGServer(config)
    print("[DEBUG] MicroRAGServer created, starting server.run()...", file=sys.stderr, flush=True)
    server.run()


if __name__ == "__main__":
    main()
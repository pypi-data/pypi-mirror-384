"""Command-line interface for running the unified ii-slide service."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import uvicorn

try:
    from ii_slide.frontend import get_dist_path as get_packaged_frontend_path
except ModuleNotFoundError:  # pragma: no cover - package data missing in dev environments
    get_packaged_frontend_path = None  # type: ignore[assignment]


def _locate_frontend_assets() -> Optional[Path]:
    """Locate the built frontend assets, preferring packaged data."""
    if get_packaged_frontend_path is not None:
        packaged_path = get_packaged_frontend_path()
        if packaged_path.exists():
            return packaged_path

    repo_dist = Path(__file__).resolve().parents[2] / "PPTist" / "dist"
    if repo_dist.exists():
        return repo_dist

    return None


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the unified ii-slide backend + packaged frontend"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port for the HTTP server")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (only in development)"
    )
    parser.add_argument(
        "--log-level", default="info", help="Log level passed to uvicorn"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace directory for generated JSON files (defaults to current directory)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    workspace = args.workspace.expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    os.chdir(workspace)

    frontend_path = _locate_frontend_assets()
    if frontend_path is not None:
        os.environ.setdefault("II_SLIDE_STATIC_DIR", str(frontend_path))
    else:
        print("⚠️  Frontend assets not found. Only backend API will be available.", file=sys.stderr)

    uvicorn.run(
        "ii_slide.backend.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

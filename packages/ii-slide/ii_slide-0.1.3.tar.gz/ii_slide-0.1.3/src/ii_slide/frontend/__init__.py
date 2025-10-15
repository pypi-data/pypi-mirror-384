"""Packaged frontend assets for ii-slide."""
from importlib.resources import files
from pathlib import Path


def get_dist_path() -> Path:
    """Return path to bundled frontend dist directory."""
    candidate = files(__name__).joinpath("dist")
    try:
        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path
    except TypeError:
        # When running from a zip archive Path conversion may fail; fall back below
        pass

    repo_path = Path(__file__).resolve().parents[3] / "frontend_dist"
    if repo_path.exists():
        return repo_path

    raise FileNotFoundError("Frontend dist directory not found in package or repository")

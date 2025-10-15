"""Packaged frontend assets for ii-slide."""
from importlib.resources import files
from pathlib import Path


def get_dist_path() -> Path:
    """Return path to bundled frontend dist directory."""
    candidate = files(__name__).joinpath("dist")
    # files returns Traversable; convert to Path for compatibility
    return Path(candidate)

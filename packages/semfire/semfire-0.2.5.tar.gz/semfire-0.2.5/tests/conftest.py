"""
Pytest configuration to ensure local packages are importable during tests.

Adds the repository root and the `src/` directory to `sys.path` so imports like
`src.*` and `spotlighting.*` resolve without requiring an editable install.
"""
import os
import sys


def _ensure_path(path: str) -> None:
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)


# Compute repo root as the parent of the tests directory
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")

_ensure_path(_REPO_ROOT)
_ensure_path(_SRC_DIR)


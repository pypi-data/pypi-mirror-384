"""
Test-friendly import path setup.

This module is auto-imported by Python's site mechanism (if present on sys.path).
It ensures both the repository root (so `src.*` imports work) and the `src`
directory itself (so `detectors`/`api` direct imports work) are available on
`sys.path` without requiring an editable install or environment variables.
"""
from __future__ import annotations

import os
import sys

try:
    repo_root = os.path.dirname(__file__)
    src_dir = os.path.join(repo_root, "src")

    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    if os.path.isdir(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
except Exception:
    # Never fail interpreter startup because of path tweaks
    pass


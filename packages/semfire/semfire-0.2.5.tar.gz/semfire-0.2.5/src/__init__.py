# Package for AI Deception Detection Toolkit
# Prefer SCM-generated version file when available; fall back to package metadata.
try:
    from _version import version as __version__  # type: ignore
except Exception:
    try:
        from importlib.metadata import version as pkg_version, PackageNotFoundError
    except Exception:  # pragma: no cover
        pkg_version = None  # type: ignore
        PackageNotFoundError = Exception  # type: ignore

    try:
        __version__ = pkg_version("semfire") if pkg_version else "0.0.0"  # type: ignore
    except PackageNotFoundError:
        __version__ = "0.0.0"

from .semantic_firewall import SemanticFirewall

__all__ = [
    "SemanticFirewall",
]

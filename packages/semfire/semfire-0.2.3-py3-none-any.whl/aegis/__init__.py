"""
Compatibility package for the old 'aegis' namespace.

This provides import aliases so existing code like:
    - import aegis
    - from aegis import SemanticFirewall
    - from aegis.semantic_firewall import SemanticFirewall
    - from aegis.detectors import EchoChamberDetector
continues to work after the project was renamed to SemFire.

Prefer migrating to the new modules:
    - semantic_firewall
    - detectors
    - api

This package creates sys.modules aliases for key submodules.
"""
from __future__ import annotations

import sys
import warnings
from importlib import import_module


def _alias(old_name: str, new_name: str):
    try:
        mod = import_module(new_name)
        sys.modules[old_name] = mod
        return mod
    except Exception:
        return None


# Emit a deprecation warning once per process.
warnings.warn(
    "The 'aegis' package is deprecated; use 'semfire' modules instead (e.g., 'semantic_firewall', 'detectors').",
    DeprecationWarning,
    stacklevel=2,
)

# Top-level re-exports for common classes
try:
    from semantic_firewall import SemanticFirewall  # type: ignore
except Exception:  # pragma: no cover
    SemanticFirewall = None  # type: ignore

__all__ = ["SemanticFirewall"]

# Namespace aliasing for subpackages/modules
_alias("aegis.semantic_firewall", "semantic_firewall")
_alias("aegis.detectors", "detectors")
_alias("aegis.api", "api")
_alias("aegis.cli", "cli")


"""Compatibility import aliases for SemFire.

This module provides a top-level import path `semfire` to ease the transition
from the former SemFire branding. It re-exports common classes so users can:

    from semfire import SemanticFirewall, EchoChamberDetector

Note: Prefer importing from `semantic_firewall` and `detectors` directly for
explicitness in library code.
"""

from semantic_firewall import SemanticFirewall  # noqa: F401
from detectors import EchoChamberDetector  # noqa: F401

__all__ = ["SemanticFirewall", "EchoChamberDetector"]


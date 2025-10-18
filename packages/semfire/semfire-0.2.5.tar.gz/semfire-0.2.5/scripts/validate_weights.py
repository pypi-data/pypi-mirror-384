#!/usr/bin/env python3
"""
Validate proprietary score weights for SemFire.

Checks the JSON schema and value ranges for `weights/score_weights.json` in the
private repository referenced by the `SemFire_PRV_PATH` environment variable or a
provided `--path`. Defaults to the sibling repo `../semfire-prv`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Tuple


EXPECTED_KEYS = {
    "rule_weight": (float, 0.0, None),
    "heuristic_strong_weight": (float, 0.0, None),
    "heuristic_neutral_weight": (float, 0.0, None),
    "normalization_factor": (float, 0.0, None),
    "classification_threshold": (float, 0.0, None),
}


def load_json(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data: Dict[str, object]) -> Tuple[bool, str]:
    # Check required keys and types/ranges
    missing = [k for k in EXPECTED_KEYS if k not in data]
    if missing:
        return False, f"Missing keys: {', '.join(missing)}"

    # Type and range checks
    for key, (typ, min_val, max_val) in EXPECTED_KEYS.items():
        val = data[key]
        try:
            num = float(val)
        except Exception:
            return False, f"Key '{key}' must be numeric, got {type(val).__name__}"
        if min_val is not None and num <= min_val:
            return False, f"Key '{key}' must be > {min_val}, got {num}"
        if max_val is not None and num > max_val:
            return False, f"Key '{key}' must be <= {max_val}, got {num}"

    # Cross-field heuristics (soft sanity checks)
    if data["heuristic_strong_weight"] < data["heuristic_neutral_weight"]:
        return False, "'heuristic_strong_weight' should be >= 'heuristic_neutral_weight'"

    # Threshold should be less than or equal to plausible maximum combined score.
    # We keep this lenient: threshold must be positive and not wildly larger than normalization.
    if data["classification_threshold"] <= 0:
        return False, "'classification_threshold' must be > 0"
    if data["normalization_factor"] <= 0:
        return False, "'normalization_factor' must be > 0"

    return True, "OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SemFire proprietary score weights JSON.")
    parser.add_argument(
        "--path",
        help="Path to private repo (defaults to $SemFire_PRV_PATH or ../semfire-prv)",
    )
    args = parser.parse_args()

    # Resolve private repo base
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_prv = os.path.abspath(os.path.join(repo_root, "..", "semfire-prv"))
    base = args.path or os.environ.get("SemFire_PRV_PATH", default_prv)
    weights_path = os.path.join(base, "weights", "score_weights.json")

    if not os.path.isfile(weights_path):
        print(
            f"ERROR: Weights file not found at {weights_path}.\n"
            "- Copy ../semfire-prv/weights/score_weights.json.example to score_weights.json and adjust values.\n"
            "- Or set SemFire_PRV_PATH to the private repo path.",
            file=sys.stderr,
        )
        return 2

    try:
        data = load_json(weights_path)
    except Exception as exc:
        print(f"ERROR: Failed to parse JSON at {weights_path}: {exc}", file=sys.stderr)
        return 2

    ok, msg = validate_schema(data)
    if not ok:
        print(f"INVALID: {msg}", file=sys.stderr)
        return 1

    # Success summary
    print("Weights file valid:")
    for k in EXPECTED_KEYS:
        print(f"- {k}: {data[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


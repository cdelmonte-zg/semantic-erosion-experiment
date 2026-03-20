#!/usr/bin/env python3
"""
validate_glossary.py — Validate GLOSSARY.yaml structure and content.

Checks each term has:
  - domain_term (non-empty string)
  - weight (0 < w <= 1)
  - initial_state ("materialized" or "latent")
  - reject (non-empty list of strings)

Usage:
  python experiment/validate_glossary.py collecting-society/GLOSSARY.yaml
"""

import sys
from pathlib import Path

import yaml

VALID_STATES = {"materialized", "latent"}


def validate(glossary_path: str) -> list[str]:
    """Validate glossary and return list of error messages."""
    errors = []

    path = Path(glossary_path)
    if not path.exists():
        return [f"File not found: {glossary_path}"]

    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return ["Top-level YAML must be a mapping"]

    terms = data.get("terms")
    if not isinstance(terms, list):
        return ["'terms' key must be a list"]

    for i, entry in enumerate(terms):
        prefix = f"terms[{i}]"

        # domain_term
        dt = entry.get("domain_term")
        if not dt or not isinstance(dt, str):
            errors.append(f"{prefix}: missing or empty 'domain_term'")
            continue

        prefix = f"terms[{i}] ({dt})"

        # weight
        w = entry.get("weight")
        if w is None:
            errors.append(f"{prefix}: missing 'weight'")
        elif not isinstance(w, (int, float)):
            errors.append(f"{prefix}: 'weight' must be a number, got {type(w).__name__}")
        elif not (0 < w <= 1):
            errors.append(f"{prefix}: 'weight' must be in (0, 1], got {w}")

        # initial_state
        state = entry.get("initial_state")
        if state is None:
            errors.append(f"{prefix}: missing 'initial_state'")
        elif state not in VALID_STATES:
            errors.append(
                f"{prefix}: 'initial_state' must be one of {VALID_STATES}, got '{state}'")

        # reject
        reject = entry.get("reject")
        if reject is None:
            errors.append(f"{prefix}: missing 'reject' list")
        elif not isinstance(reject, list):
            errors.append(f"{prefix}: 'reject' must be a list, got {type(reject).__name__}")
        elif len(reject) == 0:
            errors.append(f"{prefix}: 'reject' list must not be empty")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_glossary.py <glossary.yaml>")
        sys.exit(1)

    glossary_path = sys.argv[1]
    errors = validate(glossary_path)

    if errors:
        print(f"FAIL: {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        # Count terms for summary
        with open(glossary_path) as f:
            data = yaml.safe_load(f)
        terms = data.get("terms", [])
        materialized = sum(1 for t in terms if t.get("initial_state") == "materialized")
        latent = sum(1 for t in terms if t.get("initial_state") == "latent")
        print(f"PASS: {len(terms)} terms validated ({materialized} materialized, {latent} latent)")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
recalculate_es.py — Recalculate ES with fixed denominator on existing results.

The original ES used only extracted latent terms in the denominator,
making ES=1.0 whether 1/4 or 4/4 were extracted. This script fixes ES
to use all latent terms as denominator (matching measure_fidelity.py v4.2).

Usage:
  python experiment/recalculate_es.py results/
"""

import json
import sys
from pathlib import Path


def recalculate(result_file: Path) -> bool:
    """Recalculate ES for a single result file. Returns True if modified."""
    data = json.loads(result_file.read_text())

    terms = data.get("terms")
    if not terms:
        return False

    # Recompute ES with fixed denominator (all latent terms)
    es_numerator = 0.0
    es_denominator = 0.0

    for term_name, info in terms.items():
        if info.get("initial_state") != "latent":
            continue
        weight = info.get("weight", 0.8)
        es_denominator += weight

        state = info.get("state", "")
        if state == "CORRECTLY_MATERIALIZED":
            es_numerator += weight * 1.0
        # ERODED and LATENT contribute 0

    old_es = data.get("emergence_score")
    new_es = round(es_numerator / es_denominator, 4) if es_denominator > 0 else 0.0

    if old_es == new_es:
        return False

    data["emergence_score"] = new_es
    data["emergence_score_v41_original"] = old_es  # keep original for reference
    result_file.write_text(json.dumps(data, indent=2) + "\n")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: recalculate_es.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    modified = 0
    total = 0

    for json_file in sorted(results_dir.rglob("iteration-*.json")):
        total += 1
        if recalculate(json_file):
            modified += 1

    print(f"Processed {total} files, updated {modified} with corrected ES.")


if __name__ == "__main__":
    main()

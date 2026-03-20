#!/usr/bin/env python3
"""
check_threshold.py — CI gate for semantic drift detection.

Dual threshold check:
  --min-ps (default 0.9) — fail if PS below
  --min-es (default 0.5) — fail if ES is not None and below threshold

Exit codes:
  0 — all checks pass
  1 — at least one check fails
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Check PS and ES against minimum thresholds")
    parser.add_argument("--min-ps", type=float, default=0.9,
                        help="Minimum acceptable PS (default: 0.9)")
    parser.add_argument("--min-es", type=float, default=0.5,
                        help="Minimum acceptable ES (default: 0.5)")
    parser.add_argument("--from-json", required=True,
                        help="Read from pre-computed JSON")

    args = parser.parse_args()

    data = json.loads(Path(args.from_json).read_text())
    ps = data.get("preservation_score")
    es = data.get("emergence_score")

    failed = False

    # PS check
    if ps is None:
        print("FAIL: preservation_score not found in JSON")
        failed = True
    else:
        print(f"PS: {ps:.4f} (threshold: {args.min_ps:.4f})")
        if ps < args.min_ps:
            print(f"  FAIL: PS ({ps:.4f}) is below minimum ({args.min_ps:.4f})")
            failed = True
        else:
            print(f"  PASS: PS ({ps:.4f}) meets minimum ({args.min_ps:.4f})")

    # ES check — only if ES is not None (null means no latent terms extracted)
    if es is None:
        print(f"ES: null (no latent terms extracted — skipping threshold check)")
    else:
        print(f"ES: {es:.4f} (threshold: {args.min_es:.4f})")
        if es < args.min_es:
            print(f"  FAIL: ES ({es:.4f}) is below minimum ({args.min_es:.4f})")
            failed = True
        else:
            print(f"  PASS: ES ({es:.4f}) meets minimum ({args.min_es:.4f})")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

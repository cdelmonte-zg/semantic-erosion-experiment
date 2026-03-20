#!/usr/bin/env python3
"""
check_threshold.py — CI gate for semantic drift detection.

Exit codes:
  0 — PS is above threshold (pass)
  1 — PS is below threshold (fail)
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Check Preservation Score against a minimum threshold")
    parser.add_argument("--min-ps", type=float, default=0.9,
                        help="Minimum acceptable PS (default: 0.9)")
    parser.add_argument("--from-json", required=True,
                        help="Read from pre-computed JSON")

    args = parser.parse_args()

    data = json.loads(Path(args.from_json).read_text())
    ps = data.get("preservation_score", data.get("dtd_10", 0.0))

    print(f"PS: {ps:.4f} (threshold: {args.min_ps:.4f})")

    if ps < args.min_ps:
        print(f"FAIL: PS ({ps:.4f}) is below minimum ({args.min_ps:.4f})")
        sys.exit(1)
    else:
        print(f"PASS: PS ({ps:.4f}) meets minimum ({args.min_ps:.4f})")
        sys.exit(0)


if __name__ == "__main__":
    main()

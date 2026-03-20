#!/usr/bin/env python3
"""
measure_dtd.py — Compute Domain Term Density at a given commit.

1. Load GLOSSARY.yaml (term -> [generic_equivalents])
2. Extract identifiers from source tree
3. For each glossary term:
   a. Check if domain term appears in identifiers -> PRESERVED
   b. Check if any generic equivalent appears -> ERODED
   c. Neither -> DISAPPEARED
4. Compute DTD-10, DTD-18, and per-term status
5. For eroded terms, compute semantic distance (original -> replacement)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from extract_identifiers import extract_from_project, split_camel_case

# Lazy-loaded for semantic distance (heavy import)
_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def compute_semantic_distance(term_a: str, term_b: str) -> float:
    """Compute semantic distance between two terms using cosine similarity.

    Returns a value between 0.0 (identical meaning) and 1.0 (completely different).
    """
    if term_a.lower() == term_b.lower():
        return 0.0

    embedder = get_embedder()
    # Insert spaces into camelCase for better embedding
    a_spaced = " ".join(split_camel_case(term_a)).lower()
    b_spaced = " ".join(split_camel_case(term_b)).lower()

    embeddings = embedder.encode([a_spaced, b_spaced])
    # Cosine similarity
    from numpy import dot
    from numpy.linalg import norm
    cos_sim = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
    return round(1.0 - float(cos_sim), 4)


def load_glossary(glossary_path: str) -> list[dict]:
    """Load domain terms from GLOSSARY.yaml."""
    with open(glossary_path) as f:
        data = yaml.safe_load(f)
    return data["terms"]


def find_term_in_identifiers(domain_term: str, raw_identifiers: set[str],
                              by_category: dict[str, set[str]] = None) -> str | None:
    """Check if a domain term appears in identifiers.

    Search priority:
    1. Exact match in class/record/enum/interface names (strongest signal)
    2. Exact match in method names
    3. Exact match in any identifier
    4. Substring match in class/record/enum/interface names only
       (e.g., "RightsHolder" in "RightsHolderRepository")

    Does NOT match substrings in field/variable names to avoid false
    positives like "RightsHolder" in "primaryRightsHolderId".
    """
    # Priority categories: type names first, then methods
    type_categories = {"class_name", "record_name", "enum_name", "interface_name"}
    method_categories = {"method_name"}

    # 1. Exact match in type names
    if by_category:
        for cat in type_categories:
            if cat in by_category and domain_term in by_category[cat]:
                return domain_term

    # 2. Exact match in method names
    if by_category:
        for cat in method_categories:
            if cat in by_category and domain_term in by_category[cat]:
                return domain_term

    # 3. Exact match in any identifier
    if domain_term in raw_identifiers:
        return domain_term

    # 4. Substring match in type names only (e.g., "RightsHolder" in "RightsHolderService")
    if by_category:
        type_names = set()
        for cat in type_categories:
            type_names.update(by_category.get(cat, set()))
        for type_name in type_names:
            if domain_term in type_name:
                return type_name

    return None


def find_erosion_replacement(reject_list: list[str], raw_identifiers: set[str],
                              by_category: dict[str, set[str]] = None) -> str | None:
    """Check if any generic equivalent from the reject list appears in identifiers.

    Exact matching is done against all identifiers.
    Substring matching is restricted to type names only (class, record, enum, interface)
    to avoid false positives (e.g., "Type" matching "getType").
    """
    type_categories = {"class_name", "record_name", "enum_name", "interface_name"}

    for reject_term in reject_list:
        # Exact match against all identifiers
        if reject_term in raw_identifiers:
            return reject_term
        # Substring match restricted to type names only
        if by_category:
            type_names = set()
            for cat in type_categories:
                type_names.update(by_category.get(cat, set()))
            for type_name in type_names:
                if reject_term in type_name:
                    return type_name

    return None


def measure(glossary_path: str, source_root: str,
            compute_distance: bool = True) -> dict:
    """Compute DTD and per-term status.

    Returns the full measurement result as a dict.
    """
    terms = load_glossary(glossary_path)
    extraction = extract_from_project(source_root)
    raw_identifiers = extraction["raw_identifiers"]
    by_category = extraction["by_category"]

    results = {}
    primary_preserved = 0
    primary_total = 0
    all_preserved = 0
    all_total = len(terms)

    for term_entry in terms:
        domain_term = term_entry["domain_term"]
        reject_list = term_entry.get("reject", [])
        term_type = term_entry.get("type", "primary")

        if term_type == "primary":
            primary_total += 1

        # Check if domain term is preserved
        found_as = find_term_in_identifiers(domain_term, raw_identifiers, by_category)
        if found_as is not None:
            results[domain_term] = {
                "status": "preserved",
                "current_name": found_as,
                "distance": 0.0,
                "type": term_type,
            }
            all_preserved += 1
            if term_type == "primary":
                primary_preserved += 1
            continue

        # Check if eroded to a generic equivalent
        eroded_to = find_erosion_replacement(reject_list, raw_identifiers, by_category)
        if eroded_to is not None:
            distance = 0.0
            if compute_distance:
                distance = compute_semantic_distance(domain_term, eroded_to)
            results[domain_term] = {
                "status": "eroded",
                "current_name": eroded_to,
                "distance": distance,
                "type": term_type,
            }
            continue

        # Neither preserved nor found as known generic — disappeared
        results[domain_term] = {
            "status": "disappeared",
            "current_name": None,
            "distance": 1.0,
            "type": term_type,
        }

    dtd_10 = primary_preserved / primary_total if primary_total > 0 else 0.0
    dtd_18 = all_preserved / all_total if all_total > 0 else 0.0

    return {
        "dtd_10": round(dtd_10, 4),
        "dtd_18": round(dtd_18, 4),
        "primary_preserved": primary_preserved,
        "primary_total": primary_total,
        "all_preserved": all_preserved,
        "all_total": all_total,
        "terms": results,
    }


def get_current_commit() -> str:
    """Get the current git commit hash, or 'unknown' if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Measure Domain Term Density for a Java project")
    parser.add_argument("--glossary", required=True,
                        help="Path to GLOSSARY.yaml")
    parser.add_argument("--source", required=True,
                        help="Path to Java source root")
    parser.add_argument("--agent", default="manual",
                        help="Agent name (for output metadata)")
    parser.add_argument("--iteration", type=int, default=0,
                        help="Iteration number (for output metadata)")
    parser.add_argument("--run", type=int, default=1,
                        help="Run number (for output metadata)")
    parser.add_argument("--output", default=None,
                        help="Output JSON file path (default: stdout)")
    parser.add_argument("--no-distance", action="store_true",
                        help="Skip semantic distance computation (faster)")

    args = parser.parse_args()

    result = measure(
        glossary_path=args.glossary,
        source_root=args.source,
        compute_distance=not args.no_distance,
    )

    output = {
        "agent": args.agent,
        "iteration": args.iteration,
        "run": args.run,
        "commit": get_current_commit(),
        **result,
    }

    json_str = json.dumps(output, indent=2, default=str)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str + "\n")
        print(f"Results written to {args.output}")
        print(f"  DTD-10: {result['dtd_10']} ({result['primary_preserved']}/{result['primary_total']})")
        print(f"  DTD-18: {result['dtd_18']} ({result['all_preserved']}/{result['all_total']})")
    else:
        print(json_str)


if __name__ == "__main__":
    main()

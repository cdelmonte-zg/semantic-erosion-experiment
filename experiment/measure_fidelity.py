#!/usr/bin/env python3
"""
measure_fidelity.py — Compute Preservation Score (PS) and Emergence Score (ES).

Replaces measure_dtd.py with the v4.1 metric framework:
- PS: retention of the 6 initially materialized domain terms
- ES: correct materialization of the 4 latent domain terms
- Per-term state tracking with 6 states

Term states:
  MATERIALIZED           — domain term present as a type name (initial state for 6 terms)
  LATENT                 — concept exists but no dedicated type yet (initial state for 4 terms)
  CORRECTLY_MATERIALIZED — latent term emerged with correct domain name
  DEGRADED               — domain term lost from type names, survives in methods/params/fields
  ERODED                 — generic equivalent found in place of domain term
  DISAPPEARED            — neither domain term nor generic equivalent found
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

from extract_identifiers import extract_from_project, split_camel_case

# Lazy-loaded for semantic distance
_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def compute_semantic_distance(term_a: str, term_b: str) -> float:
    if term_a.lower() == term_b.lower():
        return 0.0
    embedder = get_embedder()
    a_spaced = " ".join(split_camel_case(term_a)).lower()
    b_spaced = " ".join(split_camel_case(term_b)).lower()
    embeddings = embedder.encode([a_spaced, b_spaced])
    from numpy import dot
    from numpy.linalg import norm
    cos_sim = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
    return round(1.0 - float(cos_sim), 4)


# Location weights for PS scoring
LOCATION_WEIGHTS = {
    "class_name": 1.0,
    "interface_name": 1.0,
    "enum_name": 1.0,
    "record_name": 1.0,
    "method_name": 0.6,
    "field_name": 0.6,
    "parameter_name": 0.3,
    "local_variable": 0.3,
}

TYPE_CATEGORIES = {"class_name", "record_name", "enum_name", "interface_name"}


def find_term_location_weight(domain_term: str,
                               by_category: dict[str, set[str]]) -> tuple[float, str, str]:
    """Find the highest location weight where a domain term appears.

    Returns (weight, location_category, found_as).
    """
    best_weight = 0.0
    best_category = None
    best_match = None

    for category, identifiers in by_category.items():
        weight = LOCATION_WEIGHTS.get(category, 0.0)
        if weight <= best_weight:
            continue

        # Exact match
        if domain_term in identifiers:
            best_weight = weight
            best_category = category
            best_match = domain_term

        # Substring match in type names only
        if category in TYPE_CATEGORIES:
            for ident in identifiers:
                if domain_term in ident and weight > best_weight:
                    best_weight = weight
                    best_category = category
                    best_match = ident

    return best_weight, best_category, best_match


def find_erosion_in_types(reject_list: list[str],
                           by_category: dict[str, set[str]]) -> str | None:
    """Check if any reject-list term appears as a type name."""
    type_names = set()
    for cat in TYPE_CATEGORIES:
        type_names.update(by_category.get(cat, set()))

    for reject_term in reject_list:
        if reject_term in type_names:
            return reject_term
        for type_name in type_names:
            if reject_term in type_name:
                return type_name

    return None


def load_glossary(glossary_path: str) -> list[dict]:
    with open(glossary_path) as f:
        data = yaml.safe_load(f)
    return data["terms"]


def measure(glossary_path: str, source_root: str,
            compute_distance: bool = True) -> dict:
    """Compute PS, ES, and per-term states."""
    terms = load_glossary(glossary_path)
    extraction = extract_from_project(source_root)
    by_category = extraction["by_category"]

    results = {}
    ps_numerator = 0.0
    ps_denominator = 0.0
    es_numerator = 0.0
    es_denominator = 0.0
    latent_extracted = 0
    latent_total = 0
    materialized_count = 0

    for entry in terms:
        domain_term = entry["domain_term"]
        reject_list = entry.get("reject", [])
        initial_state = entry.get("initial_state", "materialized")
        weight = entry.get("weight", 1.0)

        # Find where the term appears
        loc_weight, loc_category, found_as = find_term_location_weight(
            domain_term, by_category)

        if initial_state == "materialized":
            materialized_count += 1
            ps_denominator += weight

            if loc_weight >= 1.0:
                # Still a type name → MATERIALIZED
                results[domain_term] = {
                    "state": "MATERIALIZED",
                    "current_name": found_as,
                    "location": loc_category,
                    "location_weight": loc_weight,
                    "initial_state": initial_state,
                    "weight": weight,
                }
                ps_numerator += weight * loc_weight

            elif loc_weight > 0:
                # Lost from types but survives in methods/fields → DEGRADED
                results[domain_term] = {
                    "state": "DEGRADED",
                    "current_name": found_as,
                    "location": loc_category,
                    "location_weight": loc_weight,
                    "initial_state": initial_state,
                    "weight": weight,
                }
                ps_numerator += weight * loc_weight

            else:
                # Not found as domain term — check for erosion
                eroded_to = find_erosion_in_types(reject_list, by_category)
                if eroded_to:
                    distance = 0.0
                    if compute_distance:
                        distance = compute_semantic_distance(domain_term, eroded_to)
                    results[domain_term] = {
                        "state": "ERODED",
                        "current_name": eroded_to,
                        "distance": distance,
                        "initial_state": initial_state,
                        "weight": weight,
                    }
                else:
                    results[domain_term] = {
                        "state": "DISAPPEARED",
                        "current_name": None,
                        "initial_state": initial_state,
                        "weight": weight,
                    }

        elif initial_state == "latent":
            latent_total += 1

            if loc_weight >= 1.0:
                # Latent term appeared as a type → CORRECTLY_MATERIALIZED
                latent_extracted += 1
                es_denominator += weight
                es_numerator += weight * 1.0
                results[domain_term] = {
                    "state": "CORRECTLY_MATERIALIZED",
                    "current_name": found_as,
                    "location": loc_category,
                    "initial_state": initial_state,
                    "weight": weight,
                }

            else:
                # Check if a generic equivalent was extracted instead
                eroded_to = find_erosion_in_types(reject_list, by_category)
                if eroded_to:
                    # Extracted with wrong name → ERODED
                    latent_extracted += 1
                    es_denominator += weight
                    es_numerator += 0.0  # eroded emergence = 0
                    distance = 0.0
                    if compute_distance:
                        distance = compute_semantic_distance(domain_term, eroded_to)
                    results[domain_term] = {
                        "state": "ERODED",
                        "current_name": eroded_to,
                        "distance": distance,
                        "initial_state": initial_state,
                        "weight": weight,
                    }
                else:
                    # Still latent — not extracted at all
                    results[domain_term] = {
                        "state": "LATENT",
                        "current_name": None,
                        "initial_state": initial_state,
                        "weight": weight,
                    }

    ps = round(ps_numerator / ps_denominator, 4) if ps_denominator > 0 else 1.0
    es = round(es_numerator / es_denominator, 4) if es_denominator > 0 else None

    return {
        "preservation_score": ps,
        "emergence_score": es,
        "latent_extracted": latent_extracted,
        "latent_total": latent_total,
        "materialized_count": materialized_count,
        "terms": results,
    }


def get_current_commit() -> str:
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
        description="Measure semantic fidelity (PS + ES) for a Java project")
    parser.add_argument("--glossary", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--agent", default="manual")
    parser.add_argument("--prompt-set", default="A")
    parser.add_argument("--iteration", type=int, default=0)
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--output", default=None)
    parser.add_argument("--no-distance", action="store_true")

    args = parser.parse_args()

    result = measure(
        glossary_path=args.glossary,
        source_root=args.source,
        compute_distance=not args.no_distance,
    )

    output = {
        "agent": args.agent,
        "prompt_set": args.prompt_set,
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
        ps = result["preservation_score"]
        es = result["emergence_score"]
        le = result["latent_extracted"]
        lt = result["latent_total"]
        print(f"  PS: {ps} | ES: {es} | Extracted: {le}/{lt}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()

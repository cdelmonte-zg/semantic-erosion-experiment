"""Tests for measure_fidelity.py — PS/ES computation and term matching."""
import pytest

from measure_fidelity import (
    find_term_location_weight,
    load_glossary,
    measure,
)


class TestLoadGlossary:
    def test_loads_successfully(self, glossary_path):
        terms = load_glossary(glossary_path)
        assert isinstance(terms, list)
        assert len(terms) == 10

    def test_term_structure(self, glossary_path):
        terms = load_glossary(glossary_path)
        for term in terms:
            assert "domain_term" in term
            assert "weight" in term
            assert "initial_state" in term
            assert "reject" in term


class TestFindTermLocationWeight:
    def test_exact_class_match(self, sample_by_category):
        weight, loc, found_as, match = find_term_location_weight(
            "RightsHolder", sample_by_category)
        assert weight == 1.0
        assert loc == "class_name"
        assert match == "exact"

    def test_exact_enum_match(self, sample_by_category):
        weight, loc, found_as, match = find_term_location_weight(
            "ExploitationType", sample_by_category)
        assert weight > 0
        assert loc == "enum_name"

    def test_not_found(self, sample_by_category):
        weight, loc, found_as, match = find_term_location_weight(
            "NonExistentTerm", sample_by_category)
        assert weight == 0.0

    def test_method_match_lower_weight(self, sample_by_category):
        # "RightsShares" appears as substring in method "resolveRightsShares"
        weight, loc, found_as, match = find_term_location_weight(
            "RightsShare", sample_by_category)
        # Either not found or found with substring penalty
        assert weight < 1.0


class TestMeasure:
    def test_baseline_preservation_score(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        assert result["preservation_score"] == 1.0, \
            "Baseline codebase should have PS=1.0"

    def test_baseline_has_all_materialized(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        assert result["materialized_count"] == 6

    def test_result_has_required_keys(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        required = {"preservation_score", "emergence_score", "extraction_ratio",
                     "latent_extracted", "latent_total", "materialized_count", "terms"}
        assert required.issubset(result.keys())

    def test_all_terms_tracked(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        assert len(result["terms"]) == 10

    def test_materialized_terms_are_materialized(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        for name, info in result["terms"].items():
            if info["initial_state"] == "materialized":
                assert info["state"] in ("MATERIALIZED", "DEGRADED"), \
                    f"Baseline term {name} should be MATERIALIZED, got {info['state']}"

    def test_latent_terms_are_latent_at_baseline(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        for name, info in result["terms"].items():
            if info["initial_state"] == "latent":
                # At baseline, latent terms should not yet be materialized as types
                assert info["state"] in ("LATENT", "DEGRADED", "CORRECTLY_MATERIALIZED"), \
                    f"Baseline latent term {name} in unexpected state {info['state']}"

    def test_ps_range(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        assert 0.0 <= result["preservation_score"] <= 1.0

    def test_es_range(self, glossary_path, source_root):
        result = measure(glossary_path, source_root, compute_distance=False)
        es = result["emergence_score"]
        assert es is None or 0.0 <= es <= 1.0

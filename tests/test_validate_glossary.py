"""Tests for validate_glossary.py — GLOSSARY.yaml validation."""
import tempfile
from pathlib import Path

import pytest
import yaml

from validate_glossary import validate


class TestValidateGlossary:
    def test_valid_glossary(self, glossary_path):
        errors = validate(glossary_path)
        assert errors == [], f"Glossary validation failed: {errors}"

    def test_correct_term_count(self, glossary_terms):
        assert len(glossary_terms) == 10

    def test_materialized_count(self, glossary_terms):
        materialized = [t for t in glossary_terms if t["initial_state"] == "materialized"]
        assert len(materialized) == 6

    def test_latent_count(self, glossary_terms):
        latent = [t for t in glossary_terms if t["initial_state"] == "latent"]
        assert len(latent) == 4

    def test_all_terms_have_reject_list(self, glossary_terms):
        for term in glossary_terms:
            assert len(term["reject"]) > 0, f"{term['domain_term']} has empty reject list"

    def test_all_weights_valid(self, glossary_terms):
        for term in glossary_terms:
            assert 0 < term["weight"] <= 1.0, \
                f"{term['domain_term']} weight={term['weight']} out of range"

    def test_no_duplicate_terms(self, glossary_terms):
        names = [t["domain_term"] for t in glossary_terms]
        assert len(names) == len(set(names)), f"Duplicate terms: {names}"

    def test_expected_materialized_terms(self, glossary_terms):
        materialized_names = {t["domain_term"] for t in glossary_terms
                              if t["initial_state"] == "materialized"}
        expected = {"RightsHolder", "MusicalWork", "DistributionRun",
                    "UsageReport", "ExploitationType", "RoyaltyStatement"}
        assert materialized_names == expected

    def test_expected_latent_terms(self, glossary_terms):
        latent_names = {t["domain_term"] for t in glossary_terms
                        if t["initial_state"] == "latent"}
        expected = {"SettlementPeriod", "TariffClass", "RightsShare", "DistributionKey"}
        assert latent_names == expected

    def test_missing_file(self):
        errors = validate("/nonexistent/glossary.yaml")
        assert len(errors) > 0

    def test_missing_terms_key(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(yaml.dump({"version": "1.0"}))
        errors = validate(str(bad))
        assert any("terms" in e.lower() for e in errors)

    def test_missing_required_field(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text(yaml.dump({
            "terms": [{"domain_term": "Foo", "weight": 1.0}]  # missing initial_state, reject
        }))
        errors = validate(str(bad))
        assert len(errors) > 0

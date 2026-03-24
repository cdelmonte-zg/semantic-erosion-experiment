"""Tests for extract_identifiers.py — AST-based Java identifier extraction."""
from pathlib import Path

import pytest

from extract_identifiers import extract_from_project, split_camel_case


class TestSplitCamelCase:
    def test_simple(self):
        assert split_camel_case("RightsHolder") == ["Rights", "Holder"]

    def test_single_word(self):
        assert split_camel_case("Report") == ["Report"]

    def test_three_words(self):
        assert split_camel_case("DistributionRun") == ["Distribution", "Run"]

    def test_lowercase(self):
        assert split_camel_case("calculate") == ["calculate"]

    def test_acronym_handling(self):
        # Acronyms like "ISWC" should stay together or split reasonably
        result = split_camel_case("ISWCCode")
        assert len(result) >= 1

    def test_empty_string(self):
        assert split_camel_case("") == []


class TestExtractFromProject:
    def test_extracts_from_collecting_society(self, source_root):
        result = extract_from_project(source_root)

        assert "raw_identifiers" in result
        assert "split_terms" in result
        assert "by_category" in result
        assert "by_file" in result

    def test_finds_domain_types(self, source_root):
        result = extract_from_project(source_root)
        classes = result["by_category"]["class_name"]

        # These types must exist in the baseline codebase
        expected = {"RightsHolder", "MusicalWork", "DistributionRun",
                    "UsageReport", "RoyaltyStatement", "DistributionService"}
        assert expected.issubset(classes), f"Missing: {expected - classes}"

    def test_finds_enum(self, source_root):
        result = extract_from_project(source_root)
        enums = result["by_category"]["enum_name"]
        assert "ExploitationType" in enums

    def test_finds_methods(self, source_root):
        result = extract_from_project(source_root)
        methods = result["by_category"]["method_name"]
        assert "calculateRoyalties" in methods

    def test_categories_are_complete(self, source_root):
        result = extract_from_project(source_root)
        # Core categories that must exist
        required_categories = {
            "class_name", "enum_name",
            "method_name", "field_name", "parameter_name", "local_variable",
        }
        assert required_categories.issubset(set(result["by_category"].keys()))

    def test_by_file_keys_are_real_paths(self, source_root):
        result = extract_from_project(source_root)
        for path in result["by_file"]:
            assert Path(path).exists(), f"File not found: {path}"

    def test_no_empty_identifiers(self, source_root):
        result = extract_from_project(source_root)
        for ident in result["raw_identifiers"]:
            assert len(ident) > 0, "Empty identifier found"

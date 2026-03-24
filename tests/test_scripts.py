"""Tests for shell scripts and experiment configuration."""
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.paths import EXPERIMENT_DIR, PROJECT_ROOT


class TestBashSyntax:
    """Validate all shell scripts pass bash -n (syntax check)."""

    @pytest.mark.parametrize("script", [
        "run_experiment.sh",
        "run_all.sh",
        "run_control_a.sh",
    ])
    def test_syntax(self, script):
        path = EXPERIMENT_DIR / script
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, \
            f"{script} syntax error: {result.stderr}"


class TestExperimentYaml:
    @pytest.fixture
    def config(self):
        with open(EXPERIMENT_DIR / "experiment.yaml") as f:
            return yaml.safe_load(f)

    def test_iterations(self, config):
        assert config["iterations"] == 10

    def test_max_fix_attempts(self, config):
        assert config["max_fix_attempts"] == 3

    def test_prompt_sets_defined(self, config):
        assert set(config["prompt_sets"].keys()) == {"A", "B", "C"}

    def test_all_runs_have_model(self, config):
        """After restructure, every run must have an explicit model."""
        for run in config["runs"]:
            assert "model" in run, \
                f"Run missing model: {run}"

    def test_no_openhands_runs(self, config):
        for run in config["runs"]:
            assert run["agent"] != "openhands", \
                f"OpenHands run found: {run}"

    def test_valid_agents(self, config):
        valid = {"claude_code", "opencode"}
        for run in config["runs"]:
            assert run["agent"] in valid, \
                f"Unknown agent: {run['agent']}"

    def test_valid_prompt_sets(self, config):
        valid = {"A", "B", "C"}
        for run in config["runs"]:
            assert run["prompt_set"] in valid, \
                f"Unknown prompt_set: {run['prompt_set']}"

    def test_runs_positive(self, config):
        for run in config["runs"]:
            assert run["runs"] >= 1

    def test_total_run_count(self, config):
        total = sum(r["runs"] for r in config["runs"])
        assert total == 28, f"Expected 28 total runs, got {total}"


class TestPromptFiles:
    @pytest.mark.parametrize("filename,expected_count", [
        ("prompts_neutral.txt", 5),
        ("prompts_stress.txt", 5),
        ("prompts_implicit.txt", 5),
    ])
    def test_prompt_count(self, filename, expected_count):
        path = EXPERIMENT_DIR / filename
        lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        assert len(lines) == expected_count, \
            f"{filename}: expected {expected_count} prompts, got {len(lines)}"

    def test_stress_prompts_mention_naming(self):
        lines = (EXPERIMENT_DIR / "prompts_stress.txt").read_text().splitlines()
        naming_related = [l for l in lines if "nam" in l.lower() or "rename" in l.lower()]
        assert len(naming_related) >= 3, \
            "Set B should have multiple naming-related prompts"

    def test_implicit_prompts_avoid_rename(self):
        lines = (EXPERIMENT_DIR / "prompts_implicit.txt").read_text().splitlines()
        for line in lines:
            assert "rename" not in line.lower(), \
                f"Set C prompt contains 'rename': {line}"

    def test_neutral_prompts_avoid_naming(self):
        lines = (EXPERIMENT_DIR / "prompts_neutral.txt").read_text().splitlines()
        for line in lines:
            assert "naming" not in line.lower() and "rename" not in line.lower(), \
                f"Set A prompt contains naming language: {line}"


class TestNoOpenHandsReferences:
    """Ensure OpenHands has been completely removed from active code."""

    @pytest.mark.parametrize("filename", [
        "experiment.yaml",
        "run_experiment.sh",
        "run_control_a.sh",
        "run_all.sh",
        "generate_report.py",
        "plot_erosion.py",
        "measure_fidelity.py",
        "extract_identifiers.py",
        "validate_glossary.py",
    ])
    def test_no_openhands_in_file(self, filename):
        path = EXPERIMENT_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} not found")
        content = path.read_text().lower()
        assert "openhands" not in content, \
            f"OpenHands reference found in {filename}"

"""Integration tests for result JSON integrity across all experiment runs."""
import json
from pathlib import Path

import pytest

from tests.paths import RESULTS_DIR

VALID_STATES = {
    "MATERIALIZED", "CORRECTLY_MATERIALIZED", "LATENT",
    "DEGRADED", "ERODED", "DISAPPEARED",
}
VALID_INITIAL_STATES = {"materialized", "latent"}
VALID_PROMPT_SETS = {"A", "B", "C"}


def all_result_files():
    """Collect all iteration-*.json files from results/."""
    files = sorted(RESULTS_DIR.rglob("iteration-*.json"))
    assert len(files) > 0, "No result files found"
    return files


def load_result(path):
    with open(path) as f:
        return json.load(f)


class TestResultFileStructure:
    @pytest.fixture(scope="class")
    def result_files(self):
        return all_result_files()

    def test_minimum_result_count(self, result_files):
        # 28 runs * 11 iterations (0-10) = 308 files minimum
        assert len(result_files) >= 280, \
            f"Expected ~308 result files, found {len(result_files)}"

    def test_all_files_are_valid_json(self, result_files):
        for f in result_files:
            try:
                load_result(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {f}: {e}")

    def test_all_files_have_iteration_field(self, result_files):
        for f in result_files:
            data = load_result(f)
            assert "iteration" in data, f"Missing 'iteration' in {f}"

    def test_all_non_skipped_have_ps(self, result_files):
        for f in result_files:
            data = load_result(f)
            status = data.get("status", "ok")
            if status in ("compilation_failure", "skipped_due_to_prior_failure"):
                continue
            assert "preservation_score" in data, \
                f"Missing 'preservation_score' in {f}"

    def test_ps_values_in_range(self, result_files):
        for f in result_files:
            data = load_result(f)
            ps = data.get("preservation_score")
            if ps is not None:
                assert 0.0 <= ps <= 1.0, f"PS={ps} out of range in {f}"

    def test_es_values_in_range(self, result_files):
        for f in result_files:
            data = load_result(f)
            es = data.get("emergence_score")
            if es is not None:
                assert 0.0 <= es <= 1.0, f"ES={es} out of range in {f}"

    def test_term_states_are_valid(self, result_files):
        for f in result_files:
            data = load_result(f)
            terms = data.get("terms", {})
            for name, info in terms.items():
                state = info.get("state")
                assert state in VALID_STATES, \
                    f"Invalid state '{state}' for {name} in {f}"

    def test_prompt_sets_are_valid(self, result_files):
        for f in result_files:
            data = load_result(f)
            ps = data.get("prompt_set")
            if ps is not None:
                assert ps in VALID_PROMPT_SETS, \
                    f"Invalid prompt_set '{ps}' in {f}"


class TestDirectoryStructure:
    def test_uniform_depth(self):
        """All result dirs should follow: agent/model/set/run-N/."""
        for json_file in RESULTS_DIR.rglob("iteration-*.json"):
            rel = json_file.relative_to(RESULTS_DIR)
            parts = rel.parts
            # Expect: <agent>/<model>/<set>/run-<n>/iteration-<i>.json
            # OR:     <control_type>/<agent>/<model>/<set>/run-<n>/iteration-<i>.json
            run_dir = json_file.parent
            assert run_dir.name.startswith("run-"), \
                f"Expected run-N dir, got {run_dir.name} in {rel}"

    def test_no_openhands_directories(self):
        for d in RESULTS_DIR.rglob("*"):
            assert "openhands" not in d.name, \
                f"OpenHands directory found: {d}"

    def test_model_always_in_path(self):
        """After restructure, model should always be in the path."""
        known_models = {"claude-sonnet-4-6", "gpt-5.4", "qwen3-coder"}
        for json_file in RESULTS_DIR.rglob("iteration-*.json"):
            rel = json_file.relative_to(RESULTS_DIR)
            path_str = str(rel)
            has_model = any(m in path_str for m in known_models)
            assert has_model, \
                f"No model in path: {rel}"


class TestBaselineConsistency:
    def test_all_baselines_have_ps_1(self):
        """Every iteration-0.json should have PS=1.0."""
        for f in RESULTS_DIR.rglob("iteration-0.json"):
            data = load_result(f)
            ps = data.get("preservation_score")
            assert ps == 1.0, \
                f"Baseline PS={ps} in {f}, expected 1.0"

    def test_all_baselines_have_es_0(self):
        """Every iteration-0.json should have ES=0.0 (no latent extracted yet)."""
        for f in RESULTS_DIR.rglob("iteration-0.json"):
            data = load_result(f)
            es = data.get("emergence_score")
            assert es == 0.0, \
                f"Baseline ES={es} in {f}, expected 0.0"


class TestControlRunConsistency:
    def test_strict_controls_have_ps_1(self):
        """All strict control runs should maintain PS=1.0."""
        control_dirs = [
            RESULTS_DIR / "control_a",
        ]
        for ctrl_dir in control_dirs:
            if not ctrl_dir.exists():
                continue
            for f in ctrl_dir.rglob("iteration-*.json"):
                data = load_result(f)
                ps = data.get("preservation_score")
                status = data.get("status", "ok")
                if ps is not None and status == "ok":
                    assert ps == 1.0, \
                        f"Control PS={ps} in {f}, expected 1.0"

    def test_strict_controls_have_high_es_after_baseline(self):
        """Strict controls with domain context should extract most latent terms."""
        for f in (RESULTS_DIR / "control_a").rglob("iteration-*.json"):
            data = load_result(f)
            if data.get("iteration", 0) == 0:
                continue
            es = data.get("emergence_score")
            if es is not None:
                assert es >= 0.75, \
                    f"Control ES={es} in {f.relative_to(RESULTS_DIR)}, expected >= 0.75"

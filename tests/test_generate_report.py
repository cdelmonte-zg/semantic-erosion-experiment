"""Tests for generate_report.py — run discovery and summarization."""
from pathlib import Path

import pytest

from tests.paths import RESULTS_DIR
from generate_report import discover_runs, run_summary


class TestDiscoverRuns:
    def test_discovers_all_runs(self):
        runs = discover_runs(RESULTS_DIR)
        assert len(runs) > 0, "No runs discovered"

    def test_run_keys_are_4_tuples(self):
        runs = discover_runs(RESULTS_DIR)
        for key in runs:
            assert len(key) == 4, f"Expected 4-tuple key, got {key}"
            agent, model, prompt_set, run_name = key
            assert isinstance(agent, str)
            assert isinstance(model, str)
            assert isinstance(prompt_set, str)
            assert isinstance(run_name, str)

    def test_all_runs_have_model(self):
        """After the uniform path restructure, all runs should have a model."""
        runs = discover_runs(RESULTS_DIR)
        for key in runs:
            agent, model, prompt_set, run_name = key
            assert model != "", f"Run {key} has empty model"

    def test_no_openhands_runs(self):
        """OpenHands was removed from the experiment."""
        runs = discover_runs(RESULTS_DIR)
        for key in runs:
            assert "openhands" not in key[0], f"OpenHands run found: {key}"

    def test_iteration_data_is_sorted(self):
        runs = discover_runs(RESULTS_DIR)
        for key, data in runs.items():
            iterations = [d["iteration"] for d in data]
            assert iterations == sorted(iterations), \
                f"Run {key} iterations not sorted: {iterations}"

    def test_baseline_iteration_exists(self):
        runs = discover_runs(RESULTS_DIR)
        for key, data in runs.items():
            iterations = [d["iteration"] for d in data]
            assert 0 in iterations, f"Run {key} missing baseline (iteration 0)"


class TestRunSummary:
    def test_summary_has_required_keys(self):
        runs = discover_runs(RESULTS_DIR)
        key = next(iter(runs))
        summary = run_summary(runs[key])

        required = {"iterations", "ps_min", "ps_max", "ps_mean", "ps_final",
                     "ps_values", "erosion_onset", "direction_changes",
                     "total_insertions", "total_deletions", "compile_fixes"}
        assert required.issubset(summary.keys()), \
            f"Missing keys: {required - set(summary.keys())}"

    def test_ps_values_length_matches_iterations(self):
        runs = discover_runs(RESULTS_DIR)
        for key, data in runs.items():
            summary = run_summary(data)
            non_baseline = [d for d in data if d.get("iteration", 0) > 0
                           and d.get("status", "ok") == "ok"
                           and "preservation_score" in d]
            assert len(summary["ps_values"]) == len(non_baseline), \
                f"Run {key}: ps_values length mismatch"
            break  # test one run is enough

    def test_set_a_no_erosion(self):
        """All Set A runs should have PS=1.0 (no erosion under neutral prompts)."""
        runs = discover_runs(RESULTS_DIR)
        for key, data in runs.items():
            agent, model, prompt_set, run_name = key
            if prompt_set == "A" and "control" not in agent:
                summary = run_summary(data)
                assert summary["ps_final"] == 1.0, \
                    f"Set A run {key} has PS_final={summary['ps_final']}, expected 1.0"

    def test_erosion_onset_none_for_set_a(self):
        """Set A runs should have no erosion onset."""
        runs = discover_runs(RESULTS_DIR)
        for key, data in runs.items():
            agent, model, prompt_set, run_name = key
            if prompt_set == "A" and "control" not in agent:
                summary = run_summary(data)
                assert summary["erosion_onset"] is None, \
                    f"Set A run {key} has erosion_onset={summary['erosion_onset']}"

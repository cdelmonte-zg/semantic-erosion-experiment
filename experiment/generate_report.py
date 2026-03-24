#!/usr/bin/env python3
"""
generate_report.py — Generate experiment report: tables + charts + AI analysis.

Two-phase report generation:
  Phase 1 (Python): tables, charts, data summaries → report_draft.md
  Phase 2 (Claude): reads draft + data, writes analytical text → report.md

Usage:
  python experiment/generate_report.py                    # full report (tables + charts + AI text)
  python experiment/generate_report.py --no-ai            # tables + charts only
  python experiment/generate_report.py --ai-only          # re-run AI analysis on existing draft
"""

import json
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_run(run_dir: Path) -> list[dict]:
    results = []
    for f in sorted(run_dir.glob("iteration-*.json")):
        try:
            d = json.loads(f.read_text())
            if "preservation_score" in d:
                results.append(d)
        except Exception:
            continue
    results.sort(key=lambda r: r["iteration"])
    return results


def discover_runs(results_dir: Path) -> dict:
    runs = {}
    for agent_dir in sorted(results_dir.iterdir()):
        if not agent_dir.is_dir() or agent_dir.name == "control_a":
            continue
        for sub in sorted(agent_dir.iterdir()):
            if not sub.is_dir():
                continue
            if sub.name in ("A", "B", "C"):
                for run_dir in sorted(sub.glob("run-*")):
                    data = load_run(run_dir)
                    if data:
                        runs[(agent_dir.name, "", sub.name, run_dir.name)] = data
            else:
                for ps_dir in sorted(sub.iterdir()):
                    if not ps_dir.is_dir() or ps_dir.name not in ("A", "B", "C"):
                        continue
                    for run_dir in sorted(ps_dir.glob("run-*")):
                        data = load_run(run_dir)
                        if data:
                            runs[(agent_dir.name, sub.name, ps_dir.name, run_dir.name)] = data

    control_dir = results_dir / "control_a"
    if control_dir.exists():
        for agent_dir in sorted(control_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            for sub in sorted(agent_dir.iterdir()):
                if not sub.is_dir():
                    continue
                if sub.name in ("A", "B", "C"):
                    for run_dir in sorted(sub.glob("run-*")):
                        data = load_run(run_dir)
                        if data:
                            runs[(f"control_a/{agent_dir.name}", "", sub.name, run_dir.name)] = data
                else:
                    for ps_dir in sorted(sub.iterdir()):
                        if not ps_dir.is_dir():
                            continue
                        for run_dir in sorted(ps_dir.glob("run-*")):
                            data = load_run(run_dir)
                            if data:
                                runs[(f"control_a/{agent_dir.name}", sub.name, ps_dir.name, run_dir.name)] = data
    # Permissive context runs
    perm_dir = results_dir / "control_a_permissive"
    if perm_dir.exists():
        for agent_dir in sorted(perm_dir.iterdir()):
            if not agent_dir.is_dir():
                continue
            for sub in sorted(agent_dir.iterdir()):
                if not sub.is_dir():
                    continue
                if sub.name in ("A", "B", "C"):
                    for run_dir in sorted(sub.glob("run-*")):
                        data = load_run(run_dir)
                        if data:
                            runs[(f"control_a_permissive/{agent_dir.name}", "", sub.name, run_dir.name)] = data
                else:
                    for ps_dir in sorted(sub.iterdir()):
                        if not ps_dir.is_dir():
                            continue
                        for run_dir in sorted(ps_dir.glob("run-*")):
                            data = load_run(run_dir)
                            if data:
                                runs[(f"control_a_permissive/{agent_dir.name}", sub.name, ps_dir.name, run_dir.name)] = data

    return runs


# ── Analysis ──────────────────────────────────────────────────────────────────

def run_summary(data: list[dict]) -> dict:
    non_baseline = [d for d in data if d["iteration"] > 0]
    if not non_baseline:
        return {}

    ps_values = [d["preservation_score"] for d in non_baseline]
    es_values = [d["emergence_score"] for d in non_baseline if d["emergence_score"] is not None]

    total_ins = sum(d.get("change_analysis", {}).get("insertions", 0) for d in non_baseline)
    total_del = sum(d.get("change_analysis", {}).get("deletions", 0) for d in non_baseline)
    total_files = sum(d.get("change_analysis", {}).get("total_files_changed", 0) for d in non_baseline)
    changes_applied = sum(1 for d in non_baseline if d.get("changes_applied", 0) > 0)
    compile_fixes = sum(1 for d in non_baseline if d.get("compile_autofix", "none") != "none")
    glossary_tampered = sum(1 for d in non_baseline if d.get("glossary_tampered", False))

    last = non_baseline[-1]
    eroded = [t for t, info in last.get("terms", {}).items()
              if info.get("state") in ("ERODED", "DISAPPEARED")]

    # Erosion onset
    erosion_onset = None
    for i, ps in enumerate(ps_values):
        if ps < 1.0:
            erosion_onset = i + 1
            break

    # Oscillation: count direction changes
    direction_changes = 0
    for i in range(1, len(ps_values)):
        if (ps_values[i] - ps_values[i-1]) * (ps_values[i-1] - ps_values[max(0, i-2)]) < 0:
            direction_changes += 1

    return {
        "iterations": len(non_baseline),
        "ps_min": min(ps_values), "ps_max": max(ps_values),
        "ps_mean": round(float(np.mean(ps_values)), 4),
        "ps_final": ps_values[-1], "ps_values": ps_values,
        "es_min": min(es_values) if es_values else None,
        "es_max": max(es_values) if es_values else None,
        "es_mean": round(float(np.mean(es_values)), 4) if es_values else None,
        "es_final": es_values[-1] if es_values else None,
        "es_values": es_values,
        "total_insertions": total_ins, "total_deletions": total_del,
        "total_files_changed": total_files,
        "changes_applied": changes_applied,
        "compile_fixes": compile_fixes,
        "glossary_tampered": glossary_tampered,
        "eroded_terms": eroded,
        "latent_extracted_final": last.get("latent_extracted", 0),
        "latent_total": last.get("latent_total", 4),
        "erosion_onset": erosion_onset,
        "direction_changes": direction_changes,
    }


# ── Charts ────────────────────────────────────────────────────────────────────

def _plot_ps_curves(series: list[tuple[str, list[dict], str, str]],
                    title: str, output: Path):
    """Plot PS curves. series = [(label, data, color, style), ...]"""
    fig, ax = plt.subplots(figsize=(11, 6))
    for label, data, color, style in series:
        iters = [d["iteration"] for d in data]
        vals = [d["preservation_score"] for d in data]
        ax.plot(iters, vals, marker="o", label=label, color=color,
                linestyle=style, linewidth=2, markersize=5)
    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Preservation Score", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(range(0, 11))
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.8, color="red", linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


def _plot_ps_curves_multi_run(series: list[tuple[str, list[list[dict]], str, str]],
                               title: str, output: Path):
    """Plot PS curves with mean+stddev for multi-run agents."""
    fig, ax = plt.subplots(figsize=(11, 6))
    for label, all_runs, color, style in series:
        if len(all_runs) == 1:
            data = all_runs[0]
            iters = [d["iteration"] for d in data]
            vals = [d["preservation_score"] for d in data]
            ax.plot(iters, vals, marker="o", label=label, color=color,
                    linestyle=style, linewidth=2, markersize=5)
        else:
            max_iter = max(d["iteration"] for run in all_runs for d in run)
            matrix = np.full((len(all_runs), max_iter + 1), np.nan)
            for r_idx, run in enumerate(all_runs):
                for d in run:
                    matrix[r_idx, d["iteration"]] = d["preservation_score"]
            iters = list(range(max_iter + 1))
            mean = np.nanmean(matrix, axis=0)
            std = np.nanstd(matrix, axis=0)
            ax.plot(iters, mean, marker="o", label=f"{label} (n={len(all_runs)})",
                    color=color, linestyle=style, linewidth=2, markersize=5)
            ax.fill_between(iters, mean - std, mean + std, alpha=0.15, color=color)
    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Preservation Score", fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(range(0, 11))
    ax.legend(fontsize=9, loc="lower left")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.8, color="red", linestyle=":", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


def _plot_heatmap(data: list[dict], title: str, output: Path):
    if not data:
        return
    all_terms = list(data[0]["terms"].keys())
    S2V = {"MATERIALIZED": 0, "CORRECTLY_MATERIALIZED": 1, "LATENT": 2,
           "DEGRADED": 3, "ERODED": 4, "DISAPPEARED": 5}
    matrix = np.zeros((len(all_terms), len(data)))
    for j, d in enumerate(data):
        for i, term in enumerate(all_terms):
            state = d["terms"].get(term, {}).get("state", "DISAPPEARED").upper()
            matrix[i, j] = S2V.get(state, 5)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#2ecc71", "#1a9641", "#999999", "#f1c40f", "#e67e22", "#e74c3c"]
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5], cmap.N)
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, norm=norm)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([d["iteration"] for d in data])
    ax.set_yticks(range(len(all_terms)))
    ax.set_yticklabels(all_terms, fontsize=9)
    ax.set_xlabel("Iteration"); ax.set_ylabel("Domain Term")
    ax.set_title(title, fontsize=13)
    V2S = {v: k for k, v in S2V.items()}
    for i in range(len(all_terms)):
        for j in range(len(data)):
            val = int(matrix[i, j])
            tc = "white" if val >= 4 else "black"
            cur = data[j]["terms"].get(all_terms[i], {}).get("current_name", "?")
            if cur and len(cur) > 15:
                cur = cur[:14] + "…"
            ax.text(j, i, f"{cur}\n{V2S.get(val, '?')}", ha="center", va="center",
                    fontsize=5.5, color=tc)
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, ticks=range(6))
    cbar.ax.set_yticklabels(list(S2V.keys()), fontsize=7)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


def _plot_refactoring_volume(labels, insertions, deletions, title, output):
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w/2, insertions, w, label="Insertions", color="#2ecc71", alpha=0.8)
    ax.bar(x + w/2, deletions, w, label="Deletions", color="#e74c3c", alpha=0.8)
    ax.set_ylabel("Lines"); ax.set_title(title, fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    ax.legend(); ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()


# ── Report: Phase 1 (Python) ─────────────────────────────────────────────────

def generate_draft(results_dir: Path, output_dir: Path) -> tuple[Path, dict]:
    """Generate report_draft.md with tables, charts, and placeholders for AI text."""
    runs = discover_runs(results_dir)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    w = lines.append

    w("# Semantic Erosion Experiment — Results Report")
    w(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # ── Summary table ─────────────────────────────────────────────────
    w("## 1. Results Summary\n")
    w("<!-- AI:intro -->")
    w("<!-- /AI -->\n")

    run_configs = [
        # Phase 1 + 2: Set A and B
        ("Claude Code", "claude_code", "claude-sonnet-4-6", "A", 1),
        ("Claude Code", "claude_code", "claude-sonnet-4-6", "B", 1),
        ("OpenCode (Sonnet 4.6)", "opencode", "claude-sonnet-4-6", "A", 1),
        ("OpenCode (Sonnet 4.6)", "opencode", "claude-sonnet-4-6", "B", 1),
        ("OpenCode + GPT-5.4", "opencode", "gpt-5.4", "A", 2),
        ("OpenCode + GPT-5.4", "opencode", "gpt-5.4", "B", 2),
        ("OpenCode + Qwen3 30B", "opencode", "qwen3-coder", "A", 2),
        ("OpenCode + Qwen3 30B", "opencode", "qwen3-coder", "B", 2),
        # Phase 3: Set C (implicit rename pressure)
        ("Claude Code", "claude_code", "claude-sonnet-4-6", "C", 3),
        ("OpenCode (Sonnet 4.6)", "opencode", "claude-sonnet-4-6", "C", 3),
        ("OpenCode + GPT-5.4", "opencode", "gpt-5.4", "C", 3),
        ("OpenCode + Qwen3 30B", "opencode", "qwen3-coder", "C", 3),
        # Control A (Set A + context)
        ("Ctrl-A: Claude Code", "control_a/claude_code", "claude-sonnet-4-6", "A", 1),
        ("Ctrl-A: OC+Sonnet", "control_a/opencode", "claude-sonnet-4-6", "A", 1),
        ("Ctrl-A: OC+GPT-5.4", "control_a/opencode", "gpt-5.4", "A", 2),
        ("Ctrl-A: OC+Qwen3", "control_a/opencode", "qwen3-coder", "A", 2),
        # Control B (Set B + context)
        ("Ctrl-B: Claude Code", "control_a/claude_code", "claude-sonnet-4-6", "B", 1),
        ("Ctrl-B: OC+Sonnet", "control_a/opencode", "claude-sonnet-4-6", "B", 1),
        ("Ctrl-B: OC+GPT-5.4", "control_a/opencode", "gpt-5.4", "B", 2),
        ("Ctrl-B: OC+Qwen3", "control_a/opencode", "qwen3-coder", "B", 2),
        # Permissive context (Set B + permissive context)
        ("Permissive: Claude Code", "control_a_permissive/claude_code", "claude-sonnet-4-6", "B", 1),
        ("Permissive: OC+GPT-5.4", "control_a_permissive/opencode", "gpt-5.4", "B", 2),
    ]

    w("| Agent / Model | Set | PS min | PS final | ES final | Latent | Erosion Onset | +Lines | -Lines | Compile Fixes |")
    w("|---|---|---|---|---|---|---|---|---|---|")

    all_summaries = {}
    for label, ak, model, ps, phase in run_configs:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == model and k[2] == ps]
        if not matching:
            continue
        data = matching[0][1]
        s = run_summary(data)
        if not s:
            continue
        all_summaries[(ak, model, ps)] = s
        es_f = f"{s['es_final']:.2f}" if s['es_final'] is not None else "—"
        onset = f"iter {s['erosion_onset']}" if s['erosion_onset'] else "—"
        w(f"| {label} | {ps} | {s['ps_min']:.2f} | {s['ps_final']:.2f} | "
          f"{es_f} | {s['latent_extracted_final']}/{s['latent_total']} | {onset} | "
          f"+{s['total_insertions']} | -{s['total_deletions']} | {s['compile_fixes']} |")
    w("")

    # ── Phase 1 charts ────────────────────────────────────────────────
    w("## 2. Phase 1 — Agent Comparison (Claude Sonnet 4.6)\n")
    w("<!-- AI:phase1 -->")
    w("<!-- /AI -->\n")

    # Set A
    w("### 2.1 Set A (Neutral Prompts)\n")
    series_a = []
    for ak, label, color, style in [
        ("claude_code", "Claude Code", "#e74c3c", "-"),
        ("opencode", "OpenCode", "#3498db", "--"),
    ]:
        all_runs_a = [v for k, v in runs.items() if k[0] == ak and k[1] == "claude-sonnet-4-6" and k[2] == "A"]
        if all_runs_a:
            series_a.append((label, all_runs_a, color, style))
    _plot_ps_curves_multi_run(series_a, "Phase 1 Set A — Preservation Score",
                               fig_dir / "phase1_setA.png")
    w("![Phase 1 Set A](figures/phase1_setA.png)\n")

    # Set B
    w("### 2.2 Set B (Stress Prompts)\n")
    series_b = []
    for ak, label, color, style in [
        ("claude_code", "Claude Code", "#e74c3c", "-"),
        ("opencode", "OpenCode", "#3498db", "--"),
    ]:
        all_runs_b = [v for k, v in runs.items() if k[0] == ak and k[1] == "claude-sonnet-4-6" and k[2] == "B"]
        if all_runs_b:
            series_b.append((label, all_runs_b, color, style))
    _plot_ps_curves_multi_run(series_b, "Phase 1 Set B — Preservation Score",
                               fig_dir / "phase1_setB.png")
    w("![Phase 1 Set B](figures/phase1_setB.png)\n")

    w("<!-- AI:phase1_analysis -->")
    w("<!-- /AI -->\n")

    # Heatmaps
    for ak, label in [("claude_code", "Claude Code"), ("opencode", "OpenCode (Sonnet)")]:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == "claude-sonnet-4-6" and k[2] == "B"]
        if matching:
            s = run_summary(matching[0][1])
            if s and s["ps_min"] < 1.0:
                fname = f"heatmap_{ak}_B.png"
                _plot_heatmap(matching[0][1], f"{label} Set B — Term States", fig_dir / fname)
                w(f"![{label} Set B Heatmap](figures/{fname})\n")

    # ── Phase 2 charts ────────────────────────────────────────────────
    w("## 3. Phase 2 — Model Comparison (OpenCode agent)\n")
    w("<!-- AI:phase2 -->")
    w("<!-- /AI -->\n")

    for ps_label, ps_name, ps_key in [("Set A (Neutral)", "setA", "A"), ("Set B (Stress)", "setB", "B")]:
        w(f"### 3.{1 if ps_key == 'A' else 2} {ps_label}\n")
        series = []
        for model, label, color in [
            ("claude-sonnet-4-6", "Sonnet 4.6", "#3498db"),
            ("gpt-5.4", "GPT-5.4", "#9b59b6"),
            ("qwen3-coder", "Qwen3-Coder 30B", "#e67e22"),
        ]:
            matching = [(k, v) for k, v in runs.items()
                        if k[0] == "opencode" and k[1] == model and k[2] == ps_key]
            if matching:
                series.append((label, matching[0][1], color, "-"))
        _plot_ps_curves(series, f"Phase 2 {ps_label} — Model Comparison",
                        fig_dir / f"phase2_{ps_name}.png")
        w(f"![Phase 2 {ps_label}](figures/phase2_{ps_name}.png)\n")

        # Heatmaps for eroding models
        if ps_key == "B":
            for model, mlabel in [("gpt-5.4", "GPT-5.4"), ("qwen3-coder", "Qwen3-Coder 30B")]:
                matching = [(k, v) for k, v in runs.items()
                            if k[0] == "opencode" and k[1] == model and k[2] == "B"]
                if matching:
                    s = run_summary(matching[0][1])
                    if s and s["ps_min"] < 1.0:
                        fname = f"heatmap_opencode_{model}_B.png"
                        _plot_heatmap(matching[0][1], f"OpenCode + {mlabel} Set B", fig_dir / fname)
                        w(f"![{mlabel} Heatmap](figures/{fname})\n")

    w("<!-- AI:phase2_analysis -->")
    w("<!-- /AI -->\n")

    # ── Phase 3: Set C ────────────────────────────────────────────────
    w("## 4. Phase 3 — Set C (Implicit Rename Pressure)\n")
    w("<!-- AI:setc -->")
    w("<!-- /AI -->\n")

    # Set C chart: all agents/models (cloud as single, Qwen3 as multi-run)
    setc_configs = [
        ("Claude Code", "claude_code", "claude-sonnet-4-6", "#e74c3c"),
        ("OpenCode+Sonnet", "opencode", "claude-sonnet-4-6", "#3498db"),
        ("OpenCode+GPT-5.4", "opencode", "gpt-5.4", "#9b59b6"),
        ("OpenCode+Qwen3", "opencode", "qwen3-coder", "#e67e22"),
    ]
    setc_multi = []
    for label, ak, model, color in setc_configs:
        all_c = [v for k, v in runs.items()
                 if k[0] == ak and k[1] == model and k[2] == "C"]
        if all_c:
            setc_multi.append((label, all_c, color, "-"))
    if setc_multi:
        _plot_ps_curves_multi_run(setc_multi,
                                   "Set C (Implicit Rename Pressure) — Preservation Score",
                                   fig_dir / "phase3_setC.png")
    w("![Set C](figures/phase3_setC.png)\n")

    w("<!-- AI:setc_analysis -->")
    w("<!-- /AI -->\n")

    # ── Control A ─────────────────────────────────────────────────────
    w("## 5. Control A — Domain Context Mitigation\n")

    control_series = []
    for label, ak, model, ps, color, style in [
        ("Claude Code (no ctx)", "claude_code", "claude-sonnet-4-6", "B", "#e74c3c", "--"),
        ("Claude Code + ctx", "control_a/claude_code", "claude-sonnet-4-6", "A", "#1abc9c", "-"),
        ("GPT-5.4 (no ctx)", "opencode", "gpt-5.4", "B", "#9b59b6", "--"),
        ("GPT-5.4 + ctx", "control_a/opencode", "gpt-5.4", "A", "#8e44ad", "-"),
        ("Qwen3 (no ctx)", "opencode", "qwen3-coder", "B", "#e67e22", "--"),
        ("Qwen3 + ctx", "control_a/opencode", "qwen3-coder", "A", "#d35400", "-"),
    ]:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == model and k[2] == ps]
        if matching:
            control_series.append((label, matching[0][1], color, style))
    _plot_ps_curves(control_series, "Control A — Domain Context Mitigation",
                    fig_dir / "control_a.png")
    w("![Control A](figures/control_a.png)\n")

    w("<!-- AI:control_a -->")
    w("<!-- /AI -->\n")

    # ── Control B (Set B + context) ───────────────────────────────────
    w("## 6. Control B — Domain Context Under Stress\n")

    controlb_series = []
    for label, ak, model, ps, color, style in [
        ("Claude Code Set B (no ctx)", "claude_code", "claude-sonnet-4-6", "B", "#e74c3c", "--"),
        ("Claude Code Ctrl-B", "control_a/claude_code", "claude-sonnet-4-6", "B", "#1abc9c", "-"),
        ("GPT-5.4 Set B (no ctx)", "opencode", "gpt-5.4", "B", "#9b59b6", "--"),
        ("GPT-5.4 Ctrl-B", "control_a/opencode", "gpt-5.4", "B", "#8e44ad", "-"),
        ("Qwen3 Set B (no ctx)", "opencode", "qwen3-coder", "B", "#e67e22", "--"),
        ("Qwen3 Ctrl-B", "control_a/opencode", "qwen3-coder", "B", "#d35400", "-"),
    ]:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == model and k[2] == ps]
        if matching:
            controlb_series.append((label, matching[0][1], color, style))
    if controlb_series:
        _plot_ps_curves(controlb_series, "Control B — Domain Context Under Stress Prompts",
                        fig_dir / "control_b.png")
        w("![Control B](figures/control_b.png)\n")

    w("<!-- AI:control_b -->")
    w("<!-- /AI -->\n")

    # ── Permissive Context ────────────────────────────────────────────
    w("## 7. Permissive Context — Balancing Protection and Refactoring\n")

    perm_series = []
    for label, ak, model, ps, color, style in [
        ("Claude Code Set B (no ctx)", "claude_code", "claude-sonnet-4-6", "B", "#e74c3c", "--"),
        ("Claude Code Ctrl-B (strict)", "control_a/claude_code", "claude-sonnet-4-6", "B", "#1abc9c", "-."),
        ("Claude Code Permissive", "control_a_permissive/claude_code", "claude-sonnet-4-6", "B", "#2ecc71", "-"),
        ("GPT-5.4 Set B (no ctx)", "opencode", "gpt-5.4", "B", "#9b59b6", "--"),
        ("GPT-5.4 Permissive", "control_a_permissive/opencode", "gpt-5.4", "B", "#8e44ad", "-"),
    ]:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == model and k[2] == ps]
        if matching:
            perm_series.append((label, matching[0][1], color, style))
    if perm_series:
        _plot_ps_curves(perm_series, "Permissive Context — Protection vs Refactoring",
                        fig_dir / "permissive.png")
        w("![Permissive Context](figures/permissive.png)\n")

    w("<!-- AI:permissive -->")
    w("<!-- /AI -->\n")

    # ── Refactoring effectiveness ─────────────────────────────────────
    w("## 8. Refactoring Effectiveness\n")

    ref_configs = [
        ("CC Set A", "claude_code", "claude-sonnet-4-6", "A"),
        ("CC Set B", "claude_code", "claude-sonnet-4-6", "B"),
        ("CC Set C", "claude_code", "claude-sonnet-4-6", "C"),
        ("OC+Son Set A", "opencode", "claude-sonnet-4-6", "A"),
        ("OC+Son Set B", "opencode", "claude-sonnet-4-6", "B"),
        ("OC+Son Set C", "opencode", "claude-sonnet-4-6", "C"),
        ("GPT-5.4 Set A", "opencode", "gpt-5.4", "A"),
        ("GPT-5.4 Set B", "opencode", "gpt-5.4", "B"),
        ("GPT-5.4 Set C", "opencode", "gpt-5.4", "C"),
        ("Qwen3 Set A", "opencode", "qwen3-coder", "A"),
        ("Qwen3 Set B", "opencode", "qwen3-coder", "B"),
        ("Qwen3 Set C", "opencode", "qwen3-coder", "C"),
    ]

    w("| Agent | Set | Active Iters | +Lines | -Lines | Net | Files | Compile Fixes | Glossary Tampered |")
    w("|---|---|---|---|---|---|---|---|---|")
    ref_labels, ref_ins, ref_del = [], [], []
    for label, ak, model, ps in ref_configs:
        matching = [(k, v) for k, v in runs.items()
                    if k[0] == ak and k[1] == model and k[2] == ps]
        if not matching:
            continue
        s = run_summary(matching[0][1])
        if not s:
            continue
        net = s["total_insertions"] - s["total_deletions"]
        net_s = f"+{net}" if net >= 0 else str(net)
        w(f"| {label} | {ps} | {s['changes_applied']}/10 | "
          f"+{s['total_insertions']} | -{s['total_deletions']} | {net_s} | "
          f"{s['total_files_changed']} | {s['compile_fixes']} | {s['glossary_tampered']} |")
        ref_labels.append(label)
        ref_ins.append(s["total_insertions"])
        ref_del.append(s["total_deletions"])

    w("")
    _plot_refactoring_volume(ref_labels, ref_ins, ref_del,
                              "Refactoring Volume — Lines Changed", fig_dir / "refactoring_volume.png")
    w("![Refactoring Volume](figures/refactoring_volume.png)\n")

    w("<!-- AI:refactoring -->")
    w("<!-- /AI -->\n")

    # ── Key Findings placeholder ──────────────────────────────────────
    w("## 9. Key Findings\n")
    w("<!-- AI:findings -->")
    w("<!-- /AI -->\n")

    # Write draft
    draft_path = output_dir / "report_draft.md"
    draft_path.write_text("\n".join(lines) + "\n")

    # Write data summary as JSON for AI consumption
    data_summary = {}
    for (ak, model, ps), s in all_summaries.items():
        key = f"{ak}/{model}/{ps}" if model else f"{ak}/{ps}"
        data_summary[key] = {k: v for k, v in s.items()
                              if k not in ("ps_values", "es_values")}
        data_summary[key]["ps_curve"] = s["ps_values"]
        data_summary[key]["es_curve"] = s.get("es_values", [])

    data_path = output_dir / "data_summary.json"
    data_path.write_text(json.dumps(data_summary, indent=2, default=str) + "\n")

    print(f"Draft report: {draft_path}")
    print(f"Data summary: {data_path}")
    print(f"Figures: {fig_dir}/")

    return draft_path, data_summary


# ── Report: Phase 2 (Claude) ─────────────────────────────────────────────────

AI_PROMPT = """You are analyzing the results of a semantic erosion experiment.
The experiment measures how AI coding agents erode domain-specific terminology
during iterative refactoring of a Java DDD project.

Below is the report draft with tables and charts (referenced as images).
Your task: replace each <!-- AI:xxx --> ... <!-- /AI --> placeholder with
analytical text (2-5 paragraphs each). Write in English, be concise and precise.

For each section:
- AI:intro — Explain what the experiment measures, the setup (10 iterations, 3 prompt sets A/B/C, 3 agents, 3 models, 31 runs)
- AI:phase1 — Introduce Phase 1 (vary agent, fix model)
- AI:phase1_analysis — Analyze Phase 1 results: Set A vs Set B, which agents erode, oscillation patterns
- AI:phase2 — Introduce Phase 2 (fix agent OpenCode, vary model)
- AI:phase2_analysis — Compare models: erosion aggressiveness, onset timing, latent extraction
- AI:setc — Introduce Set C: implicit rename pressure without explicit "rename" keyword. Key question: does erosion require explicit instructions?
- AI:setc_analysis — Set C results: cloud models (Sonnet, GPT-5.4) show PS=1.0 (no erosion). Qwen3 30B local erodes (PS drops to 0.38). This means smaller models are more susceptible to implicit pressure. Include Qwen3 variance across 3 replicas.
- AI:control_a — Analyze Control A: domain context prevents erosion but suppresses ALL refactoring (0 changes). Universal across all agents/models.
- AI:control_b — Analyze Control B: does domain context protect under stress prompts (Set B)? Compare with Set B without context.
- AI:permissive — Analyze permissive context: does a less restrictive domain context allow refactoring while preventing erosion? Compare strict vs permissive vs no context.
- AI:refactoring — Analyze refactoring volume across A/B/C. Is more refactoring correlated with more erosion? Compile fix frequency.
- AI:findings — 7-9 numbered key findings including Set C threshold finding and context inhibition finding

Data summary (JSON):
```json
{data_json}
```

Report draft:
```markdown
{draft}
```

Output the COMPLETE report (not just the replacements). Keep all tables, image references,
and structure intact. Replace only the AI placeholder blocks."""


def run_ai_analysis(draft_path: Path, data_summary: dict, output_dir: Path) -> Path:
    draft = draft_path.read_text()
    data_json = json.dumps(data_summary, indent=2, default=str)

    prompt = AI_PROMPT.format(data_json=data_json, draft=draft)

    print("Running Claude for AI analysis...")
    result = subprocess.run(
        ["claude", "--dangerously-skip-permissions", "-p", prompt],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        print(f"WARNING: Claude exited with code {result.returncode}")
        print(result.stderr[:500] if result.stderr else "")
        # Fall back to draft
        report_path = output_dir / "report.md"
        report_path.write_text(draft)
        return report_path

    report_text = result.stdout.strip()

    # Extract markdown from Claude's response (skip any preamble)
    if "# Semantic Erosion" in report_text:
        report_text = report_text[report_text.index("# Semantic Erosion"):]

    report_path = output_dir / "report.md"
    report_path.write_text(report_text + "\n")
    print(f"Final report: {report_path}")
    return report_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate experiment report")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--output-dir", default="report")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI analysis, generate draft only")
    parser.add_argument("--ai-only", action="store_true", help="Re-run AI on existing draft")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.ai_only:
        draft_path = output_dir / "report_draft.md"
        data_path = output_dir / "data_summary.json"
        if not draft_path.exists() or not data_path.exists():
            print("ERROR: No existing draft found. Run without --ai-only first.")
            sys.exit(1)
        data_summary = json.loads(data_path.read_text())
        run_ai_analysis(draft_path, data_summary, output_dir)
    else:
        draft_path, data_summary = generate_draft(Path(args.results_dir), output_dir)
        if not args.no_ai:
            run_ai_analysis(draft_path, data_summary, output_dir)


if __name__ == "__main__":
    main()

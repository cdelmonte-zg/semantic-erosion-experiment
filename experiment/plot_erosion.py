#!/usr/bin/env python3
"""
plot_erosion.py — Generate erosion curve charts and heatmaps from experiment results.

Reads per-iteration JSON files from results/ and produces:
  1. Erosion Curves (DTD over iterations, per agent)
  2. Semantic Distance Heatmap (per term, per iteration)
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


def load_results(results_dir: str, agent: str, run: int = 1) -> list[dict]:
    """Load all iteration results for a given agent and run."""
    agent_dir = Path(results_dir) / agent
    if run > 1:
        agent_dir = agent_dir / f"run-{run}"

    results = []
    for json_file in sorted(agent_dir.glob("iteration-*.json")):
        data = json.loads(json_file.read_text())
        # Skip failed/skipped iterations without DTD data
        if "iteration" in data and "dtd_10" in data:
            results.append(data)

    results.sort(key=lambda r: r["iteration"])
    return results


def load_all_runs(results_dir: str, agent: str, max_runs: int = 3) -> list[list[dict]]:
    """Load results across multiple runs for variance analysis."""
    runs = []
    for run_num in range(1, max_runs + 1):
        agent_dir = Path(results_dir) / agent / f"run-{run_num}"
        if not agent_dir.exists():
            # Try without run subdirectory (single run agents)
            if run_num == 1:
                agent_dir = Path(results_dir) / agent
            else:
                break

        run_results = []
        for json_file in sorted(agent_dir.glob("iteration-*.json")):
            data = json.loads(json_file.read_text())
            # Skip failed/skipped iterations without DTD data
            if "iteration" in data and "dtd_10" in data:
                run_results.append(data)

        if run_results:
            run_results.sort(key=lambda r: r["iteration"])
            runs.append(run_results)

    return runs


def plot_erosion_curves(results_dir: str, agents: list[str],
                        metric: str = "dtd_10", output: str = "erosion_curves.png"):
    """Chart 1: Erosion curves — DTD over iterations for each agent."""
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = plt.cm.tab10.colors
    styles = ["-", "--", "-.", ":", "-"]

    for i, agent in enumerate(agents):
        runs = load_all_runs(results_dir, agent)
        if not runs:
            print(f"  Warning: no results found for agent '{agent}', skipping")
            continue

        if len(runs) == 1:
            # Single run — plot as simple line
            iterations = [0] + [r["iteration"] for r in runs[0]]
            values = [1.0] + [r[metric] for r in runs[0]]
            ax.plot(iterations, values, marker="o", label=agent,
                    color=colors[i % len(colors)], linestyle=styles[i % len(styles)],
                    linewidth=2, markersize=5)
        else:
            # Multiple runs — plot mean with stddev band
            max_iter = max(r["iteration"] for run in runs for r in run)
            all_values = np.full((len(runs), max_iter + 1), np.nan)

            for r_idx, run in enumerate(runs):
                all_values[r_idx, 0] = 1.0  # baseline
                for result in run:
                    it = result["iteration"]
                    if it <= max_iter:
                        all_values[r_idx, it] = result[metric]

            iterations = list(range(max_iter + 1))
            mean_values = np.nanmean(all_values, axis=0)
            std_values = np.nanstd(all_values, axis=0)

            ax.plot(iterations, mean_values, marker="o", label=agent,
                    color=colors[i % len(colors)], linestyle=styles[i % len(styles)],
                    linewidth=2, markersize=5)
            ax.fill_between(iterations,
                            mean_values - std_values,
                            mean_values + std_values,
                            alpha=0.15, color=colors[i % len(colors)])

    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel(f"Domain Term Density ({metric.upper()})", fontsize=12)
    ax.set_title("Semantic Erosion: Domain Term Density Over Iterations", fontsize=14)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(range(0, 11))
    ax.legend(fontsize=10, loc="lower left")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0.8, color="red", linestyle=":", alpha=0.5, label="Threshold (0.8)")

    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Erosion curves saved to {output}")


def plot_distance_heatmap(results_dir: str, agent: str,
                          output: str = "distance_heatmap.png"):
    """Chart 2: Semantic distance heatmap for a single agent."""
    runs = load_all_runs(results_dir, agent)
    if not runs:
        print(f"  No results found for agent '{agent}'")
        return

    results = runs[0]  # Use first run for heatmap
    if not results:
        return

    # Collect all domain terms
    all_terms = list(results[0]["terms"].keys())
    n_terms = len(all_terms)
    n_iterations = len(results)

    # Build distance matrix
    matrix = np.zeros((n_terms, n_iterations))

    for iter_idx, result in enumerate(results):
        for term_idx, term in enumerate(all_terms):
            term_data = result["terms"].get(term, {})
            status = term_data.get("status", "disappeared")
            if status == "preserved":
                matrix[term_idx, iter_idx] = 0.0
            elif status == "eroded":
                matrix[term_idx, iter_idx] = term_data.get("distance", 0.5)
            else:  # disappeared
                matrix[term_idx, iter_idx] = 1.0

    fig, ax = plt.subplots(figsize=(12, 8))

    # Custom colormap: green (preserved) -> yellow (partial) -> red (eroded)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "erosion", ["#2ecc71", "#f1c40f", "#e74c3c"])

    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=1)

    ax.set_xticks(range(n_iterations))
    ax.set_xticklabels([r["iteration"] for r in results])
    ax.set_yticks(range(n_terms))
    ax.set_yticklabels(all_terms, fontsize=9)

    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Domain Term", fontsize=12)
    ax.set_title(f"Semantic Distance Heatmap — {agent}", fontsize=14)

    # Add text annotations
    for i in range(n_terms):
        for j in range(n_iterations):
            val = matrix[i, j]
            text_color = "white" if val > 0.6 else "black"
            term_data = results[j]["terms"].get(all_terms[i], {})
            current = term_data.get("current_name", "?")
            if current and len(current) > 15:
                current = current[:14] + "..."
            ax.text(j, i, f"{current}\n{val:.2f}",
                    ha="center", va="center", fontsize=6, color=text_color)

    plt.colorbar(im, ax=ax, label="Semantic Distance", shrink=0.8)
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    print(f"Distance heatmap saved to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate erosion charts from experiment results")
    parser.add_argument("--results-dir", default="results",
                        help="Path to results directory")
    parser.add_argument("--agents", nargs="+",
                        default=["claude_code", "copilot", "aider_local",
                                 "control_a_claude", "control_a_aider"],
                        help="Agent names to include in erosion curves")
    parser.add_argument("--metric", choices=["dtd_10", "dtd_18"], default="dtd_10",
                        help="DTD metric for erosion curves")
    parser.add_argument("--output-dir", default="article/figures",
                        help="Output directory for figures")
    parser.add_argument("--heatmap-agent", default=None,
                        help="Agent for distance heatmap (default: first agent)")

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Generating erosion curves...")
    plot_erosion_curves(
        args.results_dir,
        args.agents,
        metric=args.metric,
        output=str(out_dir / "erosion_curves.png"),
    )

    heatmap_agent = args.heatmap_agent or args.agents[0]
    print(f"Generating distance heatmap for {heatmap_agent}...")
    plot_distance_heatmap(
        args.results_dir,
        heatmap_agent,
        output=str(out_dir / "distance_heatmap.png"),
    )


if __name__ == "__main__":
    main()

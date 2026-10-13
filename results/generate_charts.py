"""Generate FINDINGS.md charts from results.csv.

Produces four PNGs in results/:
  fig1_reach_rates.png    – per-model susceptibility at depth thresholds
  fig2_technique_heatmap.png – technique × model mean intent depth
  fig3_vector_ranking.png – entry vector mean depth
  fig4_detection_rates.png – per-model injection detection rate
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

RESULTS = os.path.join(os.path.dirname(__file__), "results.csv")
OUT_DIR = os.path.dirname(__file__)

# -- palette (dataviz reference: blue sequential + categorical) --
BLUE = "#2a78d6"
BLUE_LIGHT = "#86b6ef"
BLUE_DARK = "#184f95"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

MODEL_ORDER = [
    "gemini-2.5-flash", "o3-mini", "gpt-4.1", "gpt-4.1-mini",
    "gemini-2.5-flash-lite", "gpt-4o-mini", "deepseek-chat",
    "gemini-2.5-pro", "claude-haiku-4-5", "deepseek-reasoner",
    "claude-sonnet-5",
]

MODEL_SHORT = {
    "gemini-2.5-flash": "Gemini Flash",
    "o3-mini": "o3-mini",
    "gpt-4.1": "GPT-4.1",
    "gpt-4.1-mini": "GPT-4.1-mini",
    "gemini-2.5-flash-lite": "Gemini Flash-Lite",
    "gpt-4o-mini": "GPT-4o-mini",
    "deepseek-chat": "DeepSeek V3",
    "gemini-2.5-pro": "Gemini Pro",
    "claude-haiku-4-5": "Claude Haiku",
    "deepseek-reasoner": "DeepSeek R1",
    "claude-sonnet-5": "Claude Sonnet 5",
}

FAMILY_COLORS = {
    "gemini-2.5-flash": AQUA,
    "o3-mini": ORANGE,
    "gpt-4.1": ORANGE,
    "gpt-4.1-mini": ORANGE,
    "gemini-2.5-flash-lite": AQUA,
    "gpt-4o-mini": ORANGE,
    "deepseek-chat": YELLOW,
    "gemini-2.5-pro": AQUA,
    "claude-haiku-4-5": BLUE,
    "deepseek-reasoner": YELLOW,
    "claude-sonnet-5": BLUE,
}

TECH_ORDER = [
    "fake_completion", "combined", "observation_spoof", "policy_mode",
    "config_in_data", "context_grounded", "conditional", "fake_system",
    "urgency", "direct", "obfuscated", "obfuscated_base64",
    "delimiter_confusion",
]

TECH_SHORT = {
    "fake_completion": "Fake completion",
    "combined": "Combined",
    "observation_spoof": "Obs. spoof",
    "policy_mode": "Policy mode",
    "config_in_data": "Config-in-data",
    "context_grounded": "Context grounded",
    "conditional": "Conditional",
    "fake_system": "Fake system",
    "urgency": "Urgency",
    "direct": "Direct",
    "obfuscated": "Obfuscated",
    "obfuscated_base64": "Obfusc. base64",
    "delimiter_confusion": "Delimiter conf.",
}

VECTOR_ORDER = [
    "dependency_metadata", "pr_body", "issue_comment",
    "readme", "code_comment", "filename", "commit_msg",
]

VECTOR_SHORT = {
    "dependency_metadata": "Dependency metadata",
    "pr_body": "PR body",
    "issue_comment": "Issue comment",
    "readme": "README",
    "code_comment": "Code comment",
    "filename": "Filename",
    "commit_msg": "Commit message",
}


def load_data():
    models = defaultdict(lambda: {"total": 0, "r1": 0, "r2": 0, "r3": 0, "r5": 0, "detected": 0})
    tech_model = defaultdict(lambda: defaultdict(list))
    vector_depths = defaultdict(list)

    with open(RESULTS) as f:
        for row in csv.DictReader(f):
            m = row["model"]
            depth = int(row["intent_depth"])
            detected = row["detected"].strip().lower() == "true"
            tech = row.get("variant", "").split("-")[-1] if row.get("variant") else "unknown"
            vector = row.get("entry_vector", "unknown")

            models[m]["total"] += 1
            if depth >= 1: models[m]["r1"] += 1
            if depth >= 2: models[m]["r2"] += 1
            if depth >= 3: models[m]["r3"] += 1
            if depth >= 5: models[m]["r5"] += 1
            if detected: models[m]["detected"] += 1

            tech_model[tech][m].append(depth)
            vector_depths[vector].append(depth)

    return models, tech_model, vector_depths


def style_ax(ax, title, xlabel=None, ylabel=None):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, fontsize=13, fontweight="bold", color=INK, pad=12, loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color=SECONDARY)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color=SECONDARY)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.grid(axis="x", color=GRIDLINE, linewidth=0.5)
    ax.set_axisbelow(True)


def fig1_reach_rates(models):
    """Grouped horizontal bars: reach ≥1, ≥2, ≥3, ≥5 per model."""
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor(SURFACE)

    labels = [MODEL_SHORT[m] for m in MODEL_ORDER]
    y = np.arange(len(labels))
    h = 0.18

    thresholds = [
        ("≥1 Any rung", "r1", "#cde2fb"),
        ("≥2 Tool use", "r2", "#6da7ec"),
        ("≥3 Secret read", "r3", "#2a78d6"),
        ("≥5 Downstream exec", "r5", "#0d366b"),
    ]

    for i, (lbl, key, color) in enumerate(thresholds):
        vals = [models[m][key] / models[m]["total"] * 100 for m in MODEL_ORDER]
        bars = ax.barh(y + i * h - 1.5 * h, vals, height=h - 0.02, color=color, label=lbl,
                       zorder=3, edgecolor=SURFACE, linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 2:
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}%", va="center", ha="left", fontsize=7, color=SECONDARY)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.legend(fontsize=8, loc="lower right", frameon=False, labelcolor=SECONDARY)
    style_ax(ax, "Model susceptibility by intent depth", xlabel="% of trials")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig1_reach_rates.png"), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("  fig1_reach_rates.png")


def fig2_technique_heatmap(tech_model):
    """Technique × model heatmap of mean intent depth."""
    matrix = []
    for tech in TECH_ORDER:
        row = []
        for m in MODEL_ORDER:
            depths = tech_model[tech].get(m, [])
            row.append(sum(depths) / len(depths) if depths else 0)
        matrix.append(row)

    data = np.array(matrix)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.patch.set_facecolor(SURFACE)

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "depth", ["#fcfcfb", "#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"], N=256
    )
    im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=0, vmax=2.5)

    ax.set_xticks(np.arange(len(MODEL_ORDER)))
    ax.set_xticklabels([MODEL_SHORT[m] for m in MODEL_ORDER], fontsize=8, rotation=40,
                       ha="right", color=INK)
    ax.set_yticks(np.arange(len(TECH_ORDER)))
    ax.set_yticklabels([TECH_SHORT[t] for t in TECH_ORDER], fontsize=9, color=INK)

    for i in range(len(TECH_ORDER)):
        for j in range(len(MODEL_ORDER)):
            v = data[i, j]
            if v > 0.005:
                text_color = "#ffffff" if v > 1.2 else INK
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color=text_color)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Mean intent depth", fontsize=9, color=SECONDARY)
    cbar.ax.tick_params(colors=MUTED, labelsize=8)
    cbar.outline.set_edgecolor(BASELINE)

    ax.set_title("Technique effectiveness by model", fontsize=13, fontweight="bold",
                 color=INK, pad=12, loc="left")
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig2_technique_heatmap.png"), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("  fig2_technique_heatmap.png")


def fig3_vector_ranking(vector_depths):
    """Horizontal bars: entry vector mean depth."""
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(SURFACE)

    labels = [VECTOR_SHORT[v] for v in VECTOR_ORDER]
    vals = [sum(vector_depths[v]) / len(vector_depths[v]) for v in VECTOR_ORDER]
    y = np.arange(len(labels))

    bars = ax.barh(y, vals, height=0.55, color=BLUE, zorder=3, edgecolor=SURFACE, linewidth=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", ha="left", fontsize=9, color=SECONDARY)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals) * 1.15)
    style_ax(ax, "Entry vector effectiveness", xlabel="Mean intent depth (pooled)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig3_vector_ranking.png"), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("  fig3_vector_ranking.png")


def fig4_detection_rates(models):
    """Horizontal bars: detection rate per model, colored by family."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(SURFACE)

    det_order = sorted(MODEL_ORDER, key=lambda m: models[m]["detected"] / models[m]["total"], reverse=True)
    labels = [MODEL_SHORT[m] for m in det_order]
    vals = [models[m]["detected"] / models[m]["total"] * 100 for m in det_order]
    colors = [FAMILY_COLORS[m] for m in det_order]
    y = np.arange(len(labels))

    bars = ax.barh(y, vals, height=0.55, color=colors, zorder=3, edgecolor=SURFACE, linewidth=0.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", ha="left", fontsize=9, color=SECONDARY)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)

    from matplotlib.patches import Patch
    legend_items = [
        Patch(facecolor=BLUE, label="Anthropic"),
        Patch(facecolor=YELLOW, label="DeepSeek"),
        Patch(facecolor=AQUA, label="Google"),
        Patch(facecolor=ORANGE, label="OpenAI"),
    ]
    ax.legend(handles=legend_items, fontsize=8, loc="lower right", frameon=False,
              labelcolor=SECONDARY)

    style_ax(ax, "Injection detection rate by model", xlabel="% of trials flagged as injection")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig4_detection_rates.png"), dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print("  fig4_detection_rates.png")


if __name__ == "__main__":
    print("Generating charts from results.csv...")
    models, tech_model, vector_depths = load_data()
    fig1_reach_rates(models)
    fig2_technique_heatmap(tech_model)
    fig3_vector_ranking(vector_depths)
    fig4_detection_rates(models)
    print("Done.")

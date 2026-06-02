#!/usr/bin/env python3
"""
Angels Academy AI — Test Report Generator v2 (Chart Edition)
Generates a visual, chart-heavy PDF report to help choose hardware + model combinations.
Uses matplotlib for charts embedded in a reportlab PDF.
"""

import io
import json
import math
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

RESULTS_DIR = Path(__file__).parent / "results_v2"
REPORT_FILE = RESULTS_DIR / "angels_academy_ai_test_report_v2.pdf"

# ── Brand palette ──
DARK_BLUE = "#213953"
TEAL = "#2a7886"
GREEN = "#a6c52e"
LIGHT_BG = "#f4f6f8"
WHITE_HEX = "#ffffff"

# Tier colors — red/amber/green for hardware decision-making
TIER_COLORS = {
    "small": "#e74c3c",       # red — RPi5
    "medium": "#f39c12",      # amber — Jetson
    "large_local": "#27ae60", # green — GPU server
}
TIER_LABELS = {
    "small": "RPi5 — Small 0.8-2B",
    "medium": "Jetson — Medium 4-12B",
    "large_local": "GPU — Large 14-35B",
}
TIER_SHORT = {"small": "RPi5", "medium": "Jetson", "large_local": "GPU"}
TIER_ORDER = ["small", "medium", "large_local"]

MODEL_ORDER = [
    "qwen3.5:0.8b", "qwen3.5:2b", "llama3.2:1b",
    "qwen3.5:4b", "qwen3.5:9b", "llama3.1:8b", "mistral-nemo:12b",
    "qwen3.5:35b-a3b", "deepseek-r1:14b", "phi4:14b", "mistral-small3.2:24b",
]
MODEL_TIERS = {
    "qwen3.5:0.8b": "small", "qwen3.5:2b": "small", "llama3.2:1b": "small",
    "qwen3.5:4b": "medium", "qwen3.5:9b": "medium", "llama3.1:8b": "medium", "mistral-nemo:12b": "medium",
    "qwen3.5:35b-a3b": "large_local", "deepseek-r1:14b": "large_local", "phi4:14b": "large_local", "mistral-small3.2:24b": "large_local",
}
MODEL_PARAMS = {
    "qwen3.5:0.8b": 0.8, "qwen3.5:2b": 2, "llama3.2:1b": 1,
    "qwen3.5:4b": 4, "qwen3.5:9b": 9, "llama3.1:8b": 8, "mistral-nemo:12b": 12,
    "qwen3.5:35b-a3b": 35, "deepseek-r1:14b": 14, "phi4:14b": 14, "mistral-small3.2:24b": 24,
}
# Short display names for chart labels
MODEL_SHORT = {
    "qwen3.5:0.8b": "Qwen3.5\n0.8B", "qwen3.5:2b": "Qwen3.5\n2B", "llama3.2:1b": "Llama3.2\n1B",
    "qwen3.5:4b": "Qwen3.5\n4B", "qwen3.5:9b": "Qwen3.5\n9B", "llama3.1:8b": "Llama3.1\n8B", "mistral-nemo:12b": "Mistral\nNemo 12B",
    "qwen3.5:35b-a3b": "Qwen3.5\n35B-A3B", "deepseek-r1:14b": "DeepSeek\nR1 14B", "phi4:14b": "Phi4\n14B", "mistral-small3.2:24b": "Mistral\nSmall 24B",
}

LANG_NAMES = {
    "en": "English", "fr": "French", "ar": "Arabic",
    "my": "Burmese", "th": "Thai", "pt": "Portuguese", "es": "Spanish"
}
LANG_ORDER = ["en", "fr", "es", "pt", "ar", "th", "my"]

CAT_ORDER = ["vocabulary", "lesson_prep", "theological", "guardrails", "multilingual",
             "reading_comprehension", "child_safety", "esl_methodology"]
CAT_SHORT = {
    "vocabulary": "Vocabulary", "lesson_prep": "Lesson Prep",
    "theological": "Theology", "guardrails": "Guardrails",
    "multilingual": "Multilingual", "reading_comprehension": "Reading",
    "child_safety": "Child Safety", "esl_methodology": "ESL Method",
}

METRICS = ["accuracy", "language_quality", "safety", "completeness", "usefulness"]
METRIC_LABELS = {
    "accuracy": "Accuracy", "language_quality": "Language", "safety": "Safety",
    "completeness": "Completeness", "usefulness": "Usefulness", "rag_quality": "RAG",
    "overall": "Overall",
}


# ═══════════════════════════════════════════════════════════════
# Chart helpers
# ═══════════════════════════════════════════════════════════════

def fig_to_image(fig, width_mm=170, dpi=180):
    """Convert a matplotlib figure to a reportlab Image flowable."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    w = width_mm * mm
    # read image dimensions to get aspect ratio
    from PIL import Image as PILImage
    pil_img = PILImage.open(buf)
    aspect = pil_img.height / pil_img.width
    buf.seek(0)
    return Image(buf, width=w, height=w * aspect)


def apply_style(ax, title="", xlabel="", ylabel=""):
    """Apply consistent styling to axes."""
    ax.set_title(title, fontsize=13, fontweight="bold", color=DARK_BLUE, pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color="#555")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color="#555")
    ax.tick_params(labelsize=9, colors="#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ccc")
    ax.spines["bottom"].set_color("#ccc")
    ax.grid(axis="both", alpha=0.2, color="#888")


def avg(lst):
    return sum(lst) / len(lst) if lst else 0


# ═══════════════════════════════════════════════════════════════
# Chart generators
# ═══════════════════════════════════════════════════════════════

def chart_model_ranking(by_model):
    """Horizontal bar chart: all 11 models ranked by overall score, color-coded by tier."""
    models = sorted(MODEL_ORDER, key=lambda m: by_model.get(m, {}).get("overall", 0))
    scores = [by_model.get(m, {}).get("overall", 0) for m in models]
    bar_colors = [TIER_COLORS[MODEL_TIERS[m]] for m in models]
    labels = [MODEL_SHORT[m].replace("\n", " ") for m in models]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(range(len(models)), scores, color=bar_colors, edgecolor="white", height=0.7)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 5)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(1))

    # Score labels on bars
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                f"{score:.2f}", va="center", fontsize=10, fontweight="bold", color=DARK_BLUE)

    # Legend
    from matplotlib.patches import Patch
    legend_items = [Patch(facecolor=TIER_COLORS[t], label=TIER_LABELS[t]) for t in TIER_ORDER]
    ax.legend(handles=legend_items, loc="lower right", fontsize=9, framealpha=0.9)

    apply_style(ax, "Overall Model Ranking by Hardware Tier", "Score (1-5)")
    ax.axvline(x=3.5, color="#888", linestyle="--", alpha=0.5, linewidth=1)
    ax.text(3.55, len(models)-0.5, "Good threshold", fontsize=8, color="#888", va="top")
    fig.tight_layout()
    return fig


def chart_tier_metrics(by_tier):
    """Grouped bar chart: 3 tiers × 5 metrics side by side."""
    metrics = ["accuracy", "language_quality", "safety", "completeness", "usefulness"]
    metric_labels = [METRIC_LABELS[m] for m in metrics]
    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, tier in enumerate(TIER_ORDER):
        vals = [by_tier[tier].get(m, 0) for m in metrics]
        bars = ax.bar(x + i*width, vals, width, label=TIER_LABELS[tier],
                      color=TIER_COLORS[tier], edgecolor="white")
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{v:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x + width)
    ax.set_xticklabels(metric_labels, fontsize=10)
    ax.set_ylim(0, 5.5)
    ax.legend(fontsize=9, loc="upper left")
    apply_style(ax, "Hardware Tier Comparison Across All Metrics", ylabel="Score (1-5)")
    fig.tight_layout()
    return fig


def chart_model_comparison_by_metric(by_model):
    """Grouped bar chart: each model with bars for accuracy, safety, usefulness."""
    metrics = ["accuracy", "safety", "usefulness"]
    met_colors = ["#3498db", "#e74c3c", "#27ae60"]
    models = MODEL_ORDER
    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 5.5))
    for i, (met, col) in enumerate(zip(metrics, met_colors)):
        vals = [by_model.get(m, {}).get(met, 0) for m in models]
        ax.bar(x + i*width, vals, width, label=METRIC_LABELS[met], color=col, edgecolor="white")

    ax.set_xticks(x + width)
    ax.set_xticklabels([MODEL_SHORT[m] for m in models], fontsize=8)
    ax.set_ylim(0, 5.5)
    ax.legend(fontsize=9)

    # Tier background bands
    ax.axvspan(-0.5, 2.5, alpha=0.06, color=TIER_COLORS["small"])
    ax.axvspan(2.5, 6.5, alpha=0.06, color=TIER_COLORS["medium"])
    ax.axvspan(6.5, 10.5, alpha=0.06, color=TIER_COLORS["large_local"])
    ax.text(1, 5.2, "RPi5", ha="center", fontsize=9, color=TIER_COLORS["small"], fontweight="bold")
    ax.text(4.5, 5.2, "Jetson", ha="center", fontsize=9, color=TIER_COLORS["medium"], fontweight="bold")
    ax.text(8.5, 5.2, "GPU Server", ha="center", fontsize=9, color=TIER_COLORS["large_local"], fontweight="bold")

    apply_style(ax, "Model Comparison: Accuracy vs Safety vs Usefulness", ylabel="Score (1-5)")
    fig.tight_layout()
    return fig


def chart_model_language_heatmap(model_lang_scores):
    """Heatmap: model × language usefulness scores."""
    models = MODEL_ORDER
    langs = LANG_ORDER
    lang_labels = [LANG_NAMES[l] for l in langs]
    model_labels = [MODEL_SHORT[m].replace("\n", " ") for m in models]

    data = np.zeros((len(models), len(langs)))
    for i, m in enumerate(models):
        for j, l in enumerate(langs):
            scores = model_lang_scores.get(m, {}).get(l, {}).get("usefulness", [])
            data[i, j] = avg(scores) if scores else 0

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=1, vmax=5)

    ax.set_xticks(range(len(langs)))
    ax.set_xticklabels(lang_labels, fontsize=10, rotation=30, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(model_labels, fontsize=9)

    # Annotate cells
    for i in range(len(models)):
        for j in range(len(langs)):
            v = data[i, j]
            text_color = "white" if v < 2.5 else "black"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=9,
                    fontweight="bold", color=text_color)

    # Tier separators
    ax.axhline(y=2.5, color="white", linewidth=3)
    ax.axhline(y=6.5, color="white", linewidth=3)

    # Tier labels on right
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks([1, 4.5, 8.5])
    ax2.set_yticklabels(["RPi5", "Jetson", "GPU"], fontsize=10, fontweight="bold")
    ax2.tick_params(length=0)
    ax2.spines["right"].set_visible(False)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.12)
    cbar.set_label("Usefulness Score", fontsize=10)
    ax.set_title("Model x Language Usefulness Heatmap", fontsize=13,
                 fontweight="bold", color=DARK_BLUE, pad=12)
    fig.tight_layout()
    return fig


def chart_english_deep_dive(model_lang_scores):
    """Per-model English performance breakdown: accuracy + completeness + usefulness."""
    models = MODEL_ORDER
    metrics = ["accuracy", "completeness", "usefulness"]
    met_colors = ["#3498db", "#9b59b6", "#27ae60"]

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(models))
    width = 0.25
    for i, (met, col) in enumerate(zip(metrics, met_colors)):
        vals = []
        for m in models:
            scores = model_lang_scores.get(m, {}).get("en", {}).get(met, [])
            vals.append(avg(scores) if scores else 0)
        ax.bar(x + i*width, vals, width, label=METRIC_LABELS[met], color=col, edgecolor="white")

    ax.set_xticks(x + width)
    ax.set_xticklabels([MODEL_SHORT[m] for m in models], fontsize=8)
    ax.set_ylim(0, 5.5)
    ax.legend(fontsize=9)

    # Tier bands
    ax.axvspan(-0.5, 2.5, alpha=0.06, color=TIER_COLORS["small"])
    ax.axvspan(2.5, 6.5, alpha=0.06, color=TIER_COLORS["medium"])
    ax.axvspan(6.5, 10.5, alpha=0.06, color=TIER_COLORS["large_local"])

    apply_style(ax, "English Language Performance by Model", ylabel="Score (1-5)")
    fig.tight_layout()
    return fig


def chart_language_by_tier(by_tier_lang):
    """For each language, show tier performance side by side."""
    langs = LANG_ORDER
    lang_labels = [LANG_NAMES[l] for l in langs]
    x = np.arange(len(langs))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, tier in enumerate(TIER_ORDER):
        vals = [by_tier_lang[tier].get(l, 0) for l in langs]
        bars = ax.bar(x + i*width, vals, width, label=TIER_LABELS[tier],
                      color=TIER_COLORS[tier], edgecolor="white")
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f"{v:.1f}", ha="center", va="bottom", fontsize=7, fontweight="bold")

    ax.set_xticks(x + width)
    ax.set_xticklabels(lang_labels, fontsize=10)
    ax.set_ylim(0, 5.5)
    ax.legend(fontsize=9, loc="upper right")
    apply_style(ax, "Language Support by Hardware Tier (Usefulness)", ylabel="Score (1-5)")
    fig.tight_layout()
    return fig


def chart_size_vs_quality(by_model, time_by_model):
    """Scatter plot: model size (params) vs overall score, bubble size = response time."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for m in MODEL_ORDER:
        params = MODEL_PARAMS[m]
        score = by_model.get(m, {}).get("overall", 0)
        avg_time = avg(time_by_model.get(m, [1]))
        tier = MODEL_TIERS[m]
        size = max(60, avg_time * 8)  # scale bubble
        ax.scatter(params, score, s=size, c=TIER_COLORS[tier], alpha=0.8,
                   edgecolors="white", linewidths=1.5, zorder=5)
        # Label
        offset_y = 0.08
        if m == "phi4:14b":
            offset_y = -0.12
        ax.annotate(MODEL_SHORT[m].replace("\n", " "), (params, score),
                    textcoords="offset points", xytext=(8, 5 if offset_y > 0 else -15),
                    fontsize=8, color="#333")

    # Value-for-money zone
    ax.axhspan(3.5, 5, xmin=0, xmax=0.35, alpha=0.08, color="#27ae60")
    ax.text(3, 4.7, "Sweet spot\n(good quality,\nsmall model)", fontsize=8,
            color="#27ae60", ha="center", style="italic")

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}B" if x >= 1 else f"{x:.1f}B"))
    ax.set_xticks([0.8, 1, 2, 4, 8, 9, 12, 14, 24, 35])

    from matplotlib.patches import Patch
    legend_items = [Patch(facecolor=TIER_COLORS[t], label=TIER_LABELS[t]) for t in TIER_ORDER]
    ax.legend(handles=legend_items, loc="lower right", fontsize=9)

    apply_style(ax, "Model Size vs Quality (bubble = response time)", "Parameters", "Overall Score (1-5)")
    ax.set_ylim(2, 4.8)
    fig.tight_layout()
    return fig


def chart_category_by_tier(by_tier_cat):
    """Heatmap: category × tier with scores."""
    cats = CAT_ORDER
    cat_labels = [CAT_SHORT[c] for c in cats]
    tiers = TIER_ORDER
    tier_labels = [TIER_SHORT[t] for t in tiers]

    data = np.zeros((len(cats), len(tiers)))
    for i, c in enumerate(cats):
        for j, t in enumerate(tiers):
            data[i, j] = by_tier_cat[t].get(c, 0)

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=2, vmax=5)

    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels(tier_labels, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cat_labels, fontsize=10)

    for i in range(len(cats)):
        for j in range(len(tiers)):
            v = data[i, j]
            text_color = "white" if v < 3.0 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=11,
                    fontweight="bold", color=text_color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Overall Score", fontsize=10)
    ax.set_title("Category Performance by Hardware Tier", fontsize=13,
                 fontweight="bold", color=DARK_BLUE, pad=12)
    fig.tight_layout()
    return fig


def chart_safety_detail(results):
    """Per-model safety scores for guardrail + child safety categories."""
    models = MODEL_ORDER
    safety_guard = defaultdict(list)
    safety_child = defaultdict(list)

    for r in results:
        if r["category"] == "guardrails":
            safety_guard[r["model_name"]].append(r.get("scores", {}).get("safety", 0))
        elif r["category"] == "child_safety":
            safety_child[r["model_name"]].append(r.get("scores", {}).get("safety", 0))

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(models))
    width = 0.35

    vals_g = [avg(safety_guard.get(m, [0])) for m in models]
    vals_c = [avg(safety_child.get(m, [0])) for m in models]
    bars1 = ax.bar(x - width/2, vals_g, width, label="Guardrails (D)", color="#e74c3c", edgecolor="white")
    bars2 = ax.bar(x + width/2, vals_c, width, label="Child Safety (G)", color="#e67e22", edgecolor="white")

    for bar, v in zip(list(bars1) + list(bars2), vals_g + vals_c):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f"{v:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_SHORT[m] for m in models], fontsize=8)
    ax.set_ylim(0, 5.5)
    ax.axhline(y=4.0, color="#27ae60", linestyle="--", alpha=0.5, linewidth=1.5)
    ax.text(10.5, 4.1, "Target: 4.0", fontsize=8, color="#27ae60", ha="right")
    ax.legend(fontsize=9)

    # Tier bands
    ax.axvspan(-0.5, 2.5, alpha=0.06, color=TIER_COLORS["small"])
    ax.axvspan(2.5, 6.5, alpha=0.06, color=TIER_COLORS["medium"])
    ax.axvspan(6.5, 10.5, alpha=0.06, color=TIER_COLORS["large_local"])

    apply_style(ax, "Safety Scores: Guardrails & Child Safety by Model", ylabel="Safety Score (1-5)")
    fig.tight_layout()
    return fig


def chart_radar_per_tier(by_model):
    """Three radar charts, one per tier, comparing models within that tier."""
    tier_models = {
        "small": ["qwen3.5:0.8b", "qwen3.5:2b", "llama3.2:1b"],
        "medium": ["qwen3.5:4b", "qwen3.5:9b", "llama3.1:8b", "mistral-nemo:12b"],
        "large_local": ["qwen3.5:35b-a3b", "deepseek-r1:14b", "phi4:14b", "mistral-small3.2:24b"],
    }
    metrics = ["accuracy", "language_quality", "safety", "completeness", "usefulness"]
    metric_labels = ["Accuracy", "Language", "Safety", "Complete", "Useful"]
    n = len(metrics)
    angles = [i / n * 2 * math.pi for i in range(n)]
    angles += angles[:1]  # close

    model_colors = [
        "#3498db", "#e74c3c", "#27ae60", "#9b59b6",
        "#f39c12", "#1abc9c", "#e67e22", "#2980b9"
    ]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5), subplot_kw=dict(projection="polar"))
    for idx, tier in enumerate(TIER_ORDER):
        ax = axes[idx]
        models = tier_models[tier]
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=8)
        ax.set_ylim(0, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=7)
        ax.set_title(TIER_SHORT[tier], fontsize=12, fontweight="bold",
                     color=TIER_COLORS[tier], pad=15)

        for i, m in enumerate(models):
            vals = [by_model.get(m, {}).get(met, 0) for met in metrics]
            vals += vals[:1]
            ax.plot(angles, vals, "o-", linewidth=1.5, label=MODEL_SHORT[m].replace("\n", " "),
                    color=model_colors[i % len(model_colors)], markersize=4)
            ax.fill(angles, vals, alpha=0.08, color=model_colors[i % len(model_colors)])

        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15), fontsize=7)

    fig.suptitle("Metric Radar: Models Within Each Hardware Tier", fontsize=13,
                 fontweight="bold", color=DARK_BLUE, y=1.02)
    fig.tight_layout()
    return fig


def chart_response_time(time_by_model):
    """Bar chart: avg response time per model, color by tier."""
    models = MODEL_ORDER
    avg_times = [avg(time_by_model.get(m, [0])) for m in models]
    bar_colors = [TIER_COLORS[MODEL_TIERS[m]] for m in models]

    fig, ax = plt.subplots(figsize=(11, 4.5))
    bars = ax.bar(range(len(models)), avg_times, color=bar_colors, edgecolor="white")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels([MODEL_SHORT[m] for m in models], fontsize=8)
    for bar, v in zip(bars, avg_times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{v:.0f}s", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.axvspan(-0.5, 2.5, alpha=0.06, color=TIER_COLORS["small"])
    ax.axvspan(2.5, 6.5, alpha=0.06, color=TIER_COLORS["medium"])
    ax.axvspan(6.5, 10.5, alpha=0.06, color=TIER_COLORS["large_local"])

    apply_style(ax, "Average Response Time by Model (on RTX 5090)", ylabel="Seconds")
    fig.tight_layout()
    return fig


def chart_model_category_heatmap(results):
    """Heatmap: model × category overall scores."""
    models = MODEL_ORDER
    cats = CAT_ORDER
    model_cat = defaultdict(lambda: defaultdict(list))
    for r in results:
        scores = r.get("scores", {})
        # compute overall as mean of available metrics
        vals = [v for v in scores.values()]
        if vals:
            model_cat[r["model_name"]][r["category"]].append(sum(vals)/len(vals))

    data = np.zeros((len(models), len(cats)))
    for i, m in enumerate(models):
        for j, c in enumerate(cats):
            data[i, j] = avg(model_cat[m][c]) if model_cat[m][c] else 0

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=2, vmax=5)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([CAT_SHORT[c] for c in cats], fontsize=9, rotation=30, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([MODEL_SHORT[m].replace("\n", " ") for m in models], fontsize=9)

    for i in range(len(models)):
        for j in range(len(cats)):
            v = data[i, j]
            text_color = "white" if v < 3.0 else "black"
            ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=9,
                    fontweight="bold", color=text_color)

    ax.axhline(y=2.5, color="white", linewidth=3)
    ax.axhline(y=6.5, color="white", linewidth=3)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Avg Score", fontsize=10)
    ax.set_title("Model x Category Performance Heatmap", fontsize=13,
                 fontweight="bold", color=DARK_BLUE, pad=12)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════
# PDF helpers
# ═══════════════════════════════════════════════════════════════

RL_DARK_BLUE = colors.HexColor(DARK_BLUE)
RL_GREEN = colors.HexColor(GREEN)
RL_LIGHT_BG = colors.HexColor(LIGHT_BG)


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Title2", parent=styles["Title"],
        fontSize=22, textColor=RL_DARK_BLUE, spaceAfter=4*mm))
    styles.add(ParagraphStyle("Subtitle", parent=styles["Normal"],
        fontSize=12, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=8*mm))
    styles.add(ParagraphStyle("SectionHead", parent=styles["Heading1"],
        fontSize=16, textColor=RL_DARK_BLUE, spaceBefore=8*mm, spaceAfter=4*mm))
    styles.add(ParagraphStyle("SubHead", parent=styles["Heading2"],
        fontSize=13, textColor=RL_DARK_BLUE, spaceBefore=6*mm, spaceAfter=3*mm))
    styles.add(ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=3*mm))
    styles.add(ParagraphStyle("Small", parent=styles["Normal"],
        fontSize=8, leading=10, textColor=colors.grey))
    styles.add(ParagraphStyle("Finding", parent=styles["Normal"],
        fontSize=10, leading=14, spaceAfter=2*mm, leftIndent=10*mm,
        bulletIndent=5*mm, bulletFontName="Helvetica-Bold"))
    return styles


def make_table(data, col_widths=None):
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), RL_DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), RL_LIGHT_BG))
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style_cmds))
    return t


# ═══════════════════════════════════════════════════════════════
# Main report builder
# ═══════════════════════════════════════════════════════════════

def generate_report():
    results = json.loads((RESULTS_DIR / "test_results_v2.json").read_text())
    summary = json.loads((RESULTS_DIR / "test_summary_v2.json").read_text())
    styles = make_styles()

    # ── Aggregate additional data ──
    model_lang_scores = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    time_by_model = defaultdict(list)
    empty_by_model = defaultdict(int)
    total_by_model = defaultdict(int)

    for r in results:
        tier = r["model_tier"]
        lang = r["language"]
        model = r["model_name"]
        total_by_model[model] += 1

        if len(r.get("response", "")) < 5:
            empty_by_model[model] += 1

        if r.get("elapsed_seconds", 0) > 0:
            time_by_model[model].append(r["elapsed_seconds"])

        for metric, score in r.get("scores", {}).items():
            model_lang_scores[model][lang][metric].append(score)

    # Compute tier × language averages
    tier_lang_avg = {}
    for tier in TIER_ORDER:
        tier_lang_avg[tier] = {}
        for lang in LANG_ORDER:
            vals = []
            for m in MODEL_ORDER:
                if MODEL_TIERS[m] == tier:
                    s = model_lang_scores[m][lang].get("usefulness", [])
                    vals.extend(s)
            tier_lang_avg[tier][lang] = avg(vals)

    # Compute tier × category averages
    tier_cat_avg = {}
    for tier in TIER_ORDER:
        tier_cat_avg[tier] = {}
        for cat in CAT_ORDER:
            vals = []
            for r2 in results:
                if MODEL_TIERS.get(r2["model_name"]) == tier and r2["category"] == cat:
                    s = r2.get("scores", {})
                    if s:
                        vals.append(sum(s.values()) / len(s))
            tier_cat_avg[tier][cat] = avg(vals)

    by_model = summary["by_model"]
    by_tier = summary["by_tier"]

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        str(REPORT_FILE), pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    story = []

    # ═══════════════════════════════════════════
    # TITLE PAGE
    # ═══════════════════════════════════════════
    story.append(Spacer(1, 25*mm))
    story.append(Paragraph("Angels Academy AI", styles["Title2"]))
    story.append(Paragraph("Model &amp; Hardware Selection Report", styles["Title2"]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="80%", thickness=2, color=RL_GREEN))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>"
        f"1,727 test cases &middot; 11 models &middot; 7 languages &middot; 36 scenarios &middot; 8 categories<br/>"
        f"Hardware tiers tested: Raspberry Pi 5, Jetson Orin Nano, GPU Server (RTX 5090)",
        styles["Subtitle"]
    ))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "This report uses visual comparisons to help the Angels for Education editorial team "
        "choose the right hardware + model combination for each deployment region. "
        "Models are color-coded by target hardware: "
        "<font color='#e74c3c'><b>Red = Raspberry Pi 5</b></font> (Small, 0.8-2B), "
        "<font color='#f39c12'><b>Amber = Jetson Orin Nano</b></font> (Medium, 4-12B), "
        "<font color='#27ae60'><b>Green = GPU Server</b></font> (Large, 14-35B).",
        styles["Body"]
    ))

    # Quick recommendation table
    story.append(Spacer(1, 6*mm))
    rec_data = [
        ["Region", "Hardware", "Recommended Model", "Score", "Notes"],
        ["Chad (French)", "Jetson", "qwen3.5:9b", "4.13", "Best price/quality, strong French"],
        ["Chad (Arabic)", "Jetson", "qwen3.5:9b", "4.13", "Acceptable Arabic (3.5)"],
        ["Myanmar", "GPU / Cloud", "qwen3.5:35b-a3b", "4.22", "Burmese needs large model"],
        ["Thailand", "Jetson", "qwen3.5:9b", "4.13", "Thai acceptable at 9B"],
        ["Brazil", "Jetson", "qwen3.5:4b", "3.99", "Portuguese good at 4B+"],
        ["Offline basic", "RPi5", "llama3.2:1b", "3.79", "English/French only, limited"],
    ]
    story.append(make_table(rec_data, col_widths=[28*mm, 22*mm, 35*mm, 18*mm, 55*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "<i>Detailed visual analysis follows in the charts below.</i>", styles["Small"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 1: OVERALL MODEL RANKING
    # ═══════════════════════════════════════════
    story.append(Paragraph("1. Overall Model Ranking", styles["SectionHead"]))
    story.append(Paragraph(
        "All 11 models ranked by overall score. The dashed line marks the 3.5 'good' threshold. "
        "Models above this line are recommended for production use.",
        styles["Body"]))
    story.append(fig_to_image(chart_model_ranking(by_model), width_mm=170))
    story.append(Paragraph(
        "<b>Key takeaway:</b> <font color='#27ae60'>qwen3.5:35b-a3b</font> leads at 4.22, but "
        "<font color='#f39c12'>qwen3.5:9b</font> (4.13) runs on much cheaper Jetson hardware. "
        "The gap between medium and large tier is only 0.07, making Jetson the best value.",
        styles["Body"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 2: TIER METRICS COMPARISON
    # ═══════════════════════════════════════════
    story.append(Paragraph("2. Hardware Tier Comparison", styles["SectionHead"]))
    story.append(Paragraph(
        "How the three hardware tiers compare across 5 key metrics. "
        "Safety is consistent across tiers; the big gap is in accuracy and completeness.",
        styles["Body"]))
    story.append(fig_to_image(chart_tier_metrics(by_tier), width_mm=170))

    story.append(Spacer(1, 5*mm))

    # ═══════════════════════════════════════════
    # CHART 3: ACCURACY vs SAFETY vs USEFULNESS
    # ═══════════════════════════════════════════
    story.append(Paragraph("3. Per-Model: Accuracy vs Safety vs Usefulness", styles["SectionHead"]))
    story.append(Paragraph(
        "Three critical metrics per model. Background bands show hardware tier. "
        "Note: accuracy uses keyword matching which penalizes non-English responses.",
        styles["Body"]))
    story.append(fig_to_image(chart_model_comparison_by_metric(by_model), width_mm=170))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 4: RADAR CHARTS PER TIER
    # ═══════════════════════════════════════════
    story.append(Paragraph("4. Metric Profiles Within Each Tier", styles["SectionHead"]))
    story.append(Paragraph(
        "Radar charts showing how models within the same hardware tier compare. "
        "A larger polygon means better overall performance.",
        styles["Body"]))
    story.append(fig_to_image(chart_radar_per_tier(by_model), width_mm=175))
    story.append(Paragraph(
        "<b>RPi5:</b> llama3.2:1b dominates &mdash; Qwen 0.8b/2b are too small. "
        "<b>Jetson:</b> qwen3.5:9b has the largest polygon. "
        "<b>GPU:</b> qwen3.5:35b-a3b leads across all axes.",
        styles["Body"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 5: MODEL × LANGUAGE HEATMAP
    # ═══════════════════════════════════════════
    story.append(Paragraph("5. Model x Language Heatmap (Usefulness)", styles["SectionHead"]))
    story.append(Paragraph(
        "Which model works best for which language? Green = good, red = poor. "
        "This helps decide deployment per country.",
        styles["Body"]))
    story.append(fig_to_image(chart_model_language_heatmap(model_lang_scores), width_mm=155))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 6: ENGLISH DEEP DIVE
    # ═══════════════════════════════════════════
    story.append(Paragraph("6. English Language Deep Dive", styles["SectionHead"]))
    story.append(Paragraph(
        "Since English is the primary teaching language, here is a detailed breakdown "
        "of accuracy, completeness, and usefulness for English queries per model.",
        styles["Body"]))
    story.append(fig_to_image(chart_english_deep_dive(model_lang_scores), width_mm=170))

    story.append(Spacer(1, 5*mm))

    # ═══════════════════════════════════════════
    # CHART 7: LANGUAGE BY TIER
    # ═══════════════════════════════════════════
    story.append(Paragraph("7. Language Support by Hardware Tier", styles["SectionHead"]))
    story.append(Paragraph(
        "For each deployment language, how well does each hardware tier perform? "
        "Burmese and Thai need medium+ hardware.",
        styles["Body"]))
    story.append(fig_to_image(chart_language_by_tier(tier_lang_avg), width_mm=170))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 8: SIZE vs QUALITY SCATTER
    # ═══════════════════════════════════════════
    story.append(Paragraph("8. Model Size vs Quality (Cost-Benefit)", styles["SectionHead"]))
    story.append(Paragraph(
        "Scatter plot showing the relationship between model size (parameters) and quality. "
        "Bubble size indicates response time. The 'sweet spot' area highlights models that "
        "deliver good quality at a smaller size &mdash; cheaper to deploy.",
        styles["Body"]))
    story.append(fig_to_image(chart_size_vs_quality(by_model, time_by_model), width_mm=165))
    story.append(Paragraph(
        "<b>Key insight:</b> qwen3.5:9b (9B parameters) achieves 95% of the quality "
        "of the 35B model at a fraction of the cost. qwen3.5:4b is also excellent value.",
        styles["Body"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 9: CATEGORY × TIER HEATMAP
    # ═══════════════════════════════════════════
    story.append(Paragraph("9. Category Performance by Hardware Tier", styles["SectionHead"]))
    story.append(Paragraph(
        "Which tasks can each hardware tier handle? Darker green = better. "
        "Guardrails and Child Safety are weak across all tiers.",
        styles["Body"]))
    story.append(fig_to_image(chart_category_by_tier(tier_cat_avg), width_mm=110))

    story.append(Spacer(1, 5*mm))

    # ═══════════════════════════════════════════
    # CHART 10: SAFETY DETAIL
    # ═══════════════════════════════════════════
    story.append(Paragraph("10. Safety Analysis: Guardrails &amp; Child Safety", styles["SectionHead"]))
    story.append(Paragraph(
        "Critical for deployment with children. Target is 4.0+. Most models fall short &mdash; "
        "system prompt hardening is needed before production.",
        styles["Body"]))
    story.append(fig_to_image(chart_safety_detail(results), width_mm=170))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 11: MODEL × CATEGORY HEATMAP
    # ═══════════════════════════════════════════
    story.append(Paragraph("11. Full Model x Category Heatmap", styles["SectionHead"]))
    story.append(Paragraph(
        "Complete view of every model's performance across every task category. "
        "Use this to identify specific strengths and weaknesses.",
        styles["Body"]))
    story.append(fig_to_image(chart_model_category_heatmap(results), width_mm=165))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # CHART 12: RESPONSE TIME
    # ═══════════════════════════════════════════
    story.append(Paragraph("12. Response Time by Model", styles["SectionHead"]))
    story.append(Paragraph(
        "Average response time on the RTX 5090 test server. Actual times on target hardware "
        "(RPi5, Jetson) will be significantly slower. Use this for relative comparisons.",
        styles["Body"]))
    story.append(fig_to_image(chart_response_time(time_by_model), width_mm=170))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # DETAILED SCORES TABLES
    # ═══════════════════════════════════════════
    story.append(Paragraph("13. Detailed Scores Table", styles["SectionHead"]))

    headers = ["Model", "Tier", "Accur.", "Lang Q", "Safety", "Compl.", "Useful", "Overall", "Empty"]
    data = [headers]
    for model in MODEL_ORDER:
        m = by_model.get(model, {})
        data.append([
            model,
            TIER_SHORT.get(MODEL_TIERS.get(model, ""), ""),
            f"{m.get('accuracy', 0):.2f}",
            f"{m.get('language_quality', 0):.2f}",
            f"{m.get('safety', 0):.2f}",
            f"{m.get('completeness', 0):.2f}",
            f"{m.get('usefulness', 0):.2f}",
            f"{m.get('overall', 0):.2f}",
            f"{empty_by_model.get(model, 0)}/{total_by_model.get(model, 0)}",
        ])

    story.append(make_table(data, col_widths=[33*mm, 16*mm, 17*mm, 17*mm, 17*mm, 17*mm, 17*mm, 18*mm, 18*mm]))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("13.1 Scores by Language", styles["SubHead"]))

    headers = ["Language", "Accuracy", "Lang Quality", "Safety", "Completeness", "Usefulness"]
    data = [headers]
    for lang in LANG_ORDER:
        name = LANG_NAMES[lang]
        m = summary["by_language"].get(name, {})
        data.append([
            name,
            f"{m.get('accuracy', 0):.2f}",
            f"{m.get('language_quality', 0):.2f}",
            f"{m.get('safety', 0):.2f}",
            f"{m.get('completeness', 0):.2f}",
            f"{m.get('usefulness', 0):.2f}",
        ])
    story.append(make_table(data, col_widths=[30*mm, 27*mm, 27*mm, 27*mm, 27*mm, 27*mm]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # RECOMMENDATIONS
    # ═══════════════════════════════════════════
    story.append(Paragraph("14. Final Recommendations", styles["SectionHead"]))

    story.append(Paragraph("<b>Best Model Per Hardware:</b>", styles["Body"]))
    hw_recs = [
        f"<b>Raspberry Pi 5</b> (offline, budget): <b>llama3.2:1b</b> (3.79) &mdash; usable for English/French vocabulary help. "
        f"Not recommended for Arabic, Burmese, or Thai. Qwen 3.5 0.8b/2b produce too many empty responses ({empty_by_model.get('qwen3.5:0.8b', 0)} and {empty_by_model.get('qwen3.5:2b', 0)} empties respectively).",

        f"<b>Jetson Orin Nano</b> (best value): <b>qwen3.5:9b</b> (4.13) &mdash; strong across all Latin-script languages, "
        f"acceptable for Arabic and Thai. Best cost-to-quality ratio in the entire lineup.",

        f"<b>GPU Server / Cloud</b> (maximum quality): <b>qwen3.5:35b-a3b</b> (4.22) &mdash; best accuracy (3.03), "
        f"best completeness (4.83), best language quality (4.46). Required for Burmese deployment.",
    ]
    for r in hw_recs:
        story.append(Paragraph(f"&bull; {r}", styles["Finding"]))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("<b>Critical Issues to Address:</b>", styles["Body"]))
    issues = [
        "<b>Guardrail safety (3.09/5.0)</b> &mdash; Models still respond to ~40% of out-of-scope requests. "
        "Needs system prompt hardening before classroom deployment.",
        "<b>Child safety (3.18/5.0)</b> &mdash; Must add content filtering for age-inappropriate requests.",
        f"<b>Empty responses</b> &mdash; qwen3.5:0.8b produces {empty_by_model.get('qwen3.5:0.8b', 0)} empty responses "
        f"out of {total_by_model.get('qwen3.5:0.8b', 0)} tests. Consider removing from RPi5 tier.",
        "<b>Burmese language (3.34/5.0)</b> &mdash; All local models struggle. Cloud APIs (GPT-4, Claude) recommended.",
    ]
    for item in issues:
        story.append(Paragraph(f"&bull; {item}", styles["Finding"]))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("<b>Deployment Strategy:</b>", styles["Body"]))
    strategy = [
        "<b>Phase 1 (immediate):</b> Deploy qwen3.5:9b on Jetson for Chad and Thailand. "
        "Harden system prompt guardrails.",
        "<b>Phase 2:</b> Add qwen3.5:35b-a3b as cloud-hosted option for Myanmar. "
        "Test with real teachers for qualitative feedback.",
        "<b>Phase 3:</b> Evaluate cloud APIs (Anthropic, OpenAI) for Burmese and advanced use cases. "
        "Consider RPi5 + llama3.2:1b as offline fallback only.",
    ]
    for item in strategy:
        story.append(Paragraph(f"&bull; {item}", styles["Finding"]))

    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("&mdash;" * 35, styles["Small"]))
    story.append(Paragraph(
        f"Angels Academy AI &middot; Model &amp; Hardware Selection Report v2 &middot; {datetime.now().strftime('%B %Y')}<br/>"
        "Angels for Education Foundation &middot; https://angelsforglobaleducation.org",
        styles["Small"]
    ))

    # ── Build PDF ──
    doc.build(story)
    print(f"Report generated: {REPORT_FILE}")
    print(f"File size: {REPORT_FILE.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    generate_report()

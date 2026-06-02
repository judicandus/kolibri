#!/usr/bin/env python3
"""
Angels Academy AI — Full Response Catalog
Generates a PDF with all 620 test responses organized by quality category.
Uses WeasyPrint for proper Unicode (Arabic, Burmese, Thai) rendering.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_FILE = RESULTS_DIR / "test_results.json"
OUTPUT_FILE = RESULTS_DIR / "angels_academy_full_response_catalog.pdf"

LANG_NAMES = {
    "en": "English", "fr": "French", "ar": "Arabic",
    "my": "Burmese", "th": "Thai", "pt": "Portuguese", "es": "Spanish"
}
TIER_LABELS = {
    "small": "Small (1.5B)", "medium": "Medium (7-8B)",
    "large_local": "Large (35B)", "cloud": "Cloud API"
}
CAT_LABELS = {
    "vocabulary": "Vocabulary Help", "lesson_prep": "Lesson Preparation",
    "theological": "Theological Support", "guardrails": "Guardrails / Safety",
    "multilingual": "Multilingual Capability"
}

# ── Quality category definitions ──
CATEGORIES = [
    {
        "id": "excellent",
        "title": "Excellent Responses",
        "color": "#2e7d32",
        "bg": "#e8f5e9",
        "icon": "★",
        "description": "High-quality responses (avg score ≥ 4.0). These demonstrate the models at their best — accurate, complete, in the right language, with good RAG grounding.",
        "filter": lambda r, avg_score, resp_len: resp_len >= 5 and not (r["category"] == "guardrails" and r["scores"].get("safety", 5) <= 2) and avg_score >= 4.0,
    },
    {
        "id": "good",
        "title": "Good Responses",
        "color": "#1565c0",
        "bg": "#e3f2fd",
        "icon": "●",
        "description": "Acceptable responses (avg score 3.5–3.99). Generally useful but with minor issues — slightly off-topic details, incomplete coverage, or minor language imperfections.",
        "filter": lambda r, avg_score, resp_len: resp_len >= 5 and not (r["category"] == "guardrails" and r["scores"].get("safety", 5) <= 2) and 3.5 <= avg_score < 4.0,
    },
    {
        "id": "fair",
        "title": "Fair Responses — Review Recommended",
        "color": "#f57f17",
        "bg": "#fff8e1",
        "icon": "◐",
        "description": "Mediocre responses (avg score 2.5–3.49). These may be partially useful but have notable issues — wrong language mix, shallow content, missing key concepts, or poor RAG utilization. Editorial review recommended.",
        "filter": lambda r, avg_score, resp_len: resp_len >= 5 and not (r["category"] == "guardrails" and r["scores"].get("safety", 5) <= 2) and 2.5 <= avg_score < 3.5,
    },
    {
        "id": "guardrail_failures",
        "title": "Guardrail Failures — Action Required",
        "color": "#b71c1c",
        "bg": "#ffebee",
        "icon": "⚠",
        "description": "Responses to out-of-scope queries where the model FAILED to decline (safety score ≤ 2). These are critical issues — the model answered questions it should have refused (e.g., other religions, politics, personal requests). System prompt hardening is required.",
        "filter": lambda r, avg_score, resp_len: resp_len >= 5 and r["category"] == "guardrails" and r["scores"].get("safety", 5) <= 2,
    },
    {
        "id": "poor",
        "title": "Poor Responses — Problematic",
        "color": "#e65100",
        "bg": "#fff3e0",
        "icon": "✗",
        "description": "Low-quality responses (avg score 1.5–2.49). Significant issues — wrong language, garbled output, factually incorrect, or fundamentally unhelpful. These represent model limitations at this tier/language combination.",
        "filter": lambda r, avg_score, resp_len: resp_len >= 5 and not (r["category"] == "guardrails" and r["scores"].get("safety", 5) <= 2) and 1.5 <= avg_score < 2.5,
    },
    {
        "id": "empty",
        "title": "Empty / Failed Responses",
        "color": "#37474f",
        "bg": "#eceff1",
        "icon": "∅",
        "description": "The model returned an empty or near-empty response (fewer than 5 characters). This indicates a generation failure, likely due to model sampling issues or prompt incompatibility.",
        "filter": lambda r, avg_score, resp_len: resp_len < 5,
    },
]


def score_badge(value, metric=""):
    """Return colored HTML badge for a score."""
    if value >= 4:
        color, bg = "#2e7d32", "#e8f5e9"
    elif value >= 3:
        color, bg = "#f57f17", "#fff8e1"
    elif value >= 2:
        color, bg = "#e65100", "#fff3e0"
    else:
        color, bg = "#c62828", "#ffebee"
    return f'<span class="badge" style="background:{bg};color:{color}">{value}</span>'


def render_entry(r, index):
    """Render a single test result as an HTML card."""
    scores = r.get("scores", {})
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    resp = r.get("response", "")
    resp_escaped = html.escape(resp) if resp else "<em>(empty response)</em>"
    prompt_escaped = html.escape(r.get("prompt", ""))

    # RAG sources
    rag_html = ""
    rag_sources = r.get("rag_sources", [])
    if rag_sources:
        rag_items = []
        for s in rag_sources[:3]:
            src = html.escape(s.get("source", "Unknown"))
            sc = s.get("score", 0)
            rag_items.append(f'<span class="rag-source">{src} ({sc:.2f})</span>')
        rag_html = f'<div class="rag-line">RAG Sources: {" · ".join(rag_items)}</div>'

    elapsed = r.get("elapsed_seconds", 0)
    time_str = f"{elapsed:.1f}s" if elapsed else "—"

    score_cells = ""
    for metric in ["accuracy", "language_quality", "safety", "completeness", "usefulness"]:
        v = scores.get(metric, 0)
        label = metric.replace("_", " ").title()
        score_cells += f'<td>{score_badge(v)} {label}</td>'

    return f'''
    <div class="entry">
        <div class="entry-header">
            <span class="entry-id">#{index}</span>
            <span class="scenario-id">{r["scenario_id"]}</span>
            <span class="entry-desc">{html.escape(r.get("description", ""))}</span>
            <span class="entry-meta">
                <span class="lang-badge">{LANG_NAMES.get(r["language"], r["language"])}</span>
                <span class="tier-badge">{TIER_LABELS.get(r["model_tier"], r["model_tier"])}</span>
                <span class="model-badge">{r["model_name"]}</span>
                <span class="time-badge">{time_str}</span>
                <span class="avg-badge">avg: {avg_score:.1f}</span>
            </span>
        </div>
        <div class="scores-row">
            <table class="scores-table"><tr>{score_cells}</tr></table>
        </div>
        <div class="prompt-box">
            <strong>Prompt:</strong> {prompt_escaped}
        </div>
        <div class="response-box">
            <strong>Response:</strong><br>{resp_escaped}
        </div>
        {rag_html}
    </div>
    '''


def generate_catalog():
    results = json.loads(RESULTS_FILE.read_text())
    print(f"Loaded {len(results)} results")

    # Pre-compute avg scores
    entries_with_scores = []
    for r in results:
        s = r.get("scores", {})
        avg_score = sum(s.values()) / len(s) if s else 0
        resp_len = len(r.get("response", ""))
        entries_with_scores.append((r, avg_score, resp_len))

    # Categorize
    categorized = {cat["id"]: [] for cat in CATEGORIES}
    for r, avg_score, resp_len in entries_with_scores:
        for cat in CATEGORIES:
            if cat["filter"](r, avg_score, resp_len):
                categorized[cat["id"]].append((r, avg_score))
                break

    # Sort within each category: by scenario_id, then language, then model
    for cat_id in categorized:
        categorized[cat_id].sort(key=lambda x: (
            x[0]["scenario_id"], x[0]["language"], x[0]["model_name"]
        ))

    # Count summary
    for cat in CATEGORIES:
        n = len(categorized[cat["id"]])
        print(f"  {cat['title']}: {n}")

    # ── Build HTML ──
    html_parts = []

    # CSS
    html_parts.append(f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 12mm 10mm 12mm 10mm;
    @bottom-center {{
        content: "Angels Academy AI — Full Response Catalog — Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #888;
    }}
}}
body {{
    font-family: 'Noto Sans', 'DejaVu Sans', 'Arial Unicode MS', sans-serif;
    font-size: 9pt;
    line-height: 1.35;
    color: #222;
}}
h1 {{
    color: #213953;
    font-size: 20pt;
    margin-bottom: 4mm;
    page-break-after: avoid;
}}
h2 {{
    font-size: 10pt;
    color: #555;
    margin-top: 0;
    margin-bottom: 6mm;
    font-weight: normal;
}}
.cat-header {{
    page-break-before: always;
    margin-bottom: 3mm;
}}
.cat-header h1 {{
    font-size: 16pt;
    margin-bottom: 2mm;
    padding: 3mm 4mm;
    border-radius: 3px;
}}
.cat-desc {{
    font-size: 9pt;
    color: #444;
    margin-bottom: 4mm;
    padding: 2mm 4mm;
    background: #f5f5f5;
    border-left: 3px solid #ccc;
}}
.cat-count {{
    font-size: 9pt;
    font-weight: bold;
    color: #666;
    margin-bottom: 3mm;
}}
.entry {{
    border: 0.5pt solid #ddd;
    border-radius: 3px;
    margin-bottom: 3mm;
    padding: 2.5mm 3mm;
    page-break-inside: avoid;
    background: #fff;
}}
.entry-header {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 2mm;
    margin-bottom: 1.5mm;
    font-size: 8.5pt;
}}
.entry-id {{
    font-weight: bold;
    color: #888;
    font-size: 8pt;
}}
.scenario-id {{
    font-weight: bold;
    color: #213953;
    font-size: 9pt;
}}
.entry-desc {{
    color: #555;
    font-style: italic;
    font-size: 8pt;
}}
.entry-meta {{
    margin-left: auto;
}}
.lang-badge, .tier-badge, .model-badge, .time-badge, .avg-badge {{
    display: inline-block;
    padding: 0.5mm 2mm;
    border-radius: 2px;
    font-size: 7.5pt;
    font-weight: bold;
    margin-left: 1mm;
}}
.lang-badge {{ background: #e3f2fd; color: #1565c0; }}
.tier-badge {{ background: #f3e5f5; color: #6a1b9a; }}
.model-badge {{ background: #e8eaf6; color: #283593; }}
.time-badge {{ background: #fff8e1; color: #f57f17; }}
.avg-badge {{ background: #e8f5e9; color: #2e7d32; }}
.scores-row {{
    margin-bottom: 1.5mm;
}}
.scores-table {{
    border-collapse: collapse;
    font-size: 7.5pt;
}}
.scores-table td {{
    padding: 0.5mm 2mm;
    white-space: nowrap;
}}
.badge {{
    display: inline-block;
    padding: 0 1.5mm;
    border-radius: 2px;
    font-weight: bold;
    font-size: 8pt;
    min-width: 4mm;
    text-align: center;
}}
.prompt-box {{
    background: #f8f9fa;
    padding: 1.5mm 3mm;
    margin-bottom: 1.5mm;
    border-left: 2.5px solid #213953;
    font-size: 8.5pt;
}}
.response-box {{
    padding: 1.5mm 3mm;
    margin-bottom: 1mm;
    border-left: 2.5px solid #a6c52e;
    font-size: 8.5pt;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: none;
}}
.rag-line {{
    font-size: 7pt;
    color: #888;
    padding: 0.5mm 3mm;
}}
.rag-source {{
    background: #f5f5f5;
    padding: 0 1.5mm;
    border-radius: 1px;
}}
.toc {{
    margin: 5mm 0;
}}
.toc-item {{
    padding: 2mm 0;
    border-bottom: 0.5pt dotted #ccc;
}}
.toc-item a {{
    color: #213953;
    text-decoration: none;
    font-weight: bold;
}}
.toc-count {{
    float: right;
    color: #888;
    font-weight: normal;
}}
hr {{
    border: none;
    border-top: 2px solid #a6c52e;
    margin: 4mm 0;
}}
.summary-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0;
    font-size: 8.5pt;
}}
.summary-table th {{
    background: #213953;
    color: white;
    padding: 2mm 3mm;
    text-align: left;
    font-size: 8pt;
}}
.summary-table td {{
    padding: 1.5mm 3mm;
    border-bottom: 0.5pt solid #ddd;
}}
.summary-table tr:nth-child(even) {{
    background: #f8f9fa;
}}
</style>
</head>
<body>
''')

    # ── Title page ──
    html_parts.append(f'''
    <div style="text-align:center; padding-top: 40mm;">
        <h1 style="font-size: 24pt;">Angels Academy AI</h1>
        <h1 style="font-size: 18pt; color: #555;">Full Response Catalog</h1>
        <hr>
        <h2 style="font-size: 11pt; margin-top: 5mm;">
            {len(results)} Test Responses · {len(set(r["model_name"] for r in results))} Models · {len(set(r["language"] for r in results))} Languages · 24 Scenarios
        </h2>
        <p style="color:#888; font-size:9pt;">Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
        <p style="color:#888; font-size:9pt;">For editorial team review</p>
    </div>
    ''')

    # ── Table of contents ──
    html_parts.append('<div class="cat-header"><h1>Table of Contents</h1></div>')
    html_parts.append('<div class="toc">')
    for cat in CATEGORIES:
        n = len(categorized[cat["id"]])
        html_parts.append(f'''
        <div class="toc-item">
            <a href="#{cat['id']}">{cat['icon']} {cat['title']}</a>
            <span class="toc-count">{n} responses</span>
        </div>
        ''')
    html_parts.append('</div>')

    # ── Quick reference: score distribution ──
    html_parts.append('''
    <div style="margin-top: 5mm;">
        <strong>Score Scale:</strong>
        <span class="badge" style="background:#e8f5e9;color:#2e7d32">4-5 Good</span>
        <span class="badge" style="background:#fff8e1;color:#f57f17">3 Fair</span>
        <span class="badge" style="background:#fff3e0;color:#e65100">2 Poor</span>
        <span class="badge" style="background:#ffebee;color:#c62828">1 Fail</span>
    </div>
    <div style="margin-top: 3mm;">
        <strong>Scoring metrics:</strong> Accuracy (concept matching) · Language Quality (correct script/language) ·
        Safety (guardrail compliance) · Completeness (depth) · Usefulness (composite)
    </div>
    ''')

    # ── Category summary table ──
    html_parts.append('''
    <table class="summary-table" style="margin-top:5mm;">
        <tr><th>Category</th><th>Count</th><th>Description</th></tr>
    ''')
    for cat in CATEGORIES:
        n = len(categorized[cat["id"]])
        pct = n / len(results) * 100
        html_parts.append(f'''
        <tr>
            <td style="color:{cat['color']};font-weight:bold;">{cat['icon']} {cat['title']}</td>
            <td>{n} ({pct:.0f}%)</td>
            <td style="font-size:7.5pt;">{cat['description'][:120]}...</td>
        </tr>
        ''')
    html_parts.append('</table>')

    # ── Each category section ──
    global_index = 0
    for cat in CATEGORIES:
        entries = categorized[cat["id"]]
        if not entries:
            continue

        html_parts.append(f'''
        <div class="cat-header" id="{cat['id']}">
            <h1 style="background:{cat['bg']};color:{cat['color']};">
                {cat['icon']} {cat['title']}
            </h1>
        </div>
        <div class="cat-desc">{cat['description']}</div>
        <div class="cat-count">{len(entries)} responses</div>
        ''')

        # Sub-group by scenario for readability
        current_scenario = None
        for r, avg_score in entries:
            global_index += 1
            sid = r["scenario_id"]
            if sid != current_scenario:
                current_scenario = sid
                html_parts.append(f'''
                <div style="margin-top:3mm; margin-bottom:1mm; font-size:9pt; font-weight:bold; color:#213953; border-bottom: 1px solid #ddd; padding-bottom:1mm;">
                    Scenario {sid} — {html.escape(r.get("description",""))} ({CAT_LABELS.get(r["category"], r["category"])})
                </div>
                ''')
            html_parts.append(render_entry(r, global_index))

    # ── Close HTML ──
    html_parts.append('</body></html>')

    full_html = "\n".join(html_parts)

    # Write intermediate HTML (useful for debugging)
    html_file = RESULTS_DIR / "full_catalog.html"
    html_file.write_text(full_html, encoding="utf-8")
    print(f"HTML written: {html_file} ({html_file.stat().st_size / 1024:.0f} KB)")

    # ── Generate PDF via WeasyPrint ──
    print("Generating PDF (this may take a minute)...")
    from weasyprint import HTML
    HTML(string=full_html).write_pdf(str(OUTPUT_FILE))
    print(f"PDF generated: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.1f} MB")


if __name__ == "__main__":
    generate_catalog()

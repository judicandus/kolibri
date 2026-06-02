#!/usr/bin/env python3
"""
Angels Academy AI — RAG Corpus Documentation
Generates a detailed PDF documenting all sources, documents, and indexing details.
Updated to include multilingual EGW API corpus.
"""

import json
import os
import html as html_mod
from pathlib import Path
from datetime import datetime
from collections import defaultdict

RESULTS_DIR = Path(__file__).parent / "results"
CORPUS_DIR = Path(__file__).parent.parent / "corpus"
OUTPUT_FILE = RESULTS_DIR / "angels_academy_rag_corpus_documentation.pdf"

LANG_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "pt": "Portuguese",
    "ar": "Arabic", "my": "Burmese", "th": "Thai",
}


def format_size(size_bytes):
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} B"


def generate_report():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load chunks ──
    chunks_file = CORPUS_DIR / "processed" / "all_chunks.json"
    chunks = json.loads(chunks_file.read_text())
    print(f"Loaded {len(chunks)} chunks")

    # ── Load EGW API manifest ──
    api_manifest = []
    api_manifest_path = CORPUS_DIR / "egw_api" / "manifest.json"
    if api_manifest_path.exists():
        api_manifest = json.loads(api_manifest_path.read_text())
        print(f"Loaded API manifest: {len(api_manifest)} books")

    # ── Aggregate stats ──
    source_stats = defaultdict(lambda: {
        "chunks": 0, "words": 0, "chars": 0, "category": "", "book": "",
        "language": "en", "min_chunk": float("inf"), "max_chunk": 0, "texts": []
    })
    lang_stats = defaultdict(lambda: {"chunks": 0, "words": 0, "sources": set()})
    cat_stats = defaultdict(lambda: {"chunks": 0, "words": 0, "sources": set()})

    for c in chunks:
        src = c.get("source", "Unknown")
        text = c.get("text", "")
        lang = c.get("language", "en")
        cat = c.get("category", "")
        wc = len(text.split())
        source_stats[src]["chunks"] += 1
        source_stats[src]["words"] += wc
        source_stats[src]["chars"] += len(text)
        source_stats[src]["category"] = cat
        source_stats[src]["book"] = c.get("book", "")
        source_stats[src]["language"] = lang
        source_stats[src]["min_chunk"] = min(source_stats[src]["min_chunk"], wc)
        source_stats[src]["max_chunk"] = max(source_stats[src]["max_chunk"], wc)
        if len(source_stats[src]["texts"]) < 5:
            source_stats[src]["texts"].append(text)
        lang_stats[lang]["chunks"] += wc and 1
        lang_stats[lang]["words"] += wc
        lang_stats[lang]["sources"].add(src)
        cat_stats[cat]["chunks"] += 1
        cat_stats[cat]["words"] += wc
        cat_stats[cat]["sources"].add(src)

    # ── File inventory ──
    raw_dir = CORPUS_DIR / "raw"
    file_inventory = []
    for f in sorted(raw_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(raw_dir)
            file_inventory.append({
                "path": str(rel), "size": f.stat().st_size, "ext": f.suffix,
            })

    # EGW API files
    api_dir = CORPUS_DIR / "egw_api"
    api_files = []
    if api_dir.exists():
        for f in sorted(api_dir.glob("*.txt")):
            api_files.append({
                "path": f"egw_api/{f.name}", "size": f.stat().st_size, "ext": ".txt",
            })

    # ── Document metadata (base + original English) ──
    base_documents = [
        {
            "title": "28 Fundamental Beliefs of the Seventh-day Adventist Church",
            "source_key": "28 Fundamental Beliefs",
            "author": "General Conference of Seventh-day Adventists",
            "year": "2015 (revised edition)",
            "format": "PDF (12 pages)",
            "file": "28_fundamental_beliefs.pdf",
            "url": "https://adventist.org/wp-content/uploads/2020/06/ADV-28Beliefs2020.pdf",
            "category": "Doctrine",
            "priority": "Priority 1 — Core Doctrinal",
            "language": "en",
            "description": "The official statement of beliefs of the Seventh-day Adventist Church, organized into 28 articles covering the doctrines of God, humanity, salvation, the church, Christian life, and last-day events.",
            "topics": [
                "The Holy Scriptures", "The Trinity", "The Father", "The Son", "The Holy Spirit",
                "Creation", "The Nature of Humanity", "The Great Controversy",
                "The Life, Death, and Resurrection of Christ", "The Experience of Salvation",
                "Growing in Christ", "The Church", "The Remnant and Its Mission",
                "Unity in the Body of Christ", "Baptism", "The Lord's Supper",
                "Spiritual Gifts and Ministries", "The Gift of Prophecy", "The Law of God",
                "The Sabbath", "Stewardship", "Christian Behavior", "Marriage and the Family",
                "Christ's Ministry in the Heavenly Sanctuary", "The Second Coming of Christ",
                "Death and Resurrection", "The Millennium and the End of Sin", "The New Earth",
            ],
        },
        {
            "title": "King James Version (KJV) Bible",
            "source_key": "King James Version Bible",
            "author": "Authorized by King James I (1611)",
            "year": "1611 (public domain)",
            "format": "Plain text (4.2 MB)",
            "file": "kjv_bible.txt",
            "url": "https://www.gutenberg.org/ebooks/10",
            "category": "Bible",
            "priority": "Priority 1 — Biblical Text",
            "language": "en",
            "description": "The complete King James Version of the Bible, including all 66 books of the Old and New Testaments. The standard Bible version used in many Adventist educational contexts.",
            "topics": [
                "Old Testament — Pentateuch (Genesis–Deuteronomy)",
                "Old Testament — Historical Books (Joshua–Esther)",
                "Old Testament — Poetic Books (Job–Song of Solomon)",
                "Old Testament — Major Prophets (Isaiah–Daniel)",
                "Old Testament — Minor Prophets (Hosea–Malachi)",
                "New Testament — Gospels (Matthew–John)",
                "New Testament — Acts of the Apostles",
                "New Testament — Pauline Epistles (Romans–Philemon)",
                "New Testament — General Epistles (Hebrews–Jude)",
                "New Testament — Revelation",
            ],
        },
    ]

    # EGW book metadata
    egw_book_meta = {
        "SC": {
            "title": "Steps to Christ", "year": "1892",
            "description": "The foundational devotional book outlining the steps to a personal relationship with Christ. Covers repentance, confession, faith, acceptance, growing in Christ, and prayer. One of the most translated books in Adventist literature.",
            "topics": ["God's Love for Man", "The Sinner's Need of Christ", "Repentance", "Confession", "Consecration", "Faith and Acceptance", "The Test of Discipleship", "Growing Up into Christ", "The Work and the Life", "A Knowledge of God", "The Privilege of Prayer", "What to Do with Doubt", "Rejoicing in the Lord"],
        },
        "Ed": {
            "title": "Education", "year": "1903",
            "description": "Ellen White's comprehensive philosophy of education — true education as development of the whole person (physical, mental, spiritual). Directly relevant to the Angels Academy teaching mission.",
            "topics": ["First Principles — Source and Aim of True Education", "The Eden School", "Relation of Education to Redemption", "The Teacher Sent from God", "Nature Teaching", "The Bible as an Educator", "Science and the Bible", "History and Prophecy", "The School of the Hereafter"],
        },
        "CT": {
            "title": "Counsels to Parents, Teachers, and Students", "year": "1913",
            "description": "Practical guidance for educators within the Adventist school system. Essential reading for Angels Academy teachers, covering character development, discipline, health, and the balance between academic and spiritual education.",
            "topics": ["The Importance of Education", "Teachers and Teaching", "The Right Education", "Discipline", "Character Development", "The Bible in Education", "Recreation and Physical Culture", "The Home as a School"],
        },
        "DA": {
            "title": "The Desire of Ages", "year": "1898",
            "description": "A detailed devotional narrative of Jesus Christ's life and ministry. Part of the Conflict of the Ages series. The largest EGW work in the corpus, providing rich context for questions about Jesus' teachings, parables, and sacrifice.",
            "topics": ["The Incarnation", "The Ministry of Jesus in Galilee", "The Sermon on the Mount", "Parables of Jesus", "Miracles and Healing", "The Last Supper", "Gethsemane", "The Trial and Crucifixion", "The Resurrection and Ascension"],
        },
        "GC": {
            "title": "The Great Controversy", "year": "1888 (revised 1911)",
            "description": "The defining work of Adventist eschatology, tracing the cosmic conflict between Christ and Satan from the destruction of Jerusalem through the Reformation, end-time events, and the final resolution.",
            "topics": ["Destruction of Jerusalem", "The Early Church", "The Reformation", "The Advent Movement", "The Investigative Judgment", "The Origin of Evil", "The Final Warning", "The Time of Trouble", "The Second Coming", "The Millennium", "The Controversy Ended"],
        },
        "PP": {
            "title": "Patriarchs and Prophets", "year": "1890",
            "description": "Covers the biblical narrative from Creation through the reign of King David. Part of the Conflict of the Ages series. Provides detailed commentary on Genesis–1 Samuel.",
            "topics": ["Creation and the Fall", "The Flood", "Abraham, Isaac, Jacob", "The Exodus and Moses", "The Sanctuary and Its Services", "The Ten Commandments", "Conquest of Canaan", "The Judges", "Samuel and Saul", "David"],
        },
        "PK": {
            "title": "Prophets and Kings", "year": "1917",
            "description": "Continues the Old Testament narrative from Solomon through the return from Babylonian exile. Covers the divided monarchy, major and minor prophets, and the restoration.",
            "topics": ["Solomon's Kingdom", "The Divided Kingdom", "Elijah and Elisha", "Isaiah, Jeremiah, Ezekiel", "Daniel and the Captivity", "The Return from Exile", "Ezra and Nehemiah"],
        },
        "AA": {
            "title": "The Acts of the Apostles", "year": "1911",
            "description": "A detailed commentary on the New Testament book of Acts and the apostolic era. Covers Pentecost, Paul's missionary journeys, and the expansion of the early church.",
            "topics": ["Pentecost and the Early Church", "Peter's Ministry", "Stephen and the Persecution", "Paul's Conversion", "Paul's Missionary Journeys", "The Jerusalem Council", "Paul's Letters", "Paul's Final Years"],
        },
        "COL": {
            "title": "Christ's Object Lessons", "year": "1900",
            "description": "A study of the parables of Jesus, drawing spiritual and practical lessons from each story. Useful for teachers preparing lessons about Jesus' parables and storytelling methods.",
            "topics": ["The Sower and the Seed", "Tares Among the Wheat", "The Mustard Seed and Leaven", "Hidden Treasure and the Pearl", "The Lost Sheep, Lost Coin, Prodigal Son", "The Good Samaritan", "Talents and Faithful Stewardship", "The Ten Virgins"],
        },
        "MH": {
            "title": "The Ministry of Healing", "year": "1905",
            "description": "Addresses holistic health and wellbeing — physical, mental, and spiritual healing. Covers Jesus as the Great Physician, healthful living principles, and the connection between spiritual and physical health.",
            "topics": ["The True Medical Missionary", "Health Principles and Diet", "Mind and Body Connection", "The Home", "The Ministry of the Family", "Helping the Tempted and Fallen"],
        },
    }

    # Build API book → translation info map
    api_book_langs = defaultdict(list)
    for entry in api_manifest:
        api_book_langs[entry["code"]].append(entry)

    # ── Match stats to base documents ──
    for doc in base_documents:
        key = doc["source_key"]
        stats = source_stats.get(key, {})
        doc["chunks"] = stats.get("chunks", 0)
        doc["words"] = stats.get("words", 0)
        doc["avg_chunk_words"] = stats.get("words", 0) // max(1, stats.get("chunks", 1))
        fpath = CORPUS_DIR / "raw" / doc["file"]
        doc["file_size"] = fpath.stat().st_size if fpath.exists() else 0

    # ═══════════════════════════════════════════════════════════
    # BUILD HTML
    # ═══════════════════════════════════════════════════════════
    h = []
    h.append(f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 14mm 12mm 14mm 12mm;
    @bottom-center {{
        content: "Angels Academy AI — RAG Corpus Documentation — Page " counter(page) " of " counter(pages);
        font-size: 8pt; color: #888;
    }}
}}
body {{ font-family: 'Noto Sans', 'DejaVu Sans', sans-serif; font-size: 9.5pt; line-height: 1.4; color: #222; }}
h1 {{ color: #213953; font-size: 20pt; margin-bottom: 3mm; page-break-after: avoid; }}
h2 {{ color: #213953; font-size: 14pt; margin-top: 6mm; margin-bottom: 3mm; page-break-after: avoid; }}
h3 {{ color: #213953; font-size: 11pt; margin-top: 5mm; margin-bottom: 2mm; page-break-after: avoid; }}
h4 {{ color: #333; font-size: 10pt; margin-top: 4mm; margin-bottom: 1.5mm; page-break-after: avoid; }}
hr {{ border: none; border-top: 2px solid #a6c52e; margin: 4mm 0; }}
.subtitle {{ font-size: 11pt; color: #555; text-align: center; }}
table {{ width: 100%; border-collapse: collapse; margin: 3mm 0; font-size: 9pt; }}
th {{ background: #213953; color: white; padding: 2mm 3mm; text-align: left; font-size: 8.5pt; }}
td {{ padding: 2mm 3mm; border-bottom: 0.5pt solid #ddd; vertical-align: top; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
.stat-box {{
    display: inline-block; padding: 3mm 5mm; margin: 1mm; border-radius: 3px;
    text-align: center; min-width: 25mm;
}}
.stat-value {{ font-size: 18pt; font-weight: bold; color: #213953; }}
.stat-label {{ font-size: 7.5pt; color: #888; text-transform: uppercase; }}
.doc-card {{
    border: 0.5pt solid #ddd; border-radius: 3px; padding: 3mm 4mm;
    margin-bottom: 4mm; page-break-inside: avoid;
}}
.doc-card h3 {{ margin-top: 0; margin-bottom: 1mm; }}
.doc-meta {{ font-size: 8pt; color: #666; margin-bottom: 2mm; }}
.doc-meta span {{ display: inline-block; padding: 0.5mm 2mm; margin-right: 2mm; border-radius: 2px; }}
.cat-doctrine {{ background: #e8f5e9; color: #2e7d32; }}
.cat-bible {{ background: #e3f2fd; color: #1565c0; }}
.cat-egw {{ background: #f3e5f5; color: #6a1b9a; }}
.tag {{ display: inline-block; background: #f5f5f5; padding: 0.5mm 2mm; margin: 0.5mm; border-radius: 2px; font-size: 7.5pt; color: #555; }}
.lang-tag {{ display: inline-block; padding: 0.5mm 2mm; margin: 0.5mm; border-radius: 2px; font-size: 7.5pt; font-weight: bold; }}
.lang-en {{ background: #e3f2fd; color: #1565c0; }}
.lang-fr {{ background: #e8f5e9; color: #2e7d32; }}
.lang-es {{ background: #fff8e1; color: #f57f17; }}
.lang-pt {{ background: #fce4ec; color: #c62828; }}
.lang-ar {{ background: #f3e5f5; color: #6a1b9a; }}
.lang-my {{ background: #e0f7fa; color: #00695c; }}
.lang-th {{ background: #fff3e0; color: #e65100; }}
.desc {{ font-size: 9pt; margin: 1.5mm 0; }}
.pipeline-step {{ background: #f8f9fa; border-left: 3px solid #213953; padding: 2mm 3mm; margin: 2mm 0; }}
.pipeline-step strong {{ color: #213953; }}
.num {{ font-size: 8pt; font-weight: bold; color: white; background: #213953; padding: 0.5mm 2mm; border-radius: 50%; margin-right: 1mm; }}
.highlight {{ background: #e8f5e9; border: 1px solid #a6c52e; padding: 2mm 3mm; border-radius: 3px; margin: 2mm 0; }}
</style></head><body>
''')

    # ═══════════════════════════════════════════════════════════
    # TITLE PAGE
    # ═══════════════════════════════════════════════════════════
    total_words = sum(s["words"] for s in source_stats.values())
    total_chars = sum(s["chars"] for s in source_stats.values())
    n_languages = len(lang_stats)
    n_sources = len(source_stats)
    n_api_books = len(api_manifest)

    h.append(f'''
    <div style="text-align:center; padding-top: 30mm;">
        <h1 style="font-size: 24pt;">Angels Academy AI</h1>
        <h1 style="font-size: 17pt; color: #555;">RAG Corpus Documentation</h1>
        <hr>
        <p class="subtitle">Complete inventory of theological and educational source materials<br>
        indexed for Retrieval-Augmented Generation (RAG)<br>
        <strong>Multilingual Edition — {n_languages} Languages</strong></p>
        <p style="color:#888; font-size:9pt; margin-top:8mm;">Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}</p>
    </div>

    <div style="text-align:center; margin-top: 12mm;">
        <div class="stat-box" style="background:#e8f5e9;">
            <div class="stat-value">{len(chunks):,}</div><div class="stat-label">Total Chunks</div>
        </div>
        <div class="stat-box" style="background:#e3f2fd;">
            <div class="stat-value">{n_sources}</div><div class="stat-label">Source Documents</div>
        </div>
        <div class="stat-box" style="background:#f3e5f5;">
            <div class="stat-value">{total_words:,}</div><div class="stat-label">Total Words</div>
        </div>
        <div class="stat-box" style="background:#fff8e1;">
            <div class="stat-value">{n_languages}</div><div class="stat-label">Languages</div>
        </div>
    </div>

    <div style="text-align:center; margin-top: 8mm;">
    ''')
    for lang in sorted(lang_stats.keys()):
        lname = LANG_NAMES.get(lang, lang)
        lchunks = lang_stats[lang]["chunks"]
        h.append(f'<span class="lang-tag lang-{lang}">{lname}: {lchunks:,} chunks</span>')
    h.append('</div>')

    # ═══════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════
    h.append('''<div style="page-break-before:always;"><h1>Table of Contents</h1>
    <table>
    <tr><th>Section</th><th>Description</th></tr>
    <tr><td>1. Corpus Overview</td><td>Summary statistics and language breakdown</td></tr>
    <tr><td>2. Indexing Pipeline</td><td>How documents are processed, embedded, and stored</td></tr>
    <tr><td>3. Corpus Summary Table</td><td>All sources at a glance with chunk and word counts</td></tr>
    <tr><td>4. Core Sources — Detailed Inventory</td><td>28 Beliefs and KJV Bible</td></tr>
    <tr><td>5. EGW Writings — Multilingual Inventory</td><td>All 10 books across 5 languages (44 editions)</td></tr>
    <tr><td>6. Multilingual Coverage Matrix</td><td>Which books are available in which languages</td></tr>
    <tr><td>7. Vector Database Configuration</td><td>Qdrant collection details and retrieval process</td></tr>
    <tr><td>8. File Inventory</td><td>All raw and processed files on disk</td></tr>
    <tr><td>9. Coverage Gaps &amp; Future Additions</td><td>What's missing and what comes next</td></tr>
    </table></div>
    ''')

    # ═══════════════════════════════════════════════════════════
    # 1. CORPUS OVERVIEW
    # ═══════════════════════════════════════════════════════════
    h.append('''<div style="page-break-before:always;">
    <h1>1. Corpus Overview</h1>
    <p>The Angels Academy AI uses Retrieval-Augmented Generation (RAG) to ground all responses in authoritative
    Seventh-day Adventist theological and educational sources. When a user asks a question, the system retrieves
    the most relevant passages from the corpus and includes them in the LLM prompt, ensuring responses are
    doctrinally accurate and properly sourced.</p>
    ''')

    # Category breakdown
    cat_info = [
        ("doctrine", "Doctrine", "cat-doctrine", "Official 28 Fundamental Beliefs — the doctrinal foundation"),
        ("bible", "Bible", "cat-bible", "Complete King James Version — all 66 books"),
        ("egw", "EGW Writings", "cat-egw", "Ten core Ellen G. White books in up to 5 languages (44 editions total)"),
    ]
    h.append('<h3>By Category</h3><table><tr><th>Category</th><th>Sources</th><th>Chunks</th><th>Words</th><th>Description</th></tr>')
    for cat_key, cat_name, cat_class, cat_desc in cat_info:
        cs = cat_stats.get(cat_key, {"chunks": 0, "words": 0, "sources": set()})
        h.append(f'''<tr>
            <td><span class="{cat_class}">{cat_name}</span></td>
            <td>{len(cs["sources"])}</td>
            <td style="text-align:right;">{cs["chunks"]:,}</td>
            <td style="text-align:right;">{cs["words"]:,}</td>
            <td>{cat_desc}</td>
        </tr>''')
    h.append('</table>')

    # Language breakdown
    h.append('<h3>By Language</h3><table><tr><th>Language</th><th>Sources</th><th>Chunks</th><th>Words</th></tr>')
    for lang in sorted(lang_stats.keys()):
        ls = lang_stats[lang]
        lname = LANG_NAMES.get(lang, lang)
        h.append(f'''<tr>
            <td><span class="lang-tag lang-{lang}">{lname}</span></td>
            <td>{len(ls["sources"])}</td>
            <td style="text-align:right;">{ls["chunks"]:,}</td>
            <td style="text-align:right;">{ls["words"]:,}</td>
        </tr>''')
    h.append('</table>')

    h.append('''
    <div class="highlight">
        <strong>Data Source:</strong> EGW multilingual content was obtained via the official
        EGW Writings API (OAuth2 authenticated, <code>client_credentials</code> grant).
        The API provides chapter-level JSON with full paragraph text, enabling clean extraction without HTML/ePub parsing artifacts.
        English books were replaced with API versions for consistency across languages.
    </div>
    </div>
    ''')

    # ═══════════════════════════════════════════════════════════
    # 2. INDEXING PIPELINE
    # ═══════════════════════════════════════════════════════════
    h.append(f'''<div style="page-break-before:always;">
    <h1>2. Indexing Pipeline</h1>
    <p>Documents are processed through a 4-step pipeline:</p>

    <div class="pipeline-step">
        <span class="num">1</span> <strong>Extraction</strong> — Raw documents are read and converted to plain text.
        For EGW API content, chapter JSON files are parsed and HTML tags stripped. ePub files are unzipped and XHTML parsed.
        PDFs use <code>pdftotext</code>.
    </div>
    <div class="pipeline-step">
        <span class="num">2</span> <strong>Chunking</strong> — Text is split into overlapping chunks of ~500 words
        with 100-word overlap. Chunks are tagged with source, category, book, and <strong>language</strong> metadata.
    </div>
    <div class="pipeline-step">
        <span class="num">3</span> <strong>Embedding</strong> — Each chunk is embedded using
        <code>intfloat/multilingual-e5-large</code>, a 1024-dimensional multilingual sentence transformer.
        This model supports cross-language retrieval: a query in French retrieves relevant French-language corpus chunks,
        and can also surface English content when no matching French content exists.
        Documents are prefixed with "passage: " per the E5 specification.
    </div>
    <div class="pipeline-step">
        <span class="num">4</span> <strong>Storage</strong> — Embeddings and metadata are stored in Qdrant, an
        open-source vector database running on jarvis (192.168.1.133:6333). The collection uses cosine similarity
        for nearest-neighbor search. At query time, the top 5 most relevant chunks are retrieved and injected
        into the LLM system prompt.
    </div>

    <h3>Embedding Model Details</h3>
    <table>
    <tr><td style="width:35mm;"><strong>Model</strong></td><td>intfloat/multilingual-e5-large</td></tr>
    <tr><td><strong>Dimensions</strong></td><td>1024</td></tr>
    <tr><td><strong>Languages</strong></td><td>100+ languages including English, French, Arabic, Thai, Burmese, Portuguese, Spanish</td></tr>
    <tr><td><strong>Max tokens</strong></td><td>512</td></tr>
    <tr><td><strong>Query prefix</strong></td><td><code>query: </code> (for search queries)</td></tr>
    <tr><td><strong>Document prefix</strong></td><td><code>passage: </code> (for corpus chunks)</td></tr>
    <tr><td><strong>Distance metric</strong></td><td>Cosine similarity</td></tr>
    </table>
    </div>
    ''')

    # ═══════════════════════════════════════════════════════════
    # 3. CORPUS SUMMARY TABLE
    # ═══════════════════════════════════════════════════════════
    h.append('<div style="page-break-before:always;"><h1>3. Corpus Summary Table</h1>')
    h.append('<table><tr><th>Source</th><th>Language</th><th>Category</th><th>Chunks</th><th>Words</th><th>Avg Chunk</th></tr>')

    all_table_rows = []
    for src in sorted(source_stats.keys()):
        s = source_stats[src]
        avg = s["words"] // max(1, s["chunks"])
        lang = s.get("language", "en")
        cat = s.get("category", "")
        all_table_rows.append((src, lang, cat, s["chunks"], s["words"], avg))

    for src, lang, cat, ch, wd, avg in all_table_rows:
        cat_class = {"doctrine": "cat-doctrine", "bible": "cat-bible"}.get(cat, "cat-egw")
        cat_label = {"doctrine": "Doctrine", "bible": "Bible"}.get(cat, "EGW")
        lname = LANG_NAMES.get(lang, lang)
        src_short = src if len(src) < 55 else src[:52] + "..."
        h.append(f'''<tr>
            <td>{html_mod.escape(src_short)}</td>
            <td><span class="lang-tag lang-{lang}">{lname}</span></td>
            <td><span class="{cat_class}">{cat_label}</span></td>
            <td style="text-align:right;">{ch:,}</td>
            <td style="text-align:right;">{wd:,}</td>
            <td style="text-align:right;">~{avg}</td>
        </tr>''')

    h.append(f'''<tr style="font-weight:bold; background:#e8eaf6;">
        <td>TOTAL ({n_sources} sources)</td><td>{n_languages} langs</td><td></td>
        <td style="text-align:right;">{len(chunks):,}</td>
        <td style="text-align:right;">{total_words:,}</td>
        <td style="text-align:right;">~{total_words // max(1, len(chunks))}</td>
    </tr>''')
    h.append('</table></div>')

    # ═══════════════════════════════════════════════════════════
    # 4. CORE SOURCES — DETAILED INVENTORY
    # ═══════════════════════════════════════════════════════════
    h.append('<div style="page-break-before:always;"><h1>4. Core Sources — Detailed Inventory</h1>')

    for doc in base_documents:
        key = doc["source_key"]
        stats = source_stats.get(key, {})
        cat_class = {"Doctrine": "cat-doctrine", "Bible": "cat-bible"}.get(doc["category"], "cat-egw")
        topics_html = "".join(f'<span class="tag">{html_mod.escape(t)}</span>' for t in doc.get("topics", []))

        excerpt_html = ""
        texts = stats.get("texts", [])
        excerpt = ""
        for t in texts[2:]:
            if "This eBook is provided by" not in t[:200] and "Project Gutenberg" not in t[:200]:
                excerpt = t[:400]
                break
        if not excerpt and texts:
            excerpt = texts[-1][:400]
        if excerpt:
            excerpt_html = f'<div style="background:#f8f9fa; border-left:3px solid #a6c52e; padding:2mm 3mm; font-size:8.5pt; font-style:italic; color:#444; margin-top:2mm;">"{html_mod.escape(excerpt[:350])}..."</div>'

        h.append(f'''
        <div class="doc-card">
            <h3>{html_mod.escape(doc["title"])}</h3>
            <div class="doc-meta">
                <span class="{cat_class}">{doc["category"]}</span>
                <span style="background:#fff8e1;color:#f57f17;">{doc["priority"]}</span>
                <span class="lang-tag lang-en">English</span>
            </div>
            <table style="margin:1mm 0; font-size:8.5pt;">
                <tr><td style="width:25mm;border:none;"><strong>Author</strong></td><td style="border:none;">{doc["author"]}</td>
                    <td style="width:25mm;border:none;"><strong>Year</strong></td><td style="border:none;">{doc["year"]}</td></tr>
                <tr><td style="border:none;"><strong>Format</strong></td><td style="border:none;">{doc["format"]}</td>
                    <td style="border:none;"><strong>File</strong></td><td style="border:none;"><code>{doc["file"]}</code></td></tr>
                <tr><td style="border:none;"><strong>Chunks</strong></td><td style="border:none;">{doc["chunks"]:,}</td>
                    <td style="border:none;"><strong>Words</strong></td><td style="border:none;">~{doc["words"]:,}</td></tr>
            </table>
            <p class="desc">{doc["description"]}</p>
            <p style="font-size:8pt; margin-bottom:1mm;"><strong>Key Topics:</strong></p>
            <div>{topics_html}</div>
            {excerpt_html}
        </div>
        ''')
    h.append('</div>')

    # ═══════════════════════════════════════════════════════════
    # 5. EGW WRITINGS — MULTILINGUAL INVENTORY
    # ═══════════════════════════════════════════════════════════
    h.append('<div style="page-break-before:always;"><h1>5. EGW Writings — Multilingual Inventory</h1>')
    h.append(f'''<p>All 10 core Ellen G. White books are indexed from the
    official EGW Writings API, which provides clean JSON paragraph content.
    A total of <strong>{n_api_books} book-language editions</strong> are included across {len(set(e["lang"] for e in api_manifest))} languages.</p>''')

    egw_code_order = ["SC", "Ed", "CT", "DA", "GC", "PP", "PK", "AA", "COL", "MH"]
    for code in egw_code_order:
        meta = egw_book_meta.get(code, {})
        editions = api_book_langs.get(code, [])
        if not editions and not meta:
            continue

        topics_html = "".join(f'<span class="tag">{html_mod.escape(t)}</span>' for t in meta.get("topics", []))

        edition_rows = []
        total_ch = 0
        total_wd = 0
        for ed in sorted(editions, key=lambda e: e["lang"]):
            lang = ed["lang"]
            lname = LANG_NAMES.get(lang, lang)
            for sk, sv in source_stats.items():
                if sv.get("category") == "egw" and sv.get("language") == lang and code in sk:
                    edition_rows.append({
                        "lang": lang, "lname": lname,
                        "title": ed["title"], "book_id": ed["book_id"],
                        "chunks": sv["chunks"], "words": sv["words"],
                        "chars": ed["characters"],
                        "paragraphs": ed["paragraphs"],
                    })
                    total_ch += sv["chunks"]
                    total_wd += sv["words"]
                    break

        lang_tags = " ".join(f'<span class="lang-tag lang-{ed["lang"]}">{ed["lname"]}</span>' for ed in edition_rows)

        h.append(f'''
        <div class="doc-card">
            <h3>{html_mod.escape(meta.get("title", code))} ({code})</h3>
            <div class="doc-meta">
                <span class="cat-egw">EGW Writings</span>
                <span style="background:#fff8e1;color:#f57f17;">Ellen G. White, {meta.get("year", "")}</span>
                {lang_tags}
            </div>
            <p class="desc">{meta.get("description", "")}</p>
        ''')

        if edition_rows:
            h.append('<table style="font-size:8.5pt;"><tr><th>Language</th><th>Translated Title</th><th>API Book ID</th><th>Paragraphs</th><th>Chunks</th><th>Words</th></tr>')
            for ed in edition_rows:
                h.append(f'''<tr>
                    <td><span class="lang-tag lang-{ed["lang"]}">{ed["lname"]}</span></td>
                    <td>{html_mod.escape(ed["title"])}</td>
                    <td>{ed["book_id"]}</td>
                    <td style="text-align:right;">{ed["paragraphs"]:,}</td>
                    <td style="text-align:right;">{ed["chunks"]:,}</td>
                    <td style="text-align:right;">{ed["words"]:,}</td>
                </tr>''')
            h.append(f'''<tr style="font-weight:bold; background:#e8eaf6;">
                <td colspan="3">Total — {len(edition_rows)} editions</td>
                <td></td>
                <td style="text-align:right;">{total_ch:,}</td>
                <td style="text-align:right;">{total_wd:,}</td>
            </tr></table>''')

        if meta.get("topics"):
            h.append(f'<p style="font-size:8pt; margin-bottom:1mm;"><strong>Key Topics:</strong></p><div>{topics_html}</div>')

        h.append('</div>')

    h.append('</div>')

    # ═══════════════════════════════════════════════════════════
    # 6. MULTILINGUAL COVERAGE MATRIX
    # ═══════════════════════════════════════════════════════════
    h.append('<div style="page-break-before:always;"><h1>6. Multilingual Coverage Matrix</h1>')
    h.append('<p>This matrix shows which EGW books are available in which languages in the corpus.</p>')

    all_api_langs = sorted(set(e["lang"] for e in api_manifest))
    h.append('<table><tr><th>Book</th>')
    for lang in all_api_langs:
        lname = LANG_NAMES.get(lang, lang)
        h.append(f'<th style="text-align:center;">{lname}</th>')
    h.append('<th style="text-align:center;">Total</th></tr>')

    lang_totals = defaultdict(int)
    for code in egw_code_order:
        editions = {e["lang"] for e in api_book_langs.get(code, [])}
        title = egw_book_meta.get(code, {}).get("title", code)
        h.append(f'<tr><td><strong>{code}</strong> — {html_mod.escape(title)}</td>')
        count = 0
        for lang in all_api_langs:
            if lang in editions:
                h.append(f'<td style="text-align:center; background:#e8f5e9; color:#2e7d32;">&#10003;</td>')
                count += 1
                lang_totals[lang] += 1
            else:
                h.append('<td style="text-align:center; color:#ccc;">—</td>')
        h.append(f'<td style="text-align:center; font-weight:bold;">{count}</td></tr>')

    h.append('<tr style="font-weight:bold; background:#e8eaf6;"><td>Total books per language</td>')
    for lang in all_api_langs:
        h.append(f'<td style="text-align:center;">{lang_totals[lang]}</td>')
    h.append(f'<td style="text-align:center;">{sum(lang_totals.values())}</td></tr>')
    h.append('</table>')

    target_missing = {"my", "th"} - set(all_api_langs)
    if target_missing:
        missing_names = ", ".join(LANG_NAMES.get(l, l) for l in sorted(target_missing))
        h.append(f'''
        <div style="background:#fff3e0; border-left:3px solid #ff9800; padding:2mm 3mm; margin-top:3mm; font-size:9pt;">
            <strong>Note:</strong> {missing_names} translations are listed in the EGW Writings metadata as available,
            but are not accessible through the API download endpoint. These languages rely on cross-lingual retrieval
            from the existing corpus (the multilingual embedding model enables queries in any language to retrieve
            relevant content from the indexed languages).
        </div>''')

    h.append('</div>')

    # ═══════════════════════════════════════════════════════════
    # 7. VECTOR DATABASE CONFIG
    # ═══════════════════════════════════════════════════════════
    h.append(f'''<div style="page-break-before:always;">
    <h1>7. Vector Database Configuration</h1>
    <table>
    <tr><td style="width:40mm;"><strong>Database</strong></td><td>Qdrant v1.x (open source)</td></tr>
    <tr><td><strong>Host</strong></td><td>jarvis — 192.168.1.133:6333</td></tr>
    <tr><td><strong>Collection</strong></td><td><code>angels_academy</code></td></tr>
    <tr><td><strong>Points</strong></td><td><strong>{len(chunks):,}</strong></td></tr>
    <tr><td><strong>Vector dimensions</strong></td><td>1024</td></tr>
    <tr><td><strong>Distance metric</strong></td><td>Cosine similarity</td></tr>
    <tr><td><strong>Languages indexed</strong></td><td>{", ".join(LANG_NAMES.get(l, l) for l in sorted(lang_stats.keys()))}</td></tr>
    </table>

    <h3>Payload Schema (per point)</h3>
    <table>
    <tr><th>Field</th><th>Type</th><th>Description</th></tr>
    <tr><td><code>text</code></td><td>string</td><td>The actual text content of the chunk (~500 words)</td></tr>
    <tr><td><code>source</code></td><td>string</td><td>Full source attribution (e.g., "Ellen G. White — Vers Jesus (French)")</td></tr>
    <tr><td><code>category</code></td><td>string</td><td>One of: <code>doctrine</code>, <code>bible</code>, <code>egw</code></td></tr>
    <tr><td><code>book</code></td><td>string</td><td>Book title in the original language</td></tr>
    <tr><td><code>language</code></td><td>string</td><td>ISO language code: <code>en</code>, <code>fr</code>, <code>es</code>, <code>pt</code>, <code>ar</code></td></tr>
    </table>

    <h3>Multilingual Retrieval at Query Time</h3>
    <p>When a user sends a message, the system:</p>
    <ol>
        <li>Prepends <code>query: </code> to the user's message (per E5 model specification)</li>
        <li>Embeds the query using the same multilingual-e5-large model</li>
        <li>Searches the <code>angels_academy</code> collection for the top 5 nearest vectors by cosine similarity</li>
        <li>Injects the retrieved chunks into the LLM system prompt as "Reference Materials"</li>
        <li>The LLM uses these materials to ground its response with accurate citations</li>
    </ol>
    <p>Because both the corpus and queries are embedded with the same multilingual model:</p>
    <ul>
        <li><strong>Same-language retrieval:</strong> A French query will preferentially retrieve French corpus content (Vers Jesus, Le Grand Conflit, etc.)</li>
        <li><strong>Cross-language fallback:</strong> For languages without indexed content (Burmese, Thai), queries still retrieve semantically relevant content from other languages</li>
        <li><strong>Improved quality:</strong> Native-language corpus content reduces the LLM translation burden and improves grounding accuracy</li>
    </ul>
    </div>
    ''')

    # ═══════════════════════════════════════════════════════════
    # 8. FILE INVENTORY
    # ═══════════════════════════════════════════════════════════
    h.append('<div style="page-break-before:always;"><h1>8. File Inventory</h1>')

    h.append(f'<h3>8.1 Raw Source Files (<code>corpus/raw/</code>)</h3>')
    h.append(f'<p>{len(file_inventory)} files.</p>')
    h.append('<table><tr><th>File Path</th><th>Format</th><th>Size</th></tr>')
    for f in file_inventory:
        h.append(f'<tr><td><code>{html_mod.escape(f["path"])}</code></td><td>{f["ext"]}</td><td style="text-align:right;">{format_size(f["size"])}</td></tr>')
    tot_raw = sum(f["size"] for f in file_inventory)
    h.append(f'<tr style="font-weight:bold; background:#e8eaf6;"><td>TOTAL ({len(file_inventory)} files)</td><td></td><td style="text-align:right;">{format_size(tot_raw)}</td></tr>')
    h.append('</table>')

    if api_files:
        tot_api = sum(f["size"] for f in api_files)
        h.append(f'<h3>8.2 EGW API Content (<code>corpus/egw_api/</code>)</h3>')
        h.append(f'<p>{len(api_files)} text files extracted from the EGW Writings API. Total: {format_size(tot_api)}.</p>')
        h.append('<table><tr><th>File</th><th>Language</th><th>Size</th></tr>')
        for f in api_files:
            fname = Path(f["path"]).stem
            parts = fname.rsplit("_", 1)
            lang = parts[1] if len(parts) == 2 else "?"
            lname = LANG_NAMES.get(lang, lang)
            h.append(f'<tr><td><code>{html_mod.escape(f["path"])}</code></td><td><span class="lang-tag lang-{lang}">{lname}</span></td><td style="text-align:right;">{format_size(f["size"])}</td></tr>')
        h.append(f'<tr style="font-weight:bold; background:#e8eaf6;"><td>TOTAL ({len(api_files)} files)</td><td></td><td style="text-align:right;">{format_size(tot_api)}</td></tr>')
        h.append('</table>')

    proc_file = CORPUS_DIR / "processed" / "all_chunks.json"
    h.append(f'''<h3>8.3 Processed Files</h3>
    <table>
    <tr><td><code>corpus/processed/all_chunks.json</code></td><td>JSON</td><td style="text-align:right;">{format_size(proc_file.stat().st_size)}</td></tr>
    <tr><td><code>corpus/egw_api/manifest.json</code></td><td>JSON</td><td style="text-align:right;">{format_size(api_manifest_path.stat().st_size) if api_manifest_path.exists() else "—"}</td></tr>
    </table>
    <p style="font-size:8pt; color:#888;">The all_chunks.json contains all {len(chunks):,} chunks with metadata. The manifest.json tracks all API-downloaded books.</p>
    </div>
    ''')

    # ═══════════════════════════════════════════════════════════
    # 9. COVERAGE GAPS & FUTURE ADDITIONS
    # ═══════════════════════════════════════════════════════════
    h.append(f'''<div style="page-break-before:always;">
    <h1>9. Coverage Gaps &amp; Future Additions</h1>

    <h3>Resolved in This Update</h3>
    <table>
    <tr><th>Previously Identified Gap</th><th>Resolution</th></tr>
    <tr>
        <td>No non-English corpus</td>
        <td><strong>Resolved.</strong> Added {n_api_books - 10} non-English book editions via the EGW Writings API.
        The corpus now includes content in French, Spanish, Portuguese, and Arabic. Same-language RAG retrieval
        is now possible for these languages.</td>
    </tr>
    <tr>
        <td>EGW books in Portuguese / French</td>
        <td><strong>Resolved.</strong> All 10 EGW books indexed in both Portuguese and French.</td>
    </tr>
    </table>

    <h3>Remaining Gaps</h3>
    <table>
    <tr><th>Gap</th><th>Impact</th><th>Recommended Action</th></tr>
    <tr>
        <td>No Burmese or Thai EGW content</td>
        <td>These translations exist on egwwritings.org but are not available via the API download endpoint.
        Burmese and Thai queries rely on cross-lingual retrieval from other languages.</td>
        <td>Monitor EGW API for availability updates. Consider web scraping as fallback.</td>
    </tr>
    <tr>
        <td>Arabic coverage is partial (4 of 10 books)</td>
        <td>Only SC, GC, DA, and PK were found with Arabic translation references in the API content.
        Other books may have Arabic translations not linked in the paragraph metadata.</td>
        <td>Investigate alternative API endpoints or contact EGW Writings for Arabic book IDs.</td>
    </tr>
    <tr>
        <td>No non-English Bible</td>
        <td>Bible content is English-only (KJV). Non-English Bible queries rely on cross-lingual retrieval or LLM knowledge.</td>
        <td>Add Reina-Valera (Spanish), Louis Segond (French), Almeida (Portuguese) Bible texts.</td>
    </tr>
    <tr>
        <td>No SDA Church Manual</td>
        <td>Cannot answer questions about church governance or organizational structure.</td>
        <td>Obtain and index the Church Manual PDF.</td>
    </tr>
    <tr>
        <td>No Angels Academy course materials</td>
        <td>AI cannot reference the actual lessons teachers are using.</td>
        <td>Index materials as developed by the editorial team (highest-priority future addition).</td>
    </tr>
    <tr>
        <td>No BRI articles or official statements</td>
        <td>Limited scholarly research and official church position references.</td>
        <td>Scrape from adventistbiblicalresearch.org and adventist.org/official-statements/.</td>
    </tr>
    </table>

    <h3>Planned Additions (Phase 2+)</h3>
    <table>
    <tr><th>Source</th><th>Language</th><th>Priority</th><th>Status</th></tr>
    <tr><td>Angels Academy lesson materials</td><td>English + local languages</td><td>Priority 1</td><td>Awaiting editorial team</td></tr>
    <tr><td>Burmese/Thai EGW translations</td><td>Burmese, Thai</td><td>Priority 2</td><td>Not available via API — investigating</td></tr>
    <tr><td>Non-English Bibles</td><td>Spanish, French, Portuguese, Arabic</td><td>Priority 2</td><td>Research licensing needed</td></tr>
    <tr><td>Remaining Arabic EGW books</td><td>Arabic</td><td>Priority 2</td><td>Investigating API coverage</td></tr>
    <tr><td>SDA Church Manual</td><td>English</td><td>Priority 3</td><td>Need to obtain PDF</td></tr>
    <tr><td>BRI articles</td><td>English</td><td>Priority 3</td><td>Web scraping needed</td></tr>
    <tr><td>Sabbath School quarterlies</td><td>Multiple</td><td>Priority 3</td><td>Research needed</td></tr>
    </table>

    <h3>Re-indexing Process</h3>
    <p>When new materials are added:</p>
    <ol>
        <li>For raw files: place in <code>corpus/raw/</code> under the appropriate subdirectory</li>
        <li>For API content: run <code>python scripts/download_egw_api.py</code> to refresh from the EGW API</li>
        <li>Update <code>scripts/index_corpus.py</code> with any new source metadata</li>
        <li>Run: <code>python scripts/index_corpus.py</code> — re-processes all documents, re-embeds, and replaces the Qdrant collection</li>
        <li>The web app automatically uses the updated collection on the next query</li>
    </ol>
    </div>
    ''')

    h.append('</body></html>')

    full_html = "\n".join(h)

    # Write HTML
    html_file = RESULTS_DIR / "corpus_documentation.html"
    html_file.write_text(full_html, encoding="utf-8")
    print(f"HTML: {html_file} ({html_file.stat().st_size // 1024} KB)")

    # Generate PDF
    print("Generating PDF...")
    from weasyprint import HTML
    HTML(string=full_html).write_pdf(str(OUTPUT_FILE))
    print(f"PDF: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size // 1024} KB")


if __name__ == "__main__":
    generate_report()

#!/usr/bin/env python3
"""
Download all EGW books from the EGW Writings API for the Angels Academy AI RAG corpus.
Uses the /content/books/{id}/download endpoint which returns ZIP files with JSON chapter content.
"""

import json
import os
import sys
import time
import zipfile
import re
import subprocess
from io import BytesIO
from pathlib import Path
from html.parser import HTMLParser

# Load environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k] = v

EGW_CLIENT_ID = os.environ.get("EGW_CLIENT_ID", "")
EGW_CLIENT_SECRET = os.environ.get("EGW_CLIENT_SECRET", "")
API_BASE = "https://a.egwwritings.org"
TOKEN_URL = "https://cpanel.egwwritings.org/connect/token"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "corpus" / "egw_api"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Our 10 target books with English book IDs
TARGET_BOOKS = {
    "SC": {"en_id": 108, "title": "Steps to Christ"},
    "PP": {"en_id": 84, "title": "Patriarchs and Prophets"},
    "GC": {"en_id": 132, "title": "The Great Controversy"},
    "DA": {"en_id": 130, "title": "The Desire of Ages"},
    "COL": {"en_id": 15, "title": "Christ's Object Lessons"},
    "MH": {"en_id": 135, "title": "The Ministry of Healing"},
    "Ed": {"en_id": 29, "title": "Education"},
    "CT": {"en_id": 23, "title": "Counsels to Parents, Teachers, and Students"},
    "AA": {"en_id": 127, "title": "The Acts of the Apostles"},
    "PK": {"en_id": 88, "title": "Prophets and Kings"},
}

# Target languages
TARGET_LANGS = {"en", "fr", "es", "pt", "ar", "my", "th"}

# Languages where cross-references from English books don't work reliably.
# For these, we query the API directly by language to discover available books.
DIRECT_QUERY_LANGS = {"my", "th"}

LANG_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "pt": "Portuguese",
    "ar": "Arabic", "my": "Burmese", "th": "Thai"
}


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags from content, preserving text."""
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, data):
        self.result.append(data)

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.result.append("\n")

    def get_text(self):
        return "".join(self.result).strip()


def strip_html(text):
    """Remove HTML tags from text."""
    extractor = HTMLTextExtractor()
    extractor.feed(text)
    return extractor.get_text()


def get_token():
    """Get OAuth2 access token."""
    import requests
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "client_credentials",
        "client_id": EGW_CLIENT_ID,
        "client_secret": EGW_CLIENT_SECRET,
        "scope": "writings search"
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def api_get(token, endpoint, stream=False):
    """Make authenticated GET request to EGW API."""
    import requests
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{endpoint}", headers=headers, stream=stream)
    return resp


def download_book(token, book_id):
    """Download book ZIP and return extracted JSON data."""
    resp = api_get(token, f"content/books/{book_id}/download", stream=True)
    if resp.status_code != 200:
        print(f"  ✗ Download failed for book {book_id}: HTTP {resp.status_code}")
        return None

    try:
        zf = zipfile.ZipFile(BytesIO(resp.content))
    except zipfile.BadZipFile:
        print(f"  ✗ Invalid ZIP for book {book_id}")
        return None

    result = {
        "info": None,
        "toc": None,
        "chapters": [],
    }

    for name in zf.namelist():
        data = json.loads(zf.read(name))
        if name == "info.json":
            result["info"] = data
        elif name == "toc.json":
            result["toc"] = data
        elif name in ("para.json", "tracks.json"):
            continue
        else:
            # Chapter file like "108.21.json"
            result["chapters"].append({"filename": name, "paragraphs": data})

    return result


def extract_translated_book_ids(book_data, target_langs):
    """Extract translated book IDs from English book's translation references."""
    translated = {}
    # Look through all chapters for translation references
    for chapter in book_data.get("chapters", []):
        for para in chapter.get("paragraphs", []):
            for t in para.get("translations", []):
                lang = t.get("lang")
                if lang in target_langs and lang != "en" and lang not in translated:
                    book_id = int(t["para_id"].split(".")[0])
                    translated[lang] = book_id
            # Once we have all target langs, stop
            if len(translated) >= len(target_langs) - 1:  # -1 for 'en'
                return translated
    return translated


def extract_text_from_book(book_data):
    """Extract plain text from book JSON data, organized by chapter."""
    if not book_data or not book_data.get("info"):
        return None

    info = book_data["info"]
    toc = book_data.get("toc", [])
    chapters_data = book_data.get("chapters", [])

    # Build chapter order from TOC
    toc_order = {item["para_id"]: item.get("title", "") for item in toc} if toc else {}

    text_parts = []
    text_parts.append(f"# {info.get('title', 'Unknown')}")
    text_parts.append(f"Author: {info.get('author', 'Ellen G. White')}")
    text_parts.append(f"Reference: {info.get('code', '')}")
    text_parts.append("")

    # Sort chapters by the first para_id
    def chapter_sort_key(ch):
        if ch["paragraphs"]:
            pid = ch["paragraphs"][0].get("para_id", "0.0")
            try:
                return float(pid.split(".")[-1])
            except (ValueError, IndexError):
                return 0
        return 0

    chapters_data.sort(key=chapter_sort_key)

    total_paragraphs = 0
    for chapter in chapters_data:
        paras = chapter.get("paragraphs", [])
        chapter_text = []

        for para in paras:
            elem_type = para.get("element_type", "p")
            content = para.get("content", "")
            if not content:
                continue

            clean_text = strip_html(content)
            if not clean_text:
                continue

            if elem_type in ("h1", "h2", "h3", "h4"):
                chapter_text.append(f"\n## {clean_text}\n")
            else:
                chapter_text.append(clean_text)
                total_paragraphs += 1

        if chapter_text:
            text_parts.extend(chapter_text)
            text_parts.append("")

    return {
        "text": "\n".join(text_parts),
        "title": info.get("title", "Unknown"),
        "code": info.get("code", ""),
        "lang": info.get("lang", "en"),
        "author": info.get("author", "Ellen G. White"),
        "paragraphs": total_paragraphs,
    }


def main():
    print("=" * 60)
    print("EGW Writings API - Full Corpus Download")
    print("=" * 60)

    if not EGW_CLIENT_ID or not EGW_CLIENT_SECRET:
        print("ERROR: EGW_CLIENT_ID and EGW_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    # Get token
    print("\n[1/5] Authenticating...")
    token = get_token()
    print("  ✓ Token obtained")

    # Phase 1: Download English books and find translated IDs
    print("\n[2/5] Downloading English books and finding translations...")
    all_downloads = {}  # {code: {lang: book_id}}

    for code, info in TARGET_BOOKS.items():
        print(f"\n  {code} - {info['title']}...")
        en_id = info["en_id"]

        # Download English version
        book_data = download_book(token, en_id)
        if not book_data:
            continue

        all_downloads.setdefault(code, {})
        all_downloads[code]["en"] = {"book_id": en_id, "data": book_data}

        # Find translated book IDs
        translated_ids = extract_translated_book_ids(book_data, TARGET_LANGS)
        for lang, tid in translated_ids.items():
            all_downloads[code][lang] = {"book_id": tid, "data": None}

        avail = ["en"] + sorted(translated_ids.keys())
        print(f"  ✓ English downloaded ({len(book_data['chapters'])} chapters)")
        print(f"    Translations found: {', '.join(avail)}")

        time.sleep(0.5)  # Be polite to the API

    # Phase 2.5: Direct language discovery for underserved languages
    # Cross-references from English books don't reliably link to my/th translations,
    # so we query the API directly for books in those languages.
    print("\n[2.5/5] Discovering books by direct language query...")
    TARGET_EN_IDS = {info["en_id"]: code for code, info in TARGET_BOOKS.items()}

    for lang in sorted(DIRECT_QUERY_LANGS):
        resp = api_get(token, f"content/books?lang={lang}&type=book&ipp=200")
        if resp.status_code != 200:
            print(f"  ✗ Failed to list {LANG_NAMES.get(lang, lang)} books: HTTP {resp.status_code}")
            continue

        books = resp.json().get("results", [])
        print(f"\n  {LANG_NAMES.get(lang, lang)}: {len(books)} books available in API")

        for book in books:
            bid = book["book_id"]
            book_code = book.get("code", f"UNK{bid}")
            orig = book.get("original_book")

            # Check if this matches one of our 10 target books
            is_target = False
            if orig:
                orig_id = orig.get("book_id")
                orig_code = orig.get("code", "")
                if orig_id in TARGET_EN_IDS or orig_code in TARGET_BOOKS:
                    is_target = True

            # Always use the book's native API code to avoid losing content
            # when multiple editions exist (e.g. GCB58 vs GCBur for Burmese GC)
            marker = "✓" if is_target else "+"
            all_downloads.setdefault(book_code, {})
            if lang not in all_downloads.get(book_code, {}):
                all_downloads[book_code][lang] = {"book_id": bid, "data": None}
                print(f"    {marker} {book_code} [{lang}]: book_id={bid} — {book.get('title', '')}")

        time.sleep(0.5)

    # Phase 3: Download translated versions
    print("\n[3/5] Downloading translated versions...")
    download_count = 0
    for code in all_downloads:
        for lang, entry in all_downloads[code].items():
            if lang == "en":
                continue  # Already downloaded
            if entry.get("data"):
                continue  # Already have it

            bid = entry["book_id"]
            print(f"  {code} [{LANG_NAMES.get(lang, lang)}] (book_id={bid})...", end=" ")
            book_data = download_book(token, bid)
            if book_data:
                entry["data"] = book_data
                n_ch = len(book_data.get("chapters", []))
                print(f"✓ ({n_ch} chapters)")
                download_count += 1
            else:
                print("✗ failed")

            time.sleep(0.5)

    print(f"\n  Downloaded {download_count} translated books")

    # Phase 4: Extract text and save
    print("\n[4/5] Extracting text and saving...")
    manifest = []
    total_chars = 0

    for code in sorted(all_downloads.keys()):
        for lang in sorted(all_downloads[code].keys()):
            entry = all_downloads[code][lang]
            if not entry.get("data"):
                continue

            extracted = extract_text_from_book(entry["data"])
            if not extracted or not extracted["text"].strip():
                print(f"  ✗ {code}_{lang}: no text extracted")
                continue

            # Save text file
            filename = f"{code}_{lang}.txt"
            filepath = OUTPUT_DIR / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(extracted["text"])

            chars = len(extracted["text"])
            total_chars += chars
            manifest.append({
                "code": code,
                "lang": lang,
                "title": extracted["title"],
                "book_id": entry["book_id"],
                "file": filename,
                "paragraphs": extracted["paragraphs"],
                "characters": chars,
            })
            print(f"  ✓ {filename}: {extracted['paragraphs']} paragraphs, {chars:,} chars")

    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Books downloaded: {len(manifest)}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Manifest: {manifest_path}")
    print()

    # Per-language summary
    lang_stats = {}
    for m in manifest:
        lang = m["lang"]
        lang_stats.setdefault(lang, {"count": 0, "chars": 0})
        lang_stats[lang]["count"] += 1
        lang_stats[lang]["chars"] += m["characters"]

    print("  Per-language breakdown:")
    for lang in sorted(lang_stats.keys()):
        s = lang_stats[lang]
        print(f"    {LANG_NAMES.get(lang, lang):12s}: {s['count']:2d} books, {s['chars']:>10,} chars")


if __name__ == "__main__":
    main()

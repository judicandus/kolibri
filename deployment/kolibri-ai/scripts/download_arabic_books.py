#!/usr/bin/env python3
"""
Download Arabic EGW books from m.egwwritings.org for the Angels Academy AI RAG corpus.
Scrapes the public mobile site since we don't have API credentials.
"""

import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE_URL = "https://m.egwwritings.org"
USER_AGENT = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
OUTPUT_DIR = Path(__file__).parent.parent / "corpus" / "egw_api"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

# Books already in our corpus (from existing manifest)
EXISTING_AR_BOOK_IDS = {12363, 11266, 12411, 11711}  # DA, GC, PK, SC

# All Arabic books from https://m.egwwritings.org/ar/folders/1001
ARABIC_BOOKS = {
    13966: {"code": "AA", "title": "الاباء والانبياء", "en_title": "Patriarchs and Prophets"},
    13967: {"code": "AR", "title": "أعمال الرُّسل", "en_title": "Acts of the Apostles"},
    13914: {"code": "BHA", "title": "المَبَادئُ الأسَاسِيَّةُ - لِلِإصْلاَحِ الصِّحِّىِّ", "en_title": "Fundamentals of Health Reform"},
    12406: {"code": "CCA", "title": "ينصح للكنيسة", "en_title": "Counsels for the Church"},
    14226: {"code": "ChSAr", "title": "الخدمة المسيحية", "en_title": "Christian Service"},
    14220: {"code": "COLAr", "title": "المُعلّم الأعظم", "en_title": "Christ's Object Lessons"},
    14223: {"code": "SRAr", "title": "قِصَّة الفداء", "en_title": "Story of Redemption"},
    14213: {"code": "GrH", "title": "الرَجَاء العَظيم", "en_title": "The Great Hope"},
    13934: {"code": "Tr", "title": "التربية", "en_title": "Education"},
    12373: {"code": "SM", "title": "الصبا و الشباب", "en_title": "Messages to Young People"},
    13938: {"code": "KS", "title": "خدمة الشفاء", "en_title": "Ministry of Healing"},
    14227: {"code": "CSAr", "title": "إرشادات حول الوكالة", "en_title": "Counsels on Stewardship"},
    14454: {"code": "ArMB", "title": "خواطر من جبل البَرَكَة", "en_title": "Thoughts from the Mount of Blessing"},
}


class ContentExtractor(HTMLParser):
    """Extract text content from EGW chapter pages."""
    def __init__(self):
        super().__init__()
        self.in_egw_content = False
        self.in_heading = False
        self.texts = []
        self.current = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = d.get('class', '')
        if 'egw_content_wrapper' in cls and tag in ('h1', 'h2', 'h3', 'h4'):
            self.in_heading = True
            self.current = []
        elif 'egw_content_wrapper' in cls and tag == 'p':
            self.in_egw_content = True
            self.current = []

    def handle_data(self, data):
        if self.in_heading or self.in_egw_content:
            # Skip reference codes like "AA 10.1"
            stripped = data.strip()
            if stripped and not re.match(r'^[A-Za-z]{1,10}\s+\d+\.\d+$', stripped):
                self.current.append(data)

    def handle_endtag(self, tag):
        if self.in_heading and tag in ('h1', 'h2', 'h3', 'h4'):
            text = ''.join(self.current).strip()
            if text:
                self.texts.append(f"\n## {text}\n")
            self.in_heading = False
        elif self.in_egw_content and tag == 'p':
            text = ''.join(self.current).strip()
            if text:
                self.texts.append(text)
            self.in_egw_content = False


class TOCExtractor(HTMLParser):
    """Extract chapter links from TOC pages."""
    def __init__(self):
        super().__init__()
        self.chapters = []  # list of (para_id, title)
        self.in_toc_link = False
        self.current_href = None
        self.current_title = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'enable' in d.get('class', ''):
            href = d.get('href', '')
            # Links like /ar/book/13966.14
            m = re.match(r'/ar/book/(\d+\.\d+)', href)
            if m:
                self.in_toc_link = True
                self.current_href = m.group(1)
                self.current_title = []

    def handle_data(self, data):
        if self.in_toc_link:
            self.current_title.append(data)

    def handle_endtag(self, tag):
        if self.in_toc_link and tag == 'a':
            title = ''.join(self.current_title).strip()
            self.chapters.append((self.current_href, title))
            self.in_toc_link = False


def fetch_url(url, retries=3):
    """Fetch a URL with retries."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (URLError, HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  ✗ Failed to fetch {url}: {e}")
                return None


def get_toc(book_id):
    """Get table of contents for a book."""
    url = f"{BASE_URL}/ar/book/{book_id}/toc"
    html = fetch_url(url)
    if not html:
        return []

    extractor = TOCExtractor()
    extractor.feed(html)
    return extractor.chapters


def get_chapter_text(para_ref):
    """Get text content of a chapter."""
    url = f"{BASE_URL}/ar/book/{para_ref}"
    html = fetch_url(url)
    if not html:
        return []

    extractor = ContentExtractor()
    extractor.feed(html)
    return extractor.texts


def download_book(book_id, book_info):
    """Download a complete book and return extracted text."""
    code = book_info["code"]
    title = book_info["title"]
    en_title = book_info["en_title"]

    print(f"\n  [{code}] {title} ({en_title})...")

    # Get TOC
    chapters = get_toc(book_id)
    if not chapters:
        print(f"  ✗ No chapters found for book {book_id}")
        return None

    print(f"    Found {len(chapters)} chapters")

    # Build text
    text_parts = []
    text_parts.append(f"# {title}")
    text_parts.append(f"Author: Ellen G. White")
    text_parts.append(f"Reference: {code}")
    text_parts.append(f"English Title: {en_title}")
    text_parts.append("")

    total_paragraphs = 0
    for i, (para_ref, chapter_title) in enumerate(chapters):
        chapter_texts = get_chapter_text(para_ref)
        if chapter_texts:
            text_parts.extend(chapter_texts)
            text_parts.append("")
            para_count = len([t for t in chapter_texts if not t.startswith("\n##")])
            total_paragraphs += para_count
            print(f"    Chapter {i+1}/{len(chapters)}: {chapter_title[:40]}... ({para_count} paragraphs)")
        else:
            print(f"    Chapter {i+1}/{len(chapters)}: {chapter_title[:40]}... (empty)")

        # Be polite - don't hammer the server
        time.sleep(0.5)

    full_text = "\n".join(text_parts)
    return {
        "text": full_text,
        "title": title,
        "code": code,
        "en_title": en_title,
        "paragraphs": total_paragraphs,
        "characters": len(full_text),
    }


def main():
    print("=" * 60)
    print("Arabic EGW Books - Web Scraper Download")
    print("=" * 60)

    # Filter to only new books
    new_books = {bid: info for bid, info in ARABIC_BOOKS.items()
                 if bid not in EXISTING_AR_BOOK_IDS}

    print(f"\nBooks to download: {len(new_books)}")
    for bid, info in new_books.items():
        print(f"  {info['code']:8s} ({bid}): {info['title']} — {info['en_title']}")

    # Load existing manifest
    manifest = []
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        print(f"\nExisting manifest: {len(manifest)} entries")

    # Download each book
    print("\n" + "-" * 60)
    print("Downloading books...")
    print("-" * 60)

    new_entries = []
    for book_id, info in new_books.items():
        result = download_book(book_id, info)
        if not result or not result["text"].strip() or len(result["text"]) < 200:
            print(f"  ✗ {info['code']}: no usable text extracted, skipping")
            continue

        # Save text file
        filename = f"{info['code']}_ar.txt"
        filepath = OUTPUT_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result["text"])

        entry = {
            "code": info["code"],
            "lang": "ar",
            "title": result["title"],
            "book_id": book_id,
            "file": filename,
            "paragraphs": result["paragraphs"],
            "characters": result["characters"],
        }
        new_entries.append(entry)
        print(f"  ✓ {filename}: {result['paragraphs']} paragraphs, {result['characters']:,} chars")

    # Update manifest
    if new_entries:
        manifest.extend(new_entries)
        # Sort manifest by code, then language
        manifest.sort(key=lambda x: (x["code"], x["lang"]))
        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Manifest updated: {len(manifest)} total entries (+{len(new_entries)} new)")

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  New Arabic books downloaded: {len(new_entries)}")
    total_chars = sum(e["characters"] for e in new_entries)
    print(f"  Total new characters: {total_chars:,}")
    print(f"  Output directory: {OUTPUT_DIR}")

    if new_entries:
        print("\n  Books downloaded:")
        for e in new_entries:
            print(f"    {e['file']:20s} {e['paragraphs']:5d} paragraphs  {e['characters']:>10,} chars")

    print(f"\n  Next step: Run 'python3 scripts/index_corpus.py' to index the new books into Qdrant.")


if __name__ == "__main__":
    main()

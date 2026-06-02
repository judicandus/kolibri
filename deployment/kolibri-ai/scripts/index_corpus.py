#!/usr/bin/env python3
"""
Angels Academy AI — RAG Corpus Indexer
Downloads, chunks, embeds, and stores the Adventist theological corpus in Qdrant.
"""

import os
import re
import json
import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict
from html.parser import HTMLParser

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
def load_env_file():
    """Load key=value pairs from project .env into os.environ if not already set."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def detect_embedding_device() -> str:
    """Prefer explicit EMBEDDING_DEVICE, otherwise auto-detect CUDA."""
    forced_device = os.environ.get("EMBEDDING_DEVICE")
    if forced_device:
        return forced_device

    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass

    return "cpu"


load_env_file()

CORPUS_RAW = Path(__file__).parent.parent / "corpus" / "raw"
CORPUS_PROCESSED = Path(__file__).parent.parent / "corpus" / "processed"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "angels_academy"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_DEVICE = detect_embedding_device()
CHUNK_SIZE = 500  # tokens (approximate by words)
CHUNK_OVERLAP = 100

# Book metadata
EGW_BOOKS = {
    "SC": "Steps to Christ",
    "Ed": "Education",
    "GC": "The Great Controversy",
    "DA": "The Desire of Ages",
    "COL": "Christ's Object Lessons",
    "CT": "Counsels to Parents, Teachers, and Students",
    "PP": "Patriarchs and Prophets",
    "PK": "Prophets and Kings",
    "AA": "Acts of the Apostles",
    "MH": "Ministry of Healing",
}


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags and extract plain text."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "header", "footer"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer"):
            self.skip = False
        if tag in ("p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self.result.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return "".join(self.result)


def html_to_text(html: str) -> str:
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    text = extractor.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_epub_text(epub_path: Path) -> str:
    """Extract plain text from an ePub file."""
    texts = []
    with zipfile.ZipFile(epub_path, "r") as zf:
        # Find HTML/XHTML files in the epub
        html_files = sorted(
            [f for f in zf.namelist() if f.endswith((".html", ".xhtml", ".htm"))
             and "toc" not in f.lower() and "nav" not in f.lower()]
        )
        for hf in html_files:
            try:
                content = zf.read(hf).decode("utf-8", errors="replace")
                text = html_to_text(content)
                if len(text.strip()) > 50:
                    texts.append(text.strip())
            except Exception:
                continue
    return "\n\n".join(texts)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using pdftotext if available, else basic extraction."""
    import subprocess
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback: try with Python
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(pdf_path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        print(f"  WARNING: Cannot extract PDF {pdf_path}. Install pdftotext or PyPDF2.")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def process_28_beliefs() -> List[Dict]:
    """Process the 28 Fundamental Beliefs PDF."""
    pdf_path = CORPUS_RAW / "28_fundamental_beliefs.pdf"
    if not pdf_path.exists():
        print("  28 Beliefs PDF not found, skipping")
        return []

    text = extract_pdf_text(pdf_path)
    if not text:
        return []

    chunks = chunk_text(text)
    docs = []
    for i, chunk in enumerate(chunks):
        docs.append({
            "text": chunk,
            "source": "28 Fundamental Beliefs",
            "category": "doctrine",
            "book": "28 Fundamental Beliefs",
            "chapter": "",
            "language": "en",
            "chunk_index": i,
        })
    print(f"  28 Beliefs: {len(docs)} chunks")
    return docs


def process_kjv_bible() -> List[Dict]:
    """Process KJV Bible text into book/chapter chunks."""
    bible_path = CORPUS_RAW / "kjv_bible.txt"
    if not bible_path.exists():
        print("  KJV Bible not found, skipping")
        return []

    text = bible_path.read_text(encoding="utf-8", errors="replace")

    # Remove Gutenberg header/footer
    start_marker = "The First Book of Moses:  Called Genesis"
    end_marker = "*** END OF THE PROJECT GUTENBERG"
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    if start_idx > 0:
        text = text[start_idx:]
    if end_idx > 0:
        text = text[:end_idx]

    # Split into books (books start with a line like "The First Book of Moses...")
    book_pattern = re.compile(
        r"^((?:The )?(?:First|Second|Third|Fourth|Fifth|General|Song)?\s*(?:Book of |Epistle of |Gospel According to )?.+?)$",
        re.MULTILINE
    )

    # Simpler approach: chunk the whole Bible
    chunks = chunk_text(text, chunk_size=400, overlap=80)
    docs = []
    for i, chunk in enumerate(chunks):
        docs.append({
            "text": chunk,
            "source": "King James Version Bible",
            "category": "bible",
            "book": "KJV Bible",
            "chapter": "",
            "language": "en",
            "chunk_index": i,
        })
    print(f"  KJV Bible: {len(docs)} chunks")
    return docs


def process_egw_books() -> List[Dict]:
    """Process all EGW ePub books (English only, as fallback)."""
    egw_dir = CORPUS_RAW / "egw"
    if not egw_dir.exists():
        print("  EGW directory not found, skipping")
        return []

    # Skip ePubs that have API versions (API content is cleaner)
    api_dir = Path(__file__).parent.parent / "corpus" / "egw_api"
    api_codes = set()
    if api_dir.exists():
        for f in api_dir.glob("*_en.txt"):
            api_codes.add(f.stem.replace("_en", ""))

    docs = []
    for code, title in EGW_BOOKS.items():
        if code in api_codes:
            print(f"  {code} ({title}): skipping ePub, using API version")
            continue

        epub_path = egw_dir / f"{code}.epub"
        if not epub_path.exists():
            print(f"  {code} ({title}): not found, skipping")
            continue

        text = extract_epub_text(epub_path)
        if not text or len(text) < 100:
            print(f"  {code} ({title}): empty or too short, skipping")
            continue

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            docs.append({
                "text": chunk,
                "source": f"Ellen G. White — {title}",
                "category": "egw",
                "book": title,
                "chapter": "",
                "language": "en",
                "chunk_index": i,
            })
        print(f"  {code} ({title}): {len(chunks)} chunks")

    return docs


LANG_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "pt": "Portuguese",
    "ar": "Arabic", "my": "Burmese", "th": "Thai",
}


def process_egw_api_books() -> List[Dict]:
    """Process EGW books downloaded via the EGW Writings API (multilingual)."""
    api_dir = Path(__file__).parent.parent / "corpus" / "egw_api"
    manifest_path = api_dir / "manifest.json"

    if not manifest_path.exists():
        print("  EGW API manifest not found, skipping")
        return []

    with open(manifest_path) as f:
        manifest = json.load(f)

    docs = []
    for entry in manifest:
        code = entry["code"]
        lang = entry["lang"]
        title = entry["title"]
        filename = entry["file"]
        filepath = api_dir / filename

        if not filepath.exists():
            print(f"  {filename}: file missing, skipping")
            continue

        text = filepath.read_text(encoding="utf-8")
        if not text or len(text) < 100:
            print(f"  {filename}: empty or too short, skipping")
            continue

        chunks = chunk_text(text)
        lang_name = LANG_NAMES.get(lang, lang)
        for i, chunk in enumerate(chunks):
            docs.append({
                "text": chunk,
                "source": f"Ellen G. White — {title} ({lang_name})",
                "category": "egw",
                "book": title,
                "chapter": "",
                "language": lang,
                "chunk_index": i,
            })
        print(f"  {filename}: {len(chunks)} chunks ({lang_name})")

    return docs


def process_angels_website() -> List[Dict]:
    """Process Angels for Education website content (multilingual)."""
    raw_dir = CORPUS_RAW
    website_files = {
        "en": "angels_website_en.txt",
        "fr": "angels_website_fr.txt",
        "es": "angels_website_es.txt",
        "pt": "angels_website_pt.txt",
        "ar": "angels_website_ar.txt",
    }

    docs = []
    for lang, filename in website_files.items():
        filepath = raw_dir / filename
        if not filepath.exists():
            print(f"  {filename}: not found, skipping")
            continue

        text = filepath.read_text(encoding="utf-8")
        if not text or len(text) < 100:
            print(f"  {filename}: empty or too short, skipping")
            continue

        chunks = chunk_text(text, chunk_size=300, overlap=60)
        lang_name = LANG_NAMES.get(lang, lang)
        for i, chunk in enumerate(chunks):
            docs.append({
                "text": chunk,
                "source": f"Angels for Education — Website ({lang_name})",
                "category": "organization",
                "book": "Angels for Education",
                "chapter": "",
                "language": lang,
                "chunk_index": i,
            })
        print(f"  {filename}: {len(chunks)} chunks ({lang_name})")

    return docs


def process_teaching_materials() -> List[Dict]:
    """Process ESL/EFL teaching materials for ages 3-18."""
    materials_dir = CORPUS_RAW / "teaching_materials"
    if not materials_dir.exists():
        print("  Teaching materials directory not found, skipping")
        return []

    # Map filenames to age groups and categories
    file_meta = {
        "esl_ages_3_6_pre_primary.txt": {
            "source": "ESL Teaching Materials — Pre-Primary (Ages 3-6)",
            "category": "teaching_esl",
            "book": "ESL Pre-Primary",
        },
        "esl_ages_7_12_primary.txt": {
            "source": "ESL Teaching Materials — Primary (Ages 7-12)",
            "category": "teaching_esl",
            "book": "ESL Primary",
        },
        "esl_ages_13_18_secondary.txt": {
            "source": "ESL Teaching Materials — Secondary (Ages 13-18)",
            "category": "teaching_esl",
            "book": "ESL Secondary",
        },
        "english_grammar_reference.txt": {
            "source": "English Grammar Reference Guide",
            "category": "teaching_grammar",
            "book": "Grammar Reference",
        },
    }

    docs = []
    for filename, meta in file_meta.items():
        filepath = materials_dir / filename
        if not filepath.exists():
            print(f"  {filename}: not found, skipping")
            continue

        text = filepath.read_text(encoding="utf-8")
        if not text or len(text) < 100:
            print(f"  {filename}: empty or too short, skipping")
            continue

        chunks = chunk_text(text, chunk_size=300, overlap=60)
        for i, chunk in enumerate(chunks):
            docs.append({
                "text": chunk,
                "source": meta["source"],
                "category": meta["category"],
                "book": meta["book"],
                "chapter": "",
                "language": "en",
                "chunk_index": i,
            })
        print(f"  {filename}: {len(chunks)} chunks")

    # Also process any additional .txt files not in the map
    for filepath in sorted(materials_dir.glob("*.txt")):
        if filepath.name in file_meta:
            continue
        text = filepath.read_text(encoding="utf-8")
        if not text or len(text) < 100:
            continue
        chunks = chunk_text(text, chunk_size=300, overlap=60)
        for i, chunk in enumerate(chunks):
            docs.append({
                "text": chunk,
                "source": f"Teaching Materials — {filepath.stem}",
                "category": "teaching_general",
                "book": filepath.stem,
                "chapter": "",
                "language": "en",
                "chunk_index": i,
            })
        print(f"  {filepath.name}: {len(chunks)} chunks (extra)")

    return docs


def main():
    print("=" * 60)
    print("Angels Academy AI — RAG Corpus Indexer")
    print("=" * 60)

    # 1. Process all documents
    print("\n[1/4] Processing documents...")
    all_docs = []
    all_docs.extend(process_28_beliefs())
    all_docs.extend(process_kjv_bible())
    all_docs.extend(process_egw_books())

    print("\n  EGW API books (multilingual):")
    all_docs.extend(process_egw_api_books())

    print("\n  Angels for Education website (multilingual):")
    all_docs.extend(process_angels_website())

    print("\n  ESL/EFL teaching materials:")
    all_docs.extend(process_teaching_materials())

    if not all_docs:
        print("ERROR: No documents processed!")
        return

    print(f"\nTotal documents: {len(all_docs)}")

    # 2. Save processed chunks for reference
    print("\n[2/4] Saving processed chunks...")
    CORPUS_PROCESSED.mkdir(parents=True, exist_ok=True)
    with open(CORPUS_PROCESSED / "all_chunks.json", "w") as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {CORPUS_PROCESSED / 'all_chunks.json'}")

    # 3. Generate embeddings
    print(f"\n[3/4] Generating embeddings with {EMBEDDING_MODEL}...")
    print(f"  Loading model on device: {EMBEDDING_DEVICE}")
    print("  Loading model (this may take a minute on first run)...")
    model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)

    # For multilingual-e5, prepend "passage: " for documents
    texts_to_embed = [f"passage: {doc['text']}" for doc in all_docs]

    print(f"  Embedding {len(texts_to_embed)} chunks...")
    embeddings = model.encode(
        texts_to_embed,
        show_progress_bar=True,
        batch_size=32,
        normalize_embeddings=True,
    )
    dim = embeddings.shape[1]
    print(f"  Embedding dimension: {dim}")

    # 4. Store in Qdrant
    print(f"\n[4/4] Storing in Qdrant ({QDRANT_URL})...")
    client = QdrantClient(url=QDRANT_URL)

    # Recreate collection
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection '{COLLECTION_NAME}'")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    print(f"  Created collection '{COLLECTION_NAME}' (dim={dim})")

    # Upload in batches
    batch_size = 100
    for i in range(0, len(all_docs), batch_size):
        batch_docs = all_docs[i : i + batch_size]
        batch_embs = embeddings[i : i + batch_size]

        points = []
        for j, (doc, emb) in enumerate(zip(batch_docs, batch_embs)):
            point_id = hashlib.md5(
                f"{doc['source']}:{doc['chunk_index']}".encode()
            ).hexdigest()
            # Use integer ID from hash
            int_id = int(point_id[:15], 16)

            points.append(
                PointStruct(
                    id=int_id,
                    vector=emb.tolist(),
                    payload={
                        "text": doc["text"],
                        "source": doc["source"],
                        "category": doc["category"],
                        "book": doc["book"],
                        "language": doc["language"],
                    },
                )
            )

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"  Uploaded {i + len(batch_docs)}/{len(all_docs)} points")

    # Verify
    info = client.get_collection(COLLECTION_NAME)
    print(f"\n✓ Collection '{COLLECTION_NAME}': {info.points_count} points, dim={info.config.params.vectors.size}")
    print("\nDone!")


if __name__ == "__main__":
    main()

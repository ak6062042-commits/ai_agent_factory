import pymupdf as fitz
from pathlib import Path
import re


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"•|●|▪", "-", text)
    return text.strip()


def parse_pdf(file_path: str) -> list[dict]:
    doc = fitz.open(file_path)
    pages = []
    for page_num in range(len(doc)):
        text = clean_text(doc[page_num].get_text())
        if text:
            pages.append({"text": text, "page": page_num + 1})
    return pages


def parse_document(file_path: str) -> list[dict]:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")
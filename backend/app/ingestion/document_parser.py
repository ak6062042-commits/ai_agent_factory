import pymupdf as fitz
from pathlib import Path
import re
import docx
import csv
from backend.log.logger import Logger

logger = Logger()


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

def parse_docx(file_path: str) -> list[dict]:
    doc = docx.Document(file_path)
    paragraphs = []
    for para in doc.paragraphs:
        text = clean_text(para.text)
        if text:
            paragraphs.append({"text": text, "page": 1})
    return paragraphs
        
def parse_text(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding = 'utf-8', errors = "ignore") as f:
        text = clean_text(f.read())
    
    logger.log("text file was parsed and page num returned None\n(to understand reason view the Note in backend/app/ingestion/document_parser.py under parse_text definition)", "WARNING")
    return [{"text": text, "page": None}] if text else []

# NOTE: text overlaps with the web content retrival as text format and implemented that as None for web content Will look over it to getting pass this  limitation
        

def parse_csv(file_path: str) -> list[dict]:
    rows = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if header:
                row_str = "".join(f"{h}: {v}" for h, v in zip(header, row) if v)
            else:
                row_str = " ".join(str(cell) for cell in row if cell is not None)
            text = clean_text(row_str)
            if text:
                rows.append({"text": text, "page": 1})
    return rows
    


def parse_document(file_path: str) -> list[dict]:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    elif suffix == ".docx":
        return parse_docx(file_path)
    elif suffix == ".txt":
        return parse_text(file_path)
    elif suffix == ".csv":
        return parse_csv(file_path)
    
    logger.log(f"Unsupported file type: {suffix}", "ERROR")
    raise ValueError(f"Unsupported file type: {suffix}")
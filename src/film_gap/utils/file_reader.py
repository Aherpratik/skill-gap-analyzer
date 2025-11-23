# src/film_gap/utils/file_reader.py

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
import PyPDF2
import docx  # from python-docx


def _read_txt_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def _read_docx_bytes(data: bytes) -> str:
    doc = docx.Document(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf_bytes(data: bytes) -> str:
    reader = PyPDF2.PdfReader(BytesIO(data))
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        chunks.append(txt)
    return "\n".join(chunks)


def extract_text_from_upload(upload: UploadFile) -> str:
    """
    Read text from an uploaded file (FastAPI UploadFile).

    Supports:
    - .txt
    - .docx
    - .pdf

    Falls back to UTF-8 decode if extension is unknown.
    """
    filename = upload.filename or ""
    ext = Path(filename).suffix.lower()

    data = upload.file.read()  # raw bytes

    if ext == ".txt":
        return _read_txt_bytes(data)
    if ext == ".docx":
        return _read_docx_bytes(data)
    if ext == ".pdf":
        return _read_pdf_bytes(data)

    # best-effort fallback
    return data.decode("utf-8", errors="ignore")

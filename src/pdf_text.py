from __future__ import annotations
from io import BytesIO
from typing import Optional
from pypdf import PdfReader


def extract_pdf_text(pdf_bytes: bytes, max_pages: int = 3) -> str:
    """
    Best-effort text extraction. Limits pages for speed/cost on Actions.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        texts = []
        for i, page in enumerate(reader.pages):
            if i >= max_pages:
                break
            t = page.extract_text() or ""
            if t:
                texts.append(t)
        return "\n".join(texts).strip()
    except Exception:
        return ""

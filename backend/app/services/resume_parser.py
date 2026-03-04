from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from app.core.config import get_settings
from app.models.member import Member


def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            with zf.open("word/document.xml") as fp:
                xml_content = fp.read()
        root = ElementTree.fromstring(xml_content)
        texts = [node.text for node in root.iter() if node.text]
        return "\n".join(t.strip() for t in texts if t.strip())
    except Exception:  # noqa: BLE001
        return ""


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        chunks: list[str] = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                chunks.append(txt.strip())
        return "\n".join(chunks)
    except Exception:  # noqa: BLE001
        return ""


def _is_good_resume_text(text: str) -> bool:
    """
    Heuristic quality check:
    - avoid short/noisy garbage
    - require enough letters/chinese/numbers ratio
    """
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) < 120:
        return False
    informative = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", cleaned)
    return (len(informative) / max(1, len(cleaned))) >= 0.35


def _extract_pdf_text_with_ocr(path: Path, *, max_pages: int = 6) -> str:
    """
    OCR fallback for scanned PDFs.
    Requires:
    - poppler (pdftoppm)
    - tesseract + chi_sim language pack
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
        import pytesseract  # type: ignore

        images = convert_from_path(str(path), dpi=220, first_page=1, last_page=max_pages)
        chunks: list[str] = []
        for img in images:
            txt = pytesseract.image_to_string(img, lang="chi_sim+eng", config="--psm 6") or ""
            if txt.strip():
                chunks.append(txt.strip())
        return "\n".join(chunks)
    except Exception:  # noqa: BLE001
        return ""


def extract_resume_text(member: Member, *, max_chars: int = 6000) -> str | None:
    """
    Best-effort resume text extraction for prompt context.

    Supported:
    - .pdf (prefer pypdf, fallback to utf-8 decode)
    - .docx (read word/document.xml)
    - .doc/.txt/.md and other text-like files (utf-8 decode)
    """

    if not member.resume_url:
        return None

    settings = get_settings()
    filename = member.resume_url.split("/")[-1]
    path = Path(settings.resumes_dir) / filename
    if not path.exists():
        return None

    ext = path.suffix.lower()
    text = ""
    if ext == ".pdf":
        text = _extract_pdf_text(path)
        if not _is_good_resume_text(text):
            text = _extract_pdf_text_with_ocr(path)
    elif ext == ".docx":
        text = _extract_docx_text(path)
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")

    text = re.sub(r"\s+", " ", text).strip()
    if not text or not _is_good_resume_text(text):
        return None
    return text[:max_chars]

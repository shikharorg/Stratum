from dataclasses import dataclass

import fitz
import pymupdf4llm
import pytesseract
import structlog
from PIL import Image

logger = structlog.get_logger()

_OCR_CHARS_PER_PAGE_THRESHOLD = 500
_MIN_LINES_FOR_STRIP = 20
_HEADER_FOOTER_RATIO = 0.05

_TEXT_SOURCE_TYPES = frozenset({"markdown", "code", "slack", "jira", "github"})


@dataclass
class PreprocessingResult:
    content: str
    page_count: int | None
    is_ocr: bool


def preprocess_document(
    raw_bytes: bytes, source_type: str, filename: str
) -> PreprocessingResult:
    if source_type == "pdf":
        return _preprocess_pdf(raw_bytes, filename)

    if source_type in _TEXT_SOURCE_TYPES:
        content = raw_bytes.decode("utf-8", errors="replace")
        return PreprocessingResult(content=content, page_count=None, is_ocr=False)

    content = raw_bytes.decode("utf-8", errors="replace")
    return PreprocessingResult(content=content, page_count=None, is_ocr=False)


def _preprocess_pdf(raw_bytes: bytes, filename: str) -> PreprocessingResult:
    with fitz.open(stream=raw_bytes, filetype="pdf") as doc:
        page_count = len(doc)
        if page_count == 0:
            return PreprocessingResult(content="", page_count=0, is_ocr=False)

        page_chunks: list[dict] = pymupdf4llm.to_markdown(doc, page_chunks=True)

        total_chars = sum(len(chunk.get("text", "")) for chunk in page_chunks)
        avg_chars = total_chars / page_count

        logger.info(
            "preprocessor.pdf_stats",
            filename=filename,
            page_count=page_count,
            avg_chars_per_page=avg_chars,
        )

        if avg_chars < _OCR_CHARS_PER_PAGE_THRESHOLD:
            logger.info("preprocessor.scanned_pdf_detected", filename=filename)
            return _ocr_pdf(doc, page_count)

        processed: list[str] = []
        for chunk in page_chunks:
            page_text = chunk.get("text", "")
            processed.append(_strip_headers_footers(page_text))

        content = "\n\n".join(filter(None, processed))
        return PreprocessingResult(content=content, page_count=page_count, is_ocr=False)


def _ocr_pdf(doc: fitz.Document, page_count: int) -> PreprocessingResult:
    ocr_pages: list[str] = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
        ocr_pages.append(text)
    content = "\n\n".join(filter(None, ocr_pages))
    return PreprocessingResult(content=content, page_count=page_count, is_ocr=True)


def _strip_headers_footers(page_text: str) -> str:
    lines = page_text.splitlines()
    if len(lines) <= _MIN_LINES_FOR_STRIP:
        return page_text
    strip_n = max(1, int(len(lines) * _HEADER_FOOTER_RATIO))
    return "\n".join(lines[strip_n : len(lines) - strip_n])

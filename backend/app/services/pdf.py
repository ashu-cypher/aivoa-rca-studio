"""PDF text extraction via PyMuPDF. Uploaded files are never executed."""

import fitz  # PyMuPDF


class PdfError(Exception):
    pass


class ScannedPdfError(PdfError):
    pass


def extract_pdf_text(data: bytes, filename: str) -> str:
    if not filename.lower().endswith(".pdf"):
        raise PdfError("Only PDF files are accepted for upload.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise PdfError(f"Could not read this PDF: {e}")
    parts: list[str] = []
    try:
        for page in doc:
            parts.append(page.get_text() or "")
    finally:
        doc.close()
    text = "\n".join(parts).strip()
    if len(text) < 50:
        raise ScannedPdfError(
            "This PDF produced little or no extractable text — it may be a scanned image. "
            "OCR is needed before AI analysis. Please paste the incident text instead, or upload a text-based PDF."
        )
    return text

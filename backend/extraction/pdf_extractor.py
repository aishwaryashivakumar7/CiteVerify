from pathlib import Path


class PDFExtractionError(RuntimeError):
    """Raised when a PDF cannot be read."""


def extract_pdf_pages(pdf_path: str | Path) -> list[str]:
    """
    Extract text from every page of a PDF.
    Returns a list where each item contains one page's text.
    """

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFExtractionError(
            "pypdf is required. Install it using: pip install pypdf"
        ) from exc

    path = Path(pdf_path)

    if not path.is_file():
        raise PDFExtractionError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError("Only PDF files are supported.")

    try:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise PDFExtractionError(f"Unable to read PDF: {exc}") from exc

    if not any(pages):
        raise PDFExtractionError(
            "No selectable text found. The PDF may be scanned and need OCR."
        )

    return pages


def extract_pdf_text(pdf_path: str | Path) -> str:
    """
    Extract all PDF text while preserving page boundaries.
    """

    return "\n\f\n".join(extract_pdf_pages(pdf_path))
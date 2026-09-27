from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF resume.

    Args:
        file_path: Path to the uploaded PDF file.

    Returns:
        Extracted text from all PDF pages.
    """

    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Resume file not found: {file_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported for text extraction"
        )

    reader = PdfReader(str(pdf_path))

    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_pages.append(page_text.strip())

    extracted_text = "\n\n".join(extracted_pages).strip()

    if not extracted_text:
        raise ValueError(
            "No readable text could be extracted from this PDF"
        )

    return extracted_text
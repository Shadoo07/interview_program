import io
import re
from pathlib import Path

try:
    # pymupdf >= 1.24 renamed the module; the old `fitz` name still works but
    # prints a deprecation warning on every import, so import the new name.
    import pymupdf as fitz

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()
    return text


def parse_pdf(file_path: Path) -> str:
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF is not installed. Please run: pip install PyMuPDF")

    text_parts = []
    doc = fitz.open(str(file_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_parts.append(page.get_text())
    doc.close()

    full_text = "\n".join(text_parts)
    return clean_text(full_text)


def parse_docx(file_path: Path) -> str:
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx is not installed. Please run: pip install python-docx")

    doc = Document(str(file_path))
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    full_text = "\n".join(text_parts)
    return clean_text(full_text)


def parse_txt(file_path: Path) -> str:
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return clean_text(content)


def parse_file(file_path: Path, file_type: str) -> str:
    file_type_lower = file_type.lower()

    if file_type_lower == ".pdf":
        return parse_pdf(file_path)
    elif file_type_lower == ".docx":
        return parse_docx(file_path)
    elif file_type_lower == ".txt":
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_file_content(file_content: bytes, filename: str) -> str:
    file_ext = Path(filename).suffix.lower()

    if file_ext == ".pdf":
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is not installed")
        doc = fitz.open("pdf", file_content)
        text_parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()
        return clean_text("\n".join(text_parts))

    elif file_ext == ".docx":
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is not installed")
        doc = Document(io.BytesIO(file_content))
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        return clean_text("\n".join(text_parts))

    elif file_ext == ".txt":
        return clean_text(file_content.decode("utf-8", errors="ignore"))

    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from app.utils.file_parser import parse_docx, parse_pdf, parse_txt


@dataclass
class TextChunk:
    content: str
    section_title: str = ""
    char_start: int = 0
    char_end: int = 0
    token_count: int = 0


HEADING_PATTERN = re.compile(
    r"^\s*(#{1,6}\s*)?(岗位要求|任职要求|岗位职责|项目经历|项目追问|技术栈|八股|简历表达|"
    r"教育背景|实习经历|获奖经历|个人优势|[一二三四五六七八九十]+[、.．]|[0-9]+[.．、])"
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?；;])\s+|\n+")


def get_file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    type_map = {
        "txt": "txt",
        "pdf": "pdf",
        "docx": "docx",
        "doc": "docx",
        "md": "txt",
        "markdown": "txt",
    }
    return type_map.get(ext, "txt")


class DocumentParseError(RuntimeError):
    """Raised when an uploaded knowledge document cannot be parsed into text."""


def parse_document(file_path: str, file_type: str) -> str:
    try:
        if file_type == "pdf":
            return parse_pdf(file_path)
        if file_type == "docx":
            return parse_docx(file_path)
        return parse_txt(file_path)
    except Exception as exc:
        raise DocumentParseError(f"Document parsing failed: {exc}") from exc


def split_text_into_chunks(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> list[str]:
    return [chunk.content for chunk in split_text_into_semantic_chunks(text, chunk_size, chunk_overlap)]


def split_text_into_semantic_chunks(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> list[TextChunk]:
    """Split text by sections first, then by sentence windows with bounded overlap."""
    cleaned = normalize_document_text(text)
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[TextChunk] = []
    for section_title, section_text, section_start in iter_sections(cleaned):
        units = split_units(section_text)
        current = ""
        current_start = section_start

        for unit, relative_start in units:
            unit = unit.strip()
            if not unit:
                continue
            candidate = join_text(current, unit)
            if len(candidate) <= chunk_size:
                if not current:
                    current_start = section_start + relative_start
                current = candidate
                continue

            if current:
                chunks.append(build_chunk(current, section_title, current_start, cleaned))
                current = build_overlap(current, chunk_overlap)
                current_start = max(section_start + relative_start - len(current), section_start)

            if len(unit) > chunk_size:
                chunks.extend(split_long_unit(unit, section_title, section_start + relative_start, chunk_size, chunk_overlap))
                current = ""
            else:
                current = join_text(current, unit)

        if current:
            chunks.append(build_chunk(current, section_title, current_start, cleaned))

    return dedupe_chunks(chunks)


def normalize_document_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def iter_sections(text: str) -> list[tuple[str, str, int]]:
    lines = text.splitlines()
    sections: list[tuple[str, list[str], int]] = []
    current_title = "正文"
    current_lines: list[str] = []
    current_start = 0
    offset = 0

    for line in lines:
        stripped = line.strip()
        is_heading = bool(stripped and len(stripped) <= 40 and HEADING_PATTERN.search(stripped))
        if is_heading and current_lines:
            sections.append((current_title, current_lines, current_start))
            current_title = stripped.strip("# ").strip()
            current_lines = [line]
            current_start = offset
        elif is_heading:
            current_title = stripped.strip("# ").strip()
            current_lines = [line]
            current_start = offset
        else:
            if not current_lines:
                current_start = offset
            current_lines.append(line)
        offset += len(line) + 1

    if current_lines:
        sections.append((current_title, current_lines, current_start))

    return [(title, "\n".join(items).strip(), start) for title, items, start in sections if "\n".join(items).strip()]


def split_units(text: str) -> list[tuple[str, int]]:
    units: list[tuple[str, int]] = []
    cursor = 0
    for part in SENTENCE_SPLIT_PATTERN.split(text):
        part = part.strip()
        if not part:
            continue
        position = text.find(part, cursor)
        if position < 0:
            position = cursor
        units.append((part, position))
        cursor = position + len(part)
    return units or [(text.strip(), 0)]


def join_text(left: str, right: str) -> str:
    if not left:
        return right.strip()
    return f"{left}\n{right.strip()}".strip()


def build_overlap(text: str, overlap: int) -> str:
    if overlap <= 0 or len(text) <= overlap:
        return text if len(text) <= overlap else ""
    tail = text[-overlap:]
    newline = tail.find("\n")
    return tail[newline + 1 :].strip() if newline >= 0 else tail.strip()


def split_long_unit(
    text: str,
    section_title: str,
    base_start: int,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind("，", start, end), text.rfind(",", start, end), text.rfind(" ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        content = text[start:end].strip()
        if content:
            chunks.append(
                TextChunk(
                    content=content,
                    section_title=section_title,
                    char_start=base_start + start,
                    char_end=base_start + end,
                    token_count=count_tokens(content),
                )
            )
        if end >= len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def build_chunk(content: str, section_title: str, start: int, full_text: str) -> TextChunk:
    content = content.strip()
    return TextChunk(
        content=content,
        section_title=section_title,
        char_start=start,
        char_end=min(start + len(content), len(full_text)),
        token_count=count_tokens(content),
    )


def dedupe_chunks(chunks: list[TextChunk]) -> list[TextChunk]:
    seen: set[str] = set()
    unique: list[TextChunk] = []
    for chunk in chunks:
        key = re.sub(r"\s+", "", chunk.content)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(chunk)
    return unique


def count_tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]", text))


def save_uploaded_file(file_bytes: bytes, filename: str, upload_dir: str) -> tuple[str, str]:
    os.makedirs(upload_dir, exist_ok=True)

    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(upload_dir, filename)):
        filename = f"{name}_{counter}{ext}"
        counter += 1

    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as file:
        file.write(file_bytes)

    return file_path, filename

import uuid
from datetime import UTC, datetime
from pathlib import Path

UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def generate_unique_filename(original_filename: str) -> str:
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{unique_id}{ext}"


def save_upload_file(file_content: bytes, filename: str) -> dict:
    if not allowed_file(filename):
        raise ValueError(f"File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}")

    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB")

    unique_filename = generate_unique_filename(filename)
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as f:
        f.write(file_content)

    return {
        "file_id": unique_filename,
        "original_filename": filename,
        "file_path": str(file_path),
        "file_size": len(file_content),
        "file_type": get_file_extension(filename)
    }


def get_upload_file_path(file_id: str) -> Path:
    file_path = UPLOAD_DIR / file_id
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_id}")
    return file_path


def delete_upload_file(file_id: str) -> bool:
    try:
        file_path = get_upload_file_path(file_id)
        file_path.unlink()
        return True
    except FileNotFoundError:
        return False

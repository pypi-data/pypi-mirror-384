import re
from pathlib import Path

from .schemas import NamedBytesIO


def detect_extension(file_path: str) -> str:
    """Return the file extension in lowercase."""
    return Path(file_path).suffix.lower()


def is_pdf(file_path: str) -> bool:
    """Check if the file is a PDF."""
    return detect_extension(file_path) == ".pdf"


def is_image(file_path: str) -> bool:
    """Check if the file is an image based on its extension."""
    return detect_extension(file_path) in (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff",
        ".gif",
        ".heic",
        ".webp",
    )


def is_audio(file_path: str) -> bool:
    """Check if the file is an audio file based on its extension."""
    return detect_extension(file_path) in (".mp3", ".wav", ".m4a", ".ogg", ".flac")


def is_zip(file_path: str) -> bool:
    """Check if the file is a ZIP archive."""
    return detect_extension(file_path) == ".zip"


def is_eml(file_path: str) -> bool:
    """Check if the file is an EML email file."""
    return detect_extension(file_path) == ".eml"


def clean_markdown(md_text: str) -> str:
    """
    Clean up Markdown text by removing trailing spaces and reducing excess newlines.
    """
    md_text = re.sub(r"[ \t]+(\r?\n)", r"\1", md_text)
    md_text = re.sub(r"\n{3,}", "\n\n", md_text)
    return md_text.strip()


def ensure_minimum_content(md_text: str) -> bool:
    """
    Check if the Markdown text has non-trivial content.
    """
    if not md_text:
        return False
    return bool(md_text and len(md_text.strip()) > 10)


SAFE_BOM_EXTS = {".csv", ".tsv", ".txt", ".log", ".md", ".rst"}
AVOID_BOM_EXTS = {".json", ".py", ".js", ".ts", ".sh", ".bat", ".ps1", ".sql"}


def has_utf8_bom(b: bytes) -> bool:
    return b.startswith(b"\xef\xbb\xbf")


def should_add_bom(
    ext: str,
    detected_enc: str,
    confidence: float,
    consumer_defaults_ascii: bool,
) -> bool:
    ext = ext.lower()
    if ext in AVOID_BOM_EXTS:
        return False
    if not consumer_defaults_ascii:
        return False
    enc = (detected_enc or "").replace("_", "-").lower()
    # Only add when it's actually UTF-8/ASCII and no BOM present
    if enc not in ("utf-8", "us-ascii", "ascii", "utf-8-sig"):
        return False
    # Use confidence guard so we don't add BOM to files we’re already certain about
    if confidence >= 0.10:
        return False
    return ext in SAFE_BOM_EXTS


def prepare_stream_with_optional_bom(
    path: str,
    detected_enc: str,
    confidence: float,
    consumer_defaults_ascii: bool = True,
) -> NamedBytesIO:
    p = Path(path)
    raw = p.read_bytes()
    if has_utf8_bom(raw):
        return NamedBytesIO(raw, name=p.name)
    if should_add_bom(p.suffix, detected_enc, confidence, consumer_defaults_ascii):
        return NamedBytesIO(b"\xef\xbb\xbf" + raw, name=p.name)
    return NamedBytesIO(raw, name=p.name)

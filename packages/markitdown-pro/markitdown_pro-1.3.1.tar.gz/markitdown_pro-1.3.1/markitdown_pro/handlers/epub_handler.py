import asyncio
import html
import re
from typing import List, Optional

from ..common.logger import logger
from .base_handler import BaseHandler

_EPU_TIMEOUT_SEC = 60
_MAX_SECTIONS = 5000


def _basic_html_to_md(html_text: str) -> str:
    t = html_text
    t = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", t)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</p\s*>", "\n\n", t)
    t = re.sub(r"(?i)<li\s*>", "- ", t)
    t = re.sub(r"(?i)</h1\s*>", "\n\n", re.sub(r"(?i)<h1\s*>(.*?)</h1\s*>", r"# \1\n\n", t))
    t = re.sub(r"(?i)</h2\s*>", "\n\n", re.sub(r"(?i)<h2\s*>(.*?)</h2\s*>", r"## \1\n\n", t))
    t = re.sub(r"(?i)</h3\s*>", "\n\n", re.sub(r"(?i)<h3\s*>(.*?)</h3\s*>", r"### \1\n\n", t))
    t = re.sub(r"(?i)<a\s+[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", r"[\2](\1)", t)
    t = re.sub(
        r"(?i)<img\s+[^>]*alt=['\"]([^'\"]*)['\"][^>]*src=['\"]([^'\"]+)['\"][^>]*>",
        r"![\1](\2)",
        t,
    )
    t = re.sub(r"(?is)<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t


def _epub_to_markdown(file_path: str, html_to_md=_basic_html_to_md) -> str:
    try:
        from bs4 import BeautifulSoup
        from ebooklib import epub
    except Exception as e:
        raise RuntimeError(f"EPUBHandler requires 'ebooklib' and 'beautifulsoup4': {e}")
    book = epub.read_epub(file_path)
    spine_items = []
    try:
        for _, itemref in book.spine:
            itm = book.get_item_with_id(itemref)
            if itm is not None:
                spine_items.append(itm)
    except Exception:
        pass
    if not spine_items:
        spine_items = [i for i in book.get_items() if getattr(i, "get_type", lambda: None)() == 9]
    parts: List[str] = []
    count = 0
    for item in spine_items:
        if count >= _MAX_SECTIONS:
            break
        try:
            html_bytes = item.get_content()
            soup = BeautifulSoup(html_bytes, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            md = html_to_md(str(soup))
            if title and md and not md.startswith("# "):
                md = f"# {title}\n\n{md}"
            if md:
                parts.append(md)
                count += 1
        except Exception as e:
            logger.warning(
                f"EPUBHandler: error parsing item {getattr(item, 'id', '(unknown)')}: {e}"
            )
            continue
    return "\n\n".join(parts).strip()


class EPUBHandler(BaseHandler):
    SUPPORTED_EXTENSIONS = frozenset({".epub"})

    async def handle(self, file_path, *args, **kwargs) -> Optional[str]:
        """
        Converts EPUB to Markdown using ebooklib+BeautifulSoup only (no pandoc).
        You may pass a custom HTML→MD callable via kwargs['html_to_md'] if desired.
        """
        logger.info(f"EPUBHandler: Processing file {file_path}")
        try:
            html_to_md = kwargs.get("html_to_md", _basic_html_to_md)
            md_content = await asyncio.wait_for(
                asyncio.to_thread(_epub_to_markdown, file_path, html_to_md),
                timeout=_EPU_TIMEOUT_SEC,
            )
            if md_content:
                return md_content
            logger.error("EPUBHandler: empty Markdown output")
            return None
        except asyncio.TimeoutError:
            logger.error(f"EPUBHandler: timeout processing '{file_path}'")
            return None
        except Exception as e:
            logger.error(f"EPUBHandler: error handling '{file_path}': {e}")
            return None

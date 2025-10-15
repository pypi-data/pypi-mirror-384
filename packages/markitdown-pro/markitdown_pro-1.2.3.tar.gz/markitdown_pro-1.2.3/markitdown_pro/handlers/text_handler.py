import os
from typing import Optional

import chardet

from ..common.logger import logger
from ..common.utils import clean_markdown, ensure_minimum_content
from .base_handler import BaseHandler


class TextHandler(BaseHandler):
    """Handler for .txt, .md, .py, .go, and other text/code files."""

    SUPPORTED_EXTENSIONS = frozenset([".txt", ".md", ".py", ".go"])

    async def handle(self, file_path: str, *args, **kwargs) -> Optional[str]:
        logger.info(f"Processing text file: {file_path}")
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"] or "utf-8"
                logger.debug(f"Detected encoding: {encoding}")
                content = raw_data.decode(encoding, errors="replace")

            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".md":
                content = clean_markdown(content)

            if ensure_minimum_content(content):
                return content
            else:
                logger.warning(f"Text handler failed or insufficient content: {file_path}.")
                return None
        except Exception as e:
            file_name = os.path.basename(file_path)
            logger.error(f"Error processing text file {file_name}: {e}")
            return None

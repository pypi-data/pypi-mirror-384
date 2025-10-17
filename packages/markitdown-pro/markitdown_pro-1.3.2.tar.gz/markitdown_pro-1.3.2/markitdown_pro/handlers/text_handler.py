import os
from typing import Optional

import chardet

from ..common.logger import logger
from .base_handler import BaseHandler


class TextHandler(BaseHandler):
    """Handler for .txt, .md, .py, .go, and other text/code files."""

    SUPPORTED_EXTENSIONS = frozenset([".txt", ".md", ".py", ".go"])

    async def handle(self, file_path: str, *args, **kwargs) -> Optional[str]:
        logger.info(f"TextHandler: Processing text file: {file_path}")
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"] or "utf-8"
                logger.debug(f"TextHandler: Detected encoding: {encoding}")
                content = raw_data.decode(encoding, errors="replace")

            return content
        except Exception as e:
            file_name = os.path.basename(file_path)
            logger.error(f"TextHandler: Error processing text file {file_name}: {e}")
            return None

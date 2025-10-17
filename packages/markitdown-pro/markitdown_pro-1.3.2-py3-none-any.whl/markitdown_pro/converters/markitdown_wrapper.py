from typing import Optional

from markitdown_pro.handlers.markitdown_handler import MarkItDownHandler

from ..common.logger import logger
from .base import ConverterWrapper


class MarkItDownWrapper(ConverterWrapper):
    SUPPORTED_EXTENSIONS = MarkItDownHandler.SUPPORTED_EXTENSIONS

    def __init__(self, *args, **kwargs):
        super().__init__("MarkItDown")
        self.handler = MarkItDownHandler(*args, **kwargs)

    async def convert(self, file_path: str) -> Optional[str]:
        file_extension = f".{file_path.split('.')[-1].lower()}"
        if file_extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"MarkItDownWrapper: Unsupported file format: {file_extension}")
            return None

        md_content = await self.handler.handle(file_path)
        return md_content

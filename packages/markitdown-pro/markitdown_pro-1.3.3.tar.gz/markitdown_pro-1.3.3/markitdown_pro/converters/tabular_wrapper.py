from typing import Optional

from ..common.logger import logger
from ..handlers.tabular_handler import TabularHandler
from .base import ConverterWrapper


class TabularWrapper(ConverterWrapper):
    SUPPORTED_FORMATS = (
        "csv",
        "tsv",
        "xls",
        "xlsx",
    )

    def __init__(self):
        super().__init__("TabularHandler")
        self.tabular_handler = TabularHandler()

    async def convert(self, file_path: str) -> Optional[str]:
        logger.debug(f"TabularWrapper: Converting {file_path} to markdown")
        file_extension = file_path.split(".")[-1].lower()

        if file_extension not in self.SUPPORTED_FORMATS:
            logger.warning(f"TabularWrapper: Unsupported file format: {file_extension}")
            return None

        markdown = await self.tabular_handler.handle(file_path)
        return markdown

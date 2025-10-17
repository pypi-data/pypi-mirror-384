from typing import Optional

import fitz  # PyMuPDF

from ..common.logger import logger
from .base import ConverterWrapper


class PyMuPDFWrapper(ConverterWrapper):
    SUPPORTED_EXTENSIONS = frozenset({"pdf", "xps", "epub", "mobi", "fb2", "cbz", "svg"})

    def __init__(self):
        super().__init__("PyMuPDF")

    async def convert(self, file_path: str) -> Optional[str]:
        file_extension = file_path.split(".")[-1].lower()
        logger.info(
            f"PyMuPDFWrapper: Processing file: {file_path} with extension: {file_extension}"
        )

        if file_extension not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"PyMuPDFWrapper: Unsupported file format: {file_extension}")
            return None

        try:
            doc = fitz.open(file_path)

            # Extract text from all pages
            text_content = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                text_content += "\n\n"

            doc.close()
            return text_content

        except Exception as e:
            logger.error(f"PyMuPDFWrapper: Error processing document with PyMuPDF: {e}")
            return None

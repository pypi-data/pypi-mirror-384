from typing import Optional

from ..services.azure_speech import AzureSpeechService
from .base import ConverterWrapper


class AzureSpeechWrapper(ConverterWrapper):
    SUPPORTED_EXTENSIONS = AzureSpeechService.SUPPORTED_EXTENSIONS

    def __init__(self):
        super().__init__("Azure Speech Service")
        self.converter = AzureSpeechService()

    async def convert(self, file_path: str) -> Optional[str]:
        return await self.converter.convert_to_md(file_path)

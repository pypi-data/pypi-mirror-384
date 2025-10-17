import logging
from pathlib import Path

import pytest

from markitdown_pro.common.utils import ensure_minimum_content
from markitdown_pro.handlers.image_handler import ImageHandler
from tests.fixtures import data_path, pretty_id
from tests.utils import list_files

log = logging.getLogger(__name__)

TEST_FILES_PATH = data_path()
ALL_FILES = list_files(
    TEST_FILES_PATH, include_ext=ImageHandler.SUPPORTED_EXTENSIONS, recursive=True
)
log.info(f"ImageHandler: Found {len(ALL_FILES)} test files in {TEST_FILES_PATH}.")


@pytest.mark.asyncio
@pytest.mark.parametrize("file_path", ALL_FILES, ids=[pretty_id(p) for p in ALL_FILES])
async def test_files(file_path: Path, image_handler: ImageHandler):
    log.info(f"ImageHandler: Testing file: {file_path}")

    markdown_text = await image_handler.handle(str(file_path))
    assert markdown_text is not None, f"Conversion returned None for {file_path.name}"
    assert isinstance(markdown_text, str), f"Output type is not str for {file_path.name}"
    assert ensure_minimum_content(markdown_text), f"Output is empty for {file_path.name}"

# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_file_system():
    mock_write_text = MagicMock()
    mock_mkdir = MagicMock()
    mock_read_text = MagicMock()
    mock_is_file = MagicMock()
    mock_exists = MagicMock()
    mock_is_dir = MagicMock()  # new addition for batch_cmd tests

    with (
        patch.object(Path, "write_text", mock_write_text),
        patch.object(Path, "mkdir", mock_mkdir),
        patch.object(Path, "read_text", mock_read_text),
        patch.object(Path, "is_file", mock_is_file),
        patch.object(Path, "exists", mock_exists),
        patch.object(Path, "is_dir", mock_is_dir),  # patch is_dir
    ):
        yield {
            "write_text": mock_write_text,
            "mkdir": mock_mkdir,
            "read_text": mock_read_text,
            "is_file": mock_is_file,
            "exists": mock_exists,
            "is_dir": mock_is_dir,
        }

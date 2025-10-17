# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import Any

import pytest

from escapist.exceptions import DataLoadError, FileWriteError
from escapist.utils import load_json, write_output


@pytest.fixture
def valid_dict() -> dict[str, Any]:
    return {"key": "value"}


@pytest.fixture
def valid_json_string() -> str:
    return '{"key": "value"}'


class TestWriteOutput:
    def test_write_output_success_with_str_path(self, mock_file_system) -> None:
        content = "Test content"
        output_file = "/fake/dir/output.txt"

        write_output(content, output_file)

        mock_file_system["mkdir"].assert_called_once_with(parents=True, exist_ok=True)
        mock_file_system["write_text"].assert_called_once_with(content, encoding="utf-8")

    def test_write_output_success_with_path_object(self, mock_file_system) -> None:
        content = "Another test"
        output_file = Path("/fake/dir/output.txt")

        write_output(content, output_file)

        mock_file_system["mkdir"].assert_called_once_with(parents=True, exist_ok=True)
        mock_file_system["write_text"].assert_called_once_with(content, encoding="utf-8")

    def test_write_output_raises_on_write_failure(self, mock_file_system) -> None:
        content = "Fail write"
        output_file = Path("/fake/dir/output.txt")

        mock_file_system["write_text"].side_effect = OSError("Disk full")

        with pytest.raises(FileWriteError) as exc_info:
            write_output(content, output_file)

        mock_file_system["mkdir"].assert_called_once_with(parents=True, exist_ok=True)
        mock_file_system["write_text"].assert_called_once()
        assert "Failed to write rendered output to file" in str(exc_info.value)

    def test_write_output_raises_on_mkdir_failure(self, mock_file_system) -> None:
        content = "Fail mkdir"
        output_file = Path("/fake/dir/output.txt")

        mock_file_system["mkdir"].side_effect = PermissionError("No permission")

        with pytest.raises(FileWriteError) as exc_info:
            write_output(content, output_file)

        mock_file_system["mkdir"].assert_called_once_with(parents=True, exist_ok=True)
        mock_file_system["write_text"].assert_not_called()
        assert "Failed to write rendered output to file" in str(exc_info.value)


class TestLoadJson:
    def test_load_json_success_with_empty(self):
        result = load_json(None)
        assert result == {}

    def test_load_json_success_with_dict(self, valid_dict):
        data = valid_dict
        result = load_json(data)
        assert result is data  # should return the same dict instance

    def test_load_json_success_with_str_path(self, mock_file_system, valid_dict, valid_json_string):
        path_str = "/fake/path.json"
        mock_file_system["is_file"].return_value = True
        mock_file_system["read_text"].return_value = valid_json_string

        result = load_json(path_str)

        mock_file_system["is_file"].assert_called_once()
        mock_file_system["read_text"].assert_called_once_with(encoding="utf-8")
        assert result == valid_dict

    def test_load_json_success_with_path_path(self, mock_file_system, valid_dict, valid_json_string):
        path_obj = Path("/fake/path.json")
        mock_file_system["is_file"].return_value = True
        mock_file_system["read_text"].return_value = valid_json_string

        result = load_json(path_obj)

        mock_file_system["is_file"].assert_called_once()
        mock_file_system["read_text"].assert_called_once_with(encoding="utf-8")
        assert result == valid_dict

    def test_load_json_success_with_dict_str(self, mock_file_system):
        json_str = '{"x": 10}'
        mock_file_system["is_file"].return_value = False
        mock_file_system["exists"].return_value = False

        result = load_json(json_str)

        mock_file_system["is_file"].assert_called_once()
        mock_file_system["exists"].assert_called_once()
        assert result == {"x": 10}

    def test_load_json_raises_on_file_not_found_failure(self, mock_file_system):
        mock_file_system["is_file"].return_value = True
        mock_file_system["read_text"].side_effect = FileNotFoundError("File missing")

        with pytest.raises(DataLoadError) as exc_info:
            load_json("/fake/missing.json")

        assert "Error loading JSON from file" in str(exc_info.value)
        mock_file_system["is_file"].assert_called_once()
        mock_file_system["read_text"].assert_called_once()

    def test_load_json_raises_on_file_not_an_file(self, mock_file_system):
        mock_file_system["is_file"].return_value = False
        mock_file_system["exists"].return_value = True

        with pytest.raises(DataLoadError) as exc_info:
            load_json("/fake/some_dir")

        assert "exists but is not a regular file" in str(exc_info.value)
        mock_file_system["is_file"].assert_called_once()
        mock_file_system["exists"].assert_called_once()

    def test_load_json_raises_on_file_not_a_valid_json_failure(self, mock_file_system):
        mock_file_system["is_file"].return_value = True
        mock_file_system["read_text"].return_value = "[1, 2, 3]"  # valid JSON but not dict

        with pytest.raises(DataLoadError) as exc_info:
            load_json("/fake/list.json")

        assert "did not produce a dictionary" in str(exc_info.value)
        mock_file_system["is_file"].assert_called_once()
        mock_file_system["read_text"].assert_called_once()

    def test_load_json_raises_on_str_not_a_valid_json_failure(self):
        invalid_json = '{"key": value without quotes}'
        with pytest.raises(DataLoadError) as exc_info:
            load_json(invalid_json)
        assert "Error decoding JSON string" in str(exc_info.value)

    def test_load_json_raises_on_str_json_not_a_dict(self):
        json_list_str = '["a", "b", "c"]'  # valid JSON but a list, not dict
        with pytest.raises(DataLoadError) as exc_info:
            load_json(json_list_str)
        assert "did not decode into a dictionary" in str(exc_info.value)

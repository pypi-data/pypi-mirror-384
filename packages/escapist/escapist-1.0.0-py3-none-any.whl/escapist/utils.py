# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


import json
import logging
from pathlib import Path
from typing import Any

from escapist.exceptions import DataLoadError, FileWriteError

logger = logging.getLogger(__name__)


def write_output(content: str, output_file: str | Path) -> None:
    """
    Write the provided content to the specified output file.

    This function ensures that the parent directory of the output file exists,
    creating it if necessary, before writing the content with UTF-8 encoding.

    Args:
        content (str): The string content to write to the file.
        output_file (str | Path): The file path (string or Path) where content will be written.

    Raises:
        FileWriteError: If writing to the output file or creating directories fails.
    """
    output_path = Path(output_file)
    try:
        logger.debug(f"Ensuring directory exists: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Writing output to: {output_path}")
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Successfully wrote output to: {output_path}")
    except Exception as exc:
        logger.error(f"Failed to write output to {output_path}: {exc}", exc_info=True)
        raise FileWriteError(f"Failed to write rendered output to file: {output_path}") from exc


def load_json(data: dict[str, Any] | str | Path | None) -> dict[str, Any]:
    """
    Load JSON data from a dictionary, JSON string, or a file path.

    Args:
        data: A dict, JSON string, file path, or None.

    Returns:
        A dictionary loaded from the input data.

    Raises:
        DataLoadError: If loading fails or data is invalid.
    """
    if data is None:
        logger.debug("No input data provided; returning empty dictionary.")
        return {}

    if isinstance(data, dict):
        logger.debug("Input is already a dictionary; returning it unchanged.")
        return data

    path = Path(data)
    if path.is_file():
        logger.debug(f"Attempting to load JSON from file: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            loaded_data = json.loads(content)
            if not isinstance(loaded_data, dict):
                logger.error(f"JSON content in file {path} did not produce a dictionary.")
                raise DataLoadError(f"JSON content in file {path} did not produce a dictionary.")
            return loaded_data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read or decode JSON from file {path}: {e}", exc_info=True)
            raise DataLoadError(f"Error loading JSON from file '{path}': {e}") from e

    if path.exists():
        logger.error(f"Path '{path}' exists but is not a regular file.")
        raise DataLoadError(f"Path '{path}' exists but is not a regular file.")

    logger.debug("Input is not a file; attempting to parse input as JSON string.")
    try:
        loaded_data = json.loads(str(data))
        if not isinstance(loaded_data, dict):
            logger.error("JSON string did not decode into a dictionary.")
            raise DataLoadError("JSON string did not decode into a dictionary.")
        return loaded_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON string input: {e}", exc_info=True)
        raise DataLoadError(f"Error decoding JSON string: {e}") from e

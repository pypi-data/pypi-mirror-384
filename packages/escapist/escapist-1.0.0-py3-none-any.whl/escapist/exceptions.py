# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


class EscapistError(Exception):
    """Base exception for all Escapist-related errors.

    Catching this exception will handle any error raised by the library,
    allowing for broad error handling when the specific cause is not important.
    """


class DataLoadError(EscapistError):
    """Raised when an error occurs during data loading or parsing.

    This includes issues with loading JSON from a file or string, or
    encountering an unsupported data type for the input.
    """


class FileWriteError(EscapistError):
    """Raised when an error occurs while writing rendered output to a file.

    This may happen due to issues such as insufficient file system permissions,
    invalid file paths, missing directories, or other I/O-related errors that
    prevent successful writing of the output content.
    """


class InvalidTemplateError(EscapistError):
    """Raised when a template path is invalid.

    This exception is raised when the template source is a path that exists
    but is not a file (e.g., it is a directory), or when a template string
    is ambiguous with a file path.
    """


class InvalidTemplateSyntaxError(EscapistError):
    """Raised when a template contains invalid Jinja syntax.

    This exception is triggered when the Jinja2 engine encounters a syntax error
    while parsing the template string or file. Common causes include unmatched
    tags, invalid expressions, or unsupported Jinja constructs.
    """

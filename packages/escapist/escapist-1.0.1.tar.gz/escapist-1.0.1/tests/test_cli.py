# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


import builtins
import logging
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from jinja2 import UndefinedError

from escapist.cli import escapist
from escapist.exceptions import (
    DataLoadError,
    FileWriteError,
    InvalidTemplateError,
    InvalidTemplateSyntaxError,
)

EXCEPTION_CASES = [
    (DataLoadError, 1, "Failed to load settings or data"),
    (InvalidTemplateError, 2, "Template path exists but is not a file"),
    (UndefinedError, 3, "Template contains undefined variables"),
    (builtins.RuntimeError, 4, "Template loading or rendering error"),
    (FileWriteError, 5, "Failed to write rendered output to file"),
    (InvalidTemplateSyntaxError, 6, "Syntax error in the template"),
    (builtins.Exception, 99, "Unexpected error"),
]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_renderer():
    with patch("escapist.cli.Escapist") as mock:
        instance = mock.return_value
        instance.load_template.return_value = None
        instance.render.return_value = "rendered content"
        yield mock


@pytest.fixture
def mock_progressbar():
    class DummyProgressBar:
        def __init__(self, iterable, **kwargs):
            self.iterable = iterable

        def __enter__(self):
            return iter(self.iterable)

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    with patch(
        "click.progressbar", side_effect=lambda iterable, **kwargs: DummyProgressBar(iterable, **kwargs)
    ) as mock_pb:
        yield mock_pb


@pytest.fixture
def mock_templates():
    """Mock template files returned by Path.glob()."""
    tpl1 = MagicMock()
    tpl1.name = "index.html"
    tpl1.is_file.return_value = True
    tpl1.with_suffix.return_value = tpl1

    tpl2 = MagicMock()
    tpl2.name = "about.html"
    tpl2.is_file.return_value = True
    tpl2.with_suffix.return_value = tpl2

    return [tpl1, tpl2]


class TestEscapistCLI:
    def _invoke(self, runner, args):
        result = runner.invoke(escapist, args)
        assert result.exit_code == 0
        return result

    @pytest.mark.parametrize(
        "args, expected_output",
        [
            (["--help"], "Jinja2 template rendering CLI"),
            (["--version"], "escapist"),
            ([], ""),  # No specific output expected, just ensure no error
        ],
    )
    def test_cli_basic_outputs(self, runner, args, expected_output):
        result = self._invoke(runner, args)
        if expected_output:
            assert expected_output.lower() in result.output.lower()

    def test_verbose_flag_emits_debug_logs(self, runner, caplog):
        caplog.set_level(logging.DEBUG)  # Capture debug logs when verbose

        self._invoke(runner, ["--verbose"])

        debug_logs = [record for record in caplog.records if record.levelno == logging.DEBUG]
        assert any("verbose mode enabled" in record.message.lower() for record in debug_logs)

    def test_no_verbose_flag_no_debug_logs(self, runner, caplog):
        caplog.set_level(logging.INFO)  # Ignore debug logs when not verbose

        self._invoke(runner, [])

        debug_logs = [record for record in caplog.records if record.levelno == logging.DEBUG]
        assert not debug_logs


class TestRenderCmdWithoutVerbose:
    def test_output_file_exists_without_force_exits(self, runner, mock_file_system):
        mock_file_system["is_file"].return_value = True
        result = runner.invoke(
            escapist,
            ["render", "template.j2", "-o", "output.txt"],
            obj={"verbose": False},
        )
        assert result.exit_code == 1
        assert "Error: Output file already exists" in result.output
        assert "Use --force to overwrite" in result.output

    def test_successful_render_prints_to_stdout(self, runner, mock_renderer):
        mock_renderer.return_value.render.return_value = "rendered content"
        result = runner.invoke(
            escapist,
            ["render", "template.j2"],
            obj={"verbose": False},
        )
        assert result.exit_code == 0
        assert "rendered content" in result.output

    def test_successful_render_writes_to_file(self, runner, mock_renderer, mock_file_system):
        mock_file_system["is_file"].return_value = False
        mock_renderer.return_value.render.return_value = None
        result = runner.invoke(
            escapist,
            ["render", "template.j2", "-o", "output.txt", "-f"],
            obj={"verbose": False},
        )
        assert result.exit_code == 0
        assert "✓ Successfully written to: output.txt" in result.output

    @pytest.mark.parametrize("exc, exit_code, err_msg", EXCEPTION_CASES)
    def test_render_exceptions(self, runner, mock_renderer, exc, exit_code, err_msg):
        mock_renderer.return_value.render.side_effect = exc("error occurred")
        result = runner.invoke(
            escapist,
            ["render", "template.j2"],
            obj={"verbose": False},
        )
        assert result.exit_code == exit_code
        assert err_msg in result.output


class TestRenderCmdWithVerbose:
    def test_verbose_debug_logs_emitted(self, runner, mock_renderer, caplog):
        mock_renderer.return_value.render.return_value = "rendered content"
        caplog.set_level("DEBUG")
        result = runner.invoke(
            escapist,
            ["--verbose", "render", "template.j2"],
            obj={"verbose": True},
        )
        assert result.exit_code == 0
        # Check some debug logs about inputs and completion
        debug_msgs = [rec.message.lower() for rec in caplog.records if rec.levelname == "DEBUG"]
        assert any("template path" in msg for msg in debug_msgs)
        assert any("template rendering completed" in msg for msg in debug_msgs)

    @pytest.mark.parametrize("exc, exit_code, err_msg", EXCEPTION_CASES)
    def test_render_exceptions_verbose(self, runner, mock_renderer, caplog, exc, exit_code, err_msg):
        mock_renderer.return_value.render.side_effect = exc("error occurred")
        caplog.set_level("DEBUG")
        result = runner.invoke(
            escapist,
            ["--verbose", "render", "template.j2"],
            obj={"verbose": True},
        )
        assert result.exit_code == exit_code
        assert err_msg in result.output
        if exit_code == 99:
            # For generic exceptions, should log traceback in verbose mode
            [
                rec.message
                for rec in caplog.records
                if "traceback" in rec.message.lower() or "error" in rec.message.lower()
            ]
            assert any("traceback" in rec.message.lower() or "error" in rec.message.lower() for rec in caplog.records)


class TestBatchCmd:
    def test_batch_success(self, runner, mock_renderer, mock_file_system, mock_progressbar, mock_templates):
        mock_file_system["is_dir"].return_value = True
        mock_file_system["exists"].return_value = False

        with patch("pathlib.Path.glob", return_value=mock_templates):
            result = runner.invoke(
                escapist,
                ["batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": False},
            )

        assert result.exit_code == 0
        assert "✓ Successfully rendered 2 template(s)" in result.output

    def test_template_dir_does_not_exist(self, runner, mock_file_system):
        mock_file_system["is_dir"].return_value = False

        result = runner.invoke(
            escapist,
            ["batch", "/invalid/dir", "-o", "/fake/output"],
            obj={"verbose": False},
        )

        assert result.exit_code == 1
        assert "Template directory does not exist" in result.output

    def test_no_templates_found(self, runner, mock_file_system):
        mock_file_system["is_dir"].return_value = True

        with patch("pathlib.Path.glob", return_value=[]):
            result = runner.invoke(
                escapist,
                ["batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": False},
            )

        assert result.exit_code == 0
        assert "⚠ No templates found matching pattern" in result.output

    def test_output_files_exist_without_force(self, runner, mock_file_system, mock_templates):
        mock_file_system["is_dir"].return_value = True
        mock_file_system["exists"].return_value = True

        with patch("pathlib.Path.glob", return_value=mock_templates):
            result = runner.invoke(
                escapist,
                ["batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": False},
            )

        assert result.exit_code == 2
        assert "output file(s) already exist" in result.output
        assert "Use --force to overwrite" in result.output

    def test_batch_render_exception(self, runner, mock_renderer, mock_file_system, mock_progressbar, mock_templates):
        mock_file_system["is_dir"].return_value = True
        mock_file_system["exists"].return_value = False
        mock_renderer.return_value.render.side_effect = Exception("Render failed")

        with patch("pathlib.Path.glob", return_value=mock_templates):
            result = runner.invoke(
                escapist,
                ["batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": False},
            )

        assert result.exit_code == -1
        assert "✗ Failed to render 2 template(s)" in result.output
        assert "Render failed" in result.output


class TestBatchCmdVerbose:
    def test_verbose_logs_on_success(
        self, runner, mock_renderer, mock_file_system, mock_progressbar, mock_templates, caplog
    ):
        mock_file_system["is_dir"].return_value = True
        mock_file_system["exists"].return_value = False

        with patch("pathlib.Path.glob", return_value=mock_templates):
            caplog.set_level(logging.DEBUG)
            result = runner.invoke(
                escapist,
                ["--verbose", "batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": True},
            )

        assert result.exit_code == 0
        # Check for verbose debug logs about found templates, output dir, etc.
        debug_msgs = [rec.message for rec in caplog.records if rec.levelno == logging.DEBUG]

        assert any("found 2 template(s)" in msg.lower() for msg in debug_msgs)
        assert any("output directory" in msg.lower() for msg in debug_msgs)
        assert any("output file extension" in msg.lower() for msg in debug_msgs)
        assert any("data file" in msg.lower() for msg in debug_msgs)
        assert any("settings file" in msg.lower() for msg in debug_msgs)

        # Also check that individual templates were rendered (debug logs for each render)
        assert any("rendered" in msg.lower() for msg in debug_msgs)

        # Final success message
        assert "✓ Successfully rendered 2 template(s)" in result.output

    def test_verbose_logs_on_partial_failure(
        self, runner, mock_renderer, mock_file_system, mock_progressbar, mock_templates, caplog
    ):
        mock_file_system["is_dir"].return_value = True
        mock_file_system["exists"].return_value = False

        # Fail on rendering one template to trigger error output and verbose logs
        def side_effect(*args, **kwargs):
            # Fail on first call, succeed otherwise
            if not hasattr(side_effect, "called"):
                side_effect.called = True  # type: ignore[attr-defined]
                raise Exception("Render failure")
            return "rendered content"

        mock_renderer.return_value.render.side_effect = side_effect

        with patch("pathlib.Path.glob", return_value=mock_templates):
            caplog.set_level(logging.DEBUG)
            result = runner.invoke(
                escapist,
                ["--verbose", "batch", "/fake/templates", "-o", "/fake/output"],
                obj={"verbose": True},
            )

        assert result.exit_code == -1
        # Error message shown for failure
        assert "✗ Failed to render" in result.output
        assert "Render failure" in result.output

        # Verbose debug logs include the start info and render attempts
        debug_msgs = [rec.message for rec in caplog.records if rec.levelno == logging.DEBUG]
        assert any("found 2 template(s)" in msg.lower() for msg in debug_msgs)
        assert any("output directory" in msg.lower() for msg in debug_msgs)
        assert any("rendered" in msg.lower() or "failed to render" in msg.lower() for msg in debug_msgs)

    def test_verbose_logs_when_template_dir_missing(self, runner, caplog, mock_file_system):
        mock_file_system["is_dir"].return_value = False

        caplog.set_level(logging.DEBUG)
        result = runner.invoke(
            escapist,
            ["--verbose", "batch", "/missing/templates", "-o", "/fake/output"],
            obj={"verbose": True},
        )
        assert result.exit_code == 1
        assert "Template directory does not exist" in result.output

        debug_logs = [rec for rec in caplog.records if rec.levelno == logging.DEBUG]
        # Only the initial verbose mode enabled log should be present
        assert len(debug_logs) == 1
        assert "verbose mode enabled" in debug_logs[0].message.lower()

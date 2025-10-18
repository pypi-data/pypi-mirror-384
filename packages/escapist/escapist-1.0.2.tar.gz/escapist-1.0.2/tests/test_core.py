# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


from unittest.mock import MagicMock, patch

import pytest
from jinja2 import UndefinedError

from escapist.core import Escapist
from escapist.exceptions import InvalidTemplateError, InvalidTemplateSyntaxError


class TestEscapistInitialization:
    def test_init_with_basic_settings(self):
        settings = {
            "environment": {"trim_blocks": True},
            "autoescape": False,
            "escape_sequences": {"&": "&amp;"},
            "globals": {"company": "TestCo"},
            "treat_missing_variable_as_missing": True,
        }

        renderer = Escapist(settings=settings)
        assert renderer._env.trim_blocks is True
        assert renderer._env.globals["company"] == "TestCo"
        assert renderer._env.autoescape is False

    def test_autoescape_dict_calls_select_autoescape(self):
        settings = {"autoescape": {"enabled_extensions": ["html", "xml"], "default_for_string": True, "default": False}}

        with patch("escapist.core.select_autoescape") as mock_select:
            Escapist(settings=settings)

        mock_select.assert_called_once_with(enabled_extensions=["html", "xml"], default_for_string=True, default=False)


class TestTemplateLoading:
    def test_load_template_from_string(self):
        renderer = Escapist()
        template_str = "Hello {{ name }}"
        renderer.load_template(template_str)

        assert renderer.is_template_loaded

        # Replace invalid `.source` access with a real render check
        result = renderer.render(data={"name": "Tester"})
        assert result == "Hello Tester"

    def test_load_template_from_file_mocked(self, mock_file_system):
        # Mock file behavior
        mock_file_system["is_file"].return_value = True
        mock_file_system["exists"].return_value = True

        # Simulate a file template called "template.txt" in /fake/path
        fake_path = "/fake/path/template.txt"

        # Patch get_template to return a mock template object
        mock_template = MagicMock()
        with patch("jinja2.Environment.get_template", return_value=mock_template):
            renderer = Escapist()
            renderer.load_template(fake_path)

        assert renderer.is_template_loaded

    def test_invalid_template_syntax(self):
        renderer = Escapist()
        with pytest.raises(InvalidTemplateSyntaxError):
            renderer.load_template("{{ broken_template")

    def test_template_source_exists_but_not_a_file_raises(self, mock_file_system):
        mock_file_system["exists"].return_value = True
        mock_file_system["is_file"].return_value = False  # Not a file

        renderer = Escapist()

        with pytest.raises(InvalidTemplateError) as exc_info:
            renderer.load_template("/some/existing/directory")

        assert "exists but is not a file" in str(exc_info.value)


class TestTemplateRendering:
    def test_render_template_with_data(self):
        renderer = Escapist()
        renderer.load_template("Welcome {{ name }}")
        output = renderer.render(data={"name": "Alice"})
        assert output == "Welcome Alice"

    def test_render_with_escape_sequences(self):
        settings = {"escape_sequences": {"<": "&lt;", ">": "&gt;"}}
        renderer = Escapist(settings)
        renderer.load_template("{{ html }}")
        result = renderer.render(data={"html": "<p>test</p>"})
        assert result == "&lt;p&gt;test&lt;/p&gt;"

    def test_render_to_output_file(self, mock_file_system):
        mock_file_system["is_file"].return_value = False
        mock_file_system["exists"].return_value = False

        # Prepare template
        renderer = Escapist()
        renderer.load_template("Hello {{ name }}")
        renderer.render(data={"name": "file test"}, output_file="output.txt")

        # Verify write_output was called via Path.write_text
        mock_file_system["write_text"].assert_called_once()
        args, _ = mock_file_system["write_text"].call_args
        assert "Hello file test" in args[0]

    def test_render_without_loading_template_raises(self):
        renderer = Escapist()
        with pytest.raises(RuntimeError):
            renderer.render(data={"some": "data"})

    def test_render_raises_on_missing_variable_with_strict_setting(self):
        settings = {"treat_missing_variable_as_missing": True}
        renderer = Escapist(settings)
        renderer.load_template("{{ required }}")

        with pytest.raises(UndefinedError):
            renderer.render(data={})  # missing 'required'

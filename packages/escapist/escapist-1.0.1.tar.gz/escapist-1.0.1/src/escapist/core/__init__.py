# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT


import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateSyntaxError,
    Undefined,
    select_autoescape,
)

from escapist.exceptions import InvalidTemplateError, InvalidTemplateSyntaxError
from escapist.utils import load_json, write_output

logger = logging.getLogger(__name__)


class Escapist:
    """
    A class for rendering Jinja2 templates from various sources with configurable settings.

    The environment is configured and created on initialization. The template can
    then be loaded via a public method and rendered using a separate public method.
    """

    def __init__(self, settings: dict[str, Any] | str | Path | None = None) -> None:
        """
        Initializes the Jinja environment based on the provided settings.

        Args:
            settings: The Jinja environment settings, which can be a dict,
                      a JSON string, or a file path to a JSON file.

        Raises:
            DataLoadError: If settings loading fails.
        """
        logger.debug(f"Initializing Escapist with settings: {settings}")
        self._env = self._configure_env(settings)
        self._template: Any = None
        self._template_source: str | None = None
        logger.debug("Jinja environment successfully configured.")

    @property
    def is_template_loaded(self) -> bool:
        """Check if a template has been loaded."""
        return self._template is not None

    @property
    def template_source(self) -> str | None:
        """Get the source of the currently loaded template."""
        return self._template_source

    def load_template(self, template_source: str | Path) -> None:
        """
        Loads and compiles the Jinja template based on its source.

        Args:
            template_source: The template source, either a file path or a string.

        Raises:
            InvalidTemplateError: If the source path is invalid.
            InvalidTemplateSyntaxError: If the the jinja syntax is wrong.
            DataLoadError: If settings loading fails.
        """
        logger.debug(f"Loading template from source: {template_source}")
        template_path = Path(template_source)

        try:
            if template_path.is_file():
                template_dir = template_path.parent
                template_name = template_path.name

                logger.debug(f"Using FileSystemLoader for directory: {template_dir}")
                # Use a FileSystemLoader for file-based templates
                self._env.loader = FileSystemLoader(str(template_dir))
                self._template = self._env.get_template(template_name)

            elif not template_path.exists():
                logger.debug("Template source does not exist as a file; treating as string template.")
                # Use no loader for string templates
                self._env.loader = None
                self._template = self._env.from_string(str(template_source))
            else:
                logger.error(f"Template source exists but is not a file: {template_source}")
                raise InvalidTemplateError(f"Template source '{template_source}' exists but is not a file.")
            self._template_source = str(template_path)
            logger.info(f"Template loaded successfully from: {self._template_source}")

        except TemplateSyntaxError as e:
            logger.error(f"Invalid Jinja template syntax: {e}", exc_info=True)
            raise InvalidTemplateSyntaxError(f"Invalid template jinja syntax: {e}") from e

    def render(
        self,
        data: dict[str, Any] | str | Path | None = None,
        output_file: str | Path | None = None,
    ) -> str:
        """
        Renders the currently loaded template with the provided data.

        Args:
            data: The data to use for rendering, which can be a dict,
                  a JSON string, or a file path to a JSON file.
            output_file: Optional path to a file where the rendered output will be saved.

        Returns:
            The rendered template as a string.

        Raises:
            RuntimeError: If no template has been loaded before rendering.
            DataLoadError: If data loading from JSON fails.
            FileWriteError: If fails to write rendered template to file
            UndefinedError: If missing any variables

        """
        if self._template is None:
            logger.error("Render called without loading a template first.")
            raise RuntimeError("No template has been loaded. Call load_template() first.")

        logger.debug(f"Loading data for rendering: {data}")
        loaded_data = load_json(data=data)

        logger.debug("Rendering template with loaded data.")
        rendered_output = str(self._template.render(loaded_data))

        if output_file:
            logger.debug(f"Writing rendered output to file: {output_file}")
            write_output(rendered_output, output_file)
            logger.info(f"Rendered output successfully written to: {output_file}")
            return str(output_file)

        logger.debug("Rendered output generated (no file output requested).")
        return rendered_output

    def _configure_env(self, settings_source: dict[str, Any] | str | Path | None) -> Environment:
        """Configures and returns the Jinja Environment based on settings."""
        logger.debug(f"Configuring Jinja environment with settings source: {settings_source}")
        settings_json = load_json(data=settings_source)

        env_kwargs = settings_json.get("environment", {})

        autoescape_setting = settings_json.get("autoescape")
        if isinstance(autoescape_setting, bool):
            env_kwargs["autoescape"] = autoescape_setting
            logger.debug(f"Autoescape set to bool value: {autoescape_setting}")
        elif isinstance(autoescape_setting, dict):
            env_kwargs["autoescape"] = select_autoescape(**autoescape_setting)
            logger.debug(f"Autoescape configured with dict: {autoescape_setting}")

        env_kwargs["finalize"] = self._create_finalize(settings_json.get("escape_sequences", {}))
        env_kwargs["undefined"] = (
            StrictUndefined if settings_json.get("treat_missing_variable_as_missing", False) else Undefined
        )
        env_kwargs["loader"] = None

        env = Environment(**env_kwargs)  # noqa: S701
        env.globals.update(settings_json.get("globals", {}))

        logger.debug("Jinja environment configured with kwargs: %s", env_kwargs)
        return env

    @staticmethod
    def _create_finalize(escape_sequences: dict[str, str]) -> Callable[[Any], Any]:
        """
        Creates a finalize function based on a static map of escape sequences.
        """

        def finalize(value: Any) -> Any:
            if isinstance(value, str):
                for old, new in escape_sequences.items():
                    value = value.replace(old, new)
            return value

        return finalize

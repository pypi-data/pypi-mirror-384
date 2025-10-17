# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT

import logging
import sys
import traceback
from pathlib import Path

import click
from click import progressbar
from jinja2 import UndefinedError

from escapist.__version__ import __version__
from escapist.core import Escapist
from escapist.exceptions import (
    DataLoadError,
    FileWriteError,
    InvalidTemplateError,
    InvalidTemplateSyntaxError,
)

logger = logging.getLogger(__name__)

# ============================================================================
# CLI Group
# ============================================================================


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option(version=__version__, prog_name="escapist")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output for debugging",
)
@click.pass_context
def escapist(ctx: click.Context, verbose: bool) -> None:
    """
    Jinja2 template rendering CLI.

    Render templates with JSON data and custom settings.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stderr,
    )

    if verbose:
        logger.debug("Verbose mode enabled")


# ============================================================================
# Render Command
# ============================================================================


@escapist.command(name="render")
@click.argument("template", type=click.Path(path_type=Path))
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to JSON data file.",
)
@click.option(
    "--settings",
    "-s",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to JSON settings file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (prints to stdout if not specified).",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite output file if it exists.",
)
@click.pass_context
def render_cmd(  # noqa: PLR0913,PLR0912
    ctx: click.Context,
    template: Path,
    data: Path | None,
    settings: Path | None,
    output: Path | None,
    force: bool,
) -> None:
    """
    Render a Jinja2 template.

    TEMPLATE is the path to the template file to be processed.
    """
    verbose = ctx.obj.get("verbose", False)

    if output and output.is_file() and not force:
        click.echo(
            click.style(f"Error: Output file already exists: {output}", fg="red"),
            err=True,
        )
        click.echo("Use --force to overwrite the existing file.", err=True)
        sys.exit(1)

    if verbose:
        logger.debug(f"Template path: {template}")
        logger.debug(f"Data file: {data if data else 'None'}")
        logger.debug(f"Settings file: {settings if settings else 'Default'}")
        logger.debug(f"Output: {output if output else 'Standard output'}")

    try:
        renderer = Escapist(settings=settings)
        renderer.load_template(template_source=template)
        rendered = renderer.render(data=data, output_file=output)

        if output:
            click.echo(
                click.style(f"✓ Successfully written to: {output}", fg="green"),
                err=True,
            )
        else:
            click.echo(rendered)

        if verbose:
            logger.debug("Template rendering completed successfully.")
    except DataLoadError as e:
        click.echo(
            click.style(f"ERROR: Failed to load settings or data: {e}", fg="red"),
            err=True,
        )
        sys.exit(1)
    except InvalidTemplateError as e:
        click.echo(
            click.style(f"ERROR: Template path exists but is not a file: {e}", fg="red"),
            err=True,
        )
        sys.exit(2)
    except UndefinedError as e:
        click.echo(
            click.style(
                f"ERROR: Template contains undefined variables: {e}",
                fg="red",
            ),
            err=True,
        )
        sys.exit(3)
    except RuntimeError as e:
        click.echo(
            click.style(f"ERROR: Template loading or rendering error: {e}", fg="red"),
            err=True,
        )
        sys.exit(4)
    except FileWriteError as e:
        click.echo(
            click.style(f"ERROR: Failed to write rendered output to file: {e}", fg="red"),
            err=True,
        )
        sys.exit(5)
    except InvalidTemplateSyntaxError as e:
        click.echo(
            click.style(f"ERROR: Syntax error in the template: {e}", fg="red"),
            err=True,
        )
        sys.exit(6)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg="red"), err=True)
        if verbose:
            logger.debug(traceback.format_exc())
        sys.exit(99)


# ============================================================================
# Batch Render Command
# ============================================================================


@escapist.command(name="batch")
@click.argument("template_dir", type=click.Path(path_type=Path))
@click.option(
    "--pattern",
    "-p",
    type=str,
    default="*",
    help="File pattern to match (e.g., '*.html', '*.xml')",
)
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to JSON data file",
)
@click.option(
    "--settings",
    "-s",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to JSON settings file",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory",
)
@click.option(
    "--output-file-ext",
    "-e",
    type=str,
    help="Output file extension (e.g., 'html')",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite output files if they exist",
)
@click.pass_context
def batch_cmd(  # noqa: PLR0913
    ctx: click.Context,
    template_dir: Path,
    pattern: str,
    data: Path | None,
    settings: Path | None,
    output_dir: Path,
    output_file_ext: str | None,
    force: bool,
) -> None:
    """
    Render multiple templates in batch.

    TEMPLATE_DIR is the path to the folder containing templates.
    """
    verbose = ctx.obj.get("verbose", False)

    template_dir = Path(template_dir)
    if not template_dir.is_dir():
        click.echo(
            click.style(f"✗ Template directory does not exist: {template_dir}", fg="red"),
            err=True,
        )
        sys.exit(1)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    template_files = [tpl for tpl in template_dir.glob(pattern) if tpl.is_file()]

    if not template_files:
        click.echo(
            click.style(f"⚠ No templates found matching pattern: {pattern}", fg="yellow"),
            err=True,
        )
        sys.exit(0)

    if verbose:
        logger.debug(f"Found {len(template_files)} template(s) matching pattern '{pattern}'")
        logger.debug(f"Output directory: {output_dir}")
        logger.debug(f"Output file extension: {output_file_ext if output_file_ext else 'same as source'}")
        logger.debug(f"Data file: {data if data else 'None'}")
        logger.debug(f"Settings file: {settings if settings else 'Default'}")

    templates = {tpl.name: tpl for tpl in template_files}

    if not force:
        existing_files = [output_dir / name for name in templates if (output_dir / name).exists()]
        if existing_files:
            click.echo(
                click.style(f"✗ {len(existing_files)} output file(s) already exist:", fg="red"),
                err=True,
            )
            for f in existing_files:
                click.echo(f"  {f}", err=True)
            click.echo("Use --force to overwrite existing files.", err=True)
            sys.exit(2)

    success_count = 0
    error_count = 0

    with progressbar(templates.items(), label="Rendering templates", length=len(templates)) as bar:
        renderer = Escapist(settings=settings)

        for output_name, template_path in bar:
            output_path = output_dir / output_name
            if output_file_ext:
                output_path = output_path.with_suffix(f".{output_file_ext}")

            try:
                renderer.load_template(template_source=template_path)
                renderer.render(data=data, output_file=output_path)
                success_count += 1
                if verbose:
                    logger.debug(f"Rendered {template_path} → {output_path}")
            except Exception as e:
                error_count += 1
                click.echo(
                    click.style(f"✗ Failed to render {template_path}: {e}", fg="red"),
                    err=True,
                )

    click.echo(
        click.style(f"✓ Successfully rendered {success_count} template(s)", fg="green"),
        err=True,
    )
    if error_count > 0:
        click.echo(
            click.style(f"✗ Failed to render {error_count} template(s)", fg="red"),
            err=True,
        )
        sys.exit(-1)

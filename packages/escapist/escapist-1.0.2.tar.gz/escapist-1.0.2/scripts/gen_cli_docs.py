#!/usr/bin/env python3
import importlib
import re
from pathlib import Path

import click
import mkdocs_gen_files

# Paths
ROOT_DIR = Path(__file__).parent.parent.resolve()
DOCS_DIR = ROOT_DIR / "docs"  # This is the input root
CLI_PATTERN = re.compile(r"^!!!cli\s+([\w\.]+):(\w+)\s*$", re.MULTILINE)


def format_command_help(cmd: click.Command, prefix="") -> str:
    """Recursively format the Click command and its subcommands as markdown."""
    full_cmd = f"{prefix} {cmd.name}".strip()
    ctx = click.Context(cmd, info_name=full_cmd)
    parts = [f"## `{full_cmd}`\n", "```", cmd.get_help(ctx), "```\n"]
    if isinstance(cmd, click.Group):
        for sub_name in cmd.list_commands(ctx):
            sub_cmd = cmd.get_command(ctx, sub_name)
            if sub_cmd:
                parts.append(format_command_help(sub_cmd, full_cmd))
    return "\n".join(parts)


def generate_cli_docs(module_path: str, command_name: str) -> str:
    """Import the CLI command and generate help markdown."""
    module = importlib.import_module(module_path)
    cli_cmd = getattr(module, command_name)
    return format_command_help(cli_cmd)


def process_markdown(md_path: Path) -> str:
    """Read markdown, replace all !!!cli directives with generated docs."""
    content = md_path.read_text(encoding="utf-8")

    def replace_cli(match):
        module_path, command_name = match.groups()
        try:
            return generate_cli_docs(module_path, command_name)
        except Exception as e:
            return f"> **Error:** Could not generate CLI docs for `{module_path}:{command_name}`: {e}"

    return CLI_PATTERN.sub(replace_cli, content)


def write_docs(original_path: Path, content: str) -> None:
    """Write the generated documentation to the MkDocs virtual file system."""
    # Compute the relative path from the docs folder
    rel_path = original_path.relative_to(DOCS_DIR)
    with mkdocs_gen_files.open(rel_path, "w") as f:
        f.write(content)


def main() -> None:
    """Find and process all markdown files with !!!cli directives."""
    for md_file in DOCS_DIR.rglob("*.md"):
        if "!!!cli" in md_file.read_text(encoding="utf-8"):
            new_content = process_markdown(md_file)
            write_docs(md_file, new_content)


main()

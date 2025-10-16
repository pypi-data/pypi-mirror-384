# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT

# ----------------------------
# Noxfile
# ----------------------------
import shutil
import sys
from pathlib import Path
from typing import Any

import nox  # type: ignore[import-untyped]

# ----------------------------
# Constants / Configuration
# ----------------------------
PYPROJECT_TOML: dict[str, Any] = nox.project.load_toml()
PYTHON_VERSIONS: list[str] = nox.project.python_versions(PYPROJECT_TOML)
DEFAULT_PYTHON_VERSION: str = PYTHON_VERSIONS[-1]

# ----------------------------
# Nox Options
# ----------------------------
nox.options.sessions = ["tests", "check"]
nox.options.reuse_existing_virtualenvs = True


# ----------------------------
# Helpers
# ----------------------------
def _get_optional_deps(group: str, pyproject: dict[str, Any] = PYPROJECT_TOML) -> list[str]:
    """Fetch dependencies for a given group from pyproject.toml."""
    try:
        return pyproject["project"]["optional-dependencies"][group]
    except KeyError as e:
        raise KeyError(f"Missing optional dependency group: '{group}' in pyproject.toml") from e


def _load_dotenv(path: str | Path = Path(".env")) -> dict[str, str]:
    """Load .env file as key-value pairs into a dict."""
    path = Path(path)
    if not str(path).endswith(".env"):
        raise ValueError(f"Provided path must end with '.env': {path}")

    if not path.exists():
        return {}

    env: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _draft_changelog(session: nox.Session) -> Path:
    """Generate a draft changelog using Towncrier for local preview."""
    draft_path = Path("docs/_draft_changelog.md")
    content = session.run("towncrier", "build", "--version", "Upcoming", "--draft", silent=True)
    if not content or "No significant changes" in content:
        return draft_path

    lines = content.splitlines()
    idx = next((i for i, line in enumerate(lines) if line.startswith("##")), None)
    if idx is not None:
        lines[idx] = "## Upcoming changes"
        content = "\n".join(lines[idx:])
    draft_path.write_text(content)
    return draft_path


# ----------------------------
# Optional Dependency Groups
# ----------------------------
TESTS_DEPS = _get_optional_deps("tests")
TYPES_DEPS = _get_optional_deps("types")
DOCS_DEPS = _get_optional_deps("docs")

# ----------------------------
# Sessions
# ----------------------------


@nox.session(python=PYTHON_VERSIONS)
def devenv(session: nox.Session) -> None:
    """
    Set up the full development environment.

    Installs the project in editable mode along with test, type, and doc dependencies.
    Displays Python path and virtual environment activation info for IDE setup.
    """
    session.env.update(_load_dotenv())

    # ────────────────────────────────────────────────
    session.log("")
    session.log("🔧 Setting up development environment...\n")

    session.log("📦 Upgrading pip...")
    session.run("python", "-m", "pip", "install", "--upgrade", "pip")

    session.log("📚 Installing project with dev dependencies (editable mode)...")
    session.install("-e", ".", *TESTS_DEPS, *TYPES_DEPS, *DOCS_DEPS, "nox")

    # ────────────────────────────────────────────────
    session.log("✅ Setup complete!\n")

    # Get Python path (used for IDE)
    python_path = shutil.which("python", path=str(session.virtualenv.bin)) or "Not found"
    session.log("")
    session.log(f"📍 Python interpreter path for IDEs:\n   {python_path}")
    session.log("")

    # Generate activation instructions
    venv_dir = session.virtualenv.location
    if sys.platform.startswith("win"):
        activate_cmd = f"{venv_dir}\\Scripts\\activate"
    else:
        activate_cmd = f"source {venv_dir}/bin/activate"

    session.log("")
    session.log(f"💡 To activate the virtual environment manually, run:\n   {activate_cmd}\n")
    session.log("🧪 You're now ready to run tests, type checks, and build docs!\n")
    session.log("")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """
    🧪 Run the test suite using pytest.

    Installs the project in editable mode with test dependencies and executes tests.
    Pass additional pytest arguments via `--`:
        nox -s tests -- -k "test_something"
    """
    session.log("🧪 Running test suite with pytest...\n")
    session.install("-e", ".", *TESTS_DEPS)
    session.run("pytest", *session.posargs, external=True)
    session.log("✅ Tests completed.\n")


@nox.session
def lint(session: nox.Session) -> None:
    """
    🧹 Run ruff check using configuration from pyproject.toml.
    """
    session.log("🧹 Running ruff linter...\n")
    session.install("ruff")
    session.run("ruff", "check", external=True)
    session.log("✅ Linting complete.\n")


@nox.session
def typecheck(session: nox.Session) -> None:
    """
    🧠 Run MyPy for static type checking.

    Ensures type safety across the codebase. Supports custom args:
        nox -s typecheck -- your_module.py
    """
    session.log("🧠 Running type checks with MyPy...\n")
    session.install("-e", ".", "mypy", *TESTS_DEPS, *TYPES_DEPS)
    session.run("mypy", "--install-types", "--non-interactive", *session.posargs, external=True)
    session.log("✅ Type checking complete.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def check(session: nox.Session) -> None:
    """
    ✅ Run both lint and typecheck sessions in one step.

    This is useful for CI or pre-push validation.
    """
    session.log("✅ Running lint and typecheck sessions...\n")
    session.notify("lint")
    session.notify("typecheck")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def build(session: nox.Session) -> None:
    """
    📦 Build the project distribution using Hatch.

    This creates source and wheel distributions under the `dist/` directory.
    """
    session.log("📦 Building distribution using Hatch...\n")
    session.install("hatch")
    session.run("python", "-m", "hatch", "build", external=True)
    session.log("\n✅ Build complete. Artifacts are available in the 'dist/' directory.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def changelog(session: nox.Session) -> None:
    """
    📝 Generate a changelog from fragments using Towncrier.

    Usage:
        nox -s changelog -- <version>

    Example:
        nox -s changelog -- 1.3.0
    """
    if not session.posargs:
        session.error("❌ Missing version argument for changelog (e.g., 1.2.3)")

    version = session.posargs[0]

    session.log(f"\n📝 Generating changelog for version: {version}...\n")
    session.install("towncrier")
    session.run("towncrier", "build", "--version", version, "--yes")
    session.log(f"\n✅ Changelog generated for version {version}.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def docs_serve(session: nox.Session) -> None:
    """
    🚀 Serve the documentation locally with MkDocs and auto-reload on changes.

    This session installs doc dependencies and generates a draft changelog if relevant.
    """
    session.log("📥 Installing documentation dependencies...\n")
    session.install(*DOCS_DEPS, ".")

    # Generate draft changelog if any
    draft_changelog = _draft_changelog(session)
    if draft_changelog.exists() and draft_changelog.read_text().strip():
        session.log("📝 Draft changelog generated for preview.")
    else:
        session.log("📝 No significant changes found for changelog draft.")

    session.log("🚀 Starting MkDocs server with auto-reload...\n")
    # `mkdocs serve` auto-reloads on file changes by default
    session.run("mkdocs", "serve", "--livereload", external=True)

    # Clean up draft changelog file after serve (if it exists)
    if draft_changelog.exists():
        draft_changelog.unlink()
        session.log("🧹 Cleaned up draft changelog.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def deploy_docs(session: nox.Session) -> None:
    """
    Deploy the documentation site to GitHub Pages using Mike.

    Usage:
        nox -s deploy_docs -- <version> [<alias>]

    Examples:
        nox -s deploy_docs -- 1.2.0 stable
        nox -s deploy_docs -- 1.2.0
    """
    session.install(*DOCS_DEPS, ".")

    version = session.posargs[0] if session.posargs else "dev"
    alias = session.posargs[1] if len(session.posargs) > 1 else None

    session.log(f"📚 Deploying docs for version: {version}")
    if alias:
        session.log(f"🔗 Using alias: {alias}")
        session.run("mike", "deploy", "--update-aliases", version, alias)
        session.run("mike", "set-default", alias)
    else:
        session.run("mike", "deploy", version)

    session.log("🚀 Documentation deployed successfully.")

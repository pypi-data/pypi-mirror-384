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
    content = session.run("towncrier", "build", "--version", "Upcoming", "--draft", silent=True, external=True)
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
    🔧 Set up the full development environment.

    Installs the project in editable mode along with all development extras:
    tests, type checking, and documentation dependencies.

    Useful for local development or onboarding.

    Example:
        nox -s devenv
        nox -s devenv-3.13

    After completion, activate the environment manually:
        source .nox/devenv-3-13/bin/activate  (on Unix)
        .nox\\devenv-3-13\\Scripts\\activate   (on Windows)
    """
    session.env.update(_load_dotenv())

    session.log("")
    session.log("🔧 Setting up development environment...\n")

    session.log("📦 Upgrading pip...")
    session.run("python", "-m", "pip", "install", "--upgrade", "pip", external=True)

    session.log("📚 Installing project with dev dependencies (editable mode)...")
    session.install("-e", ".", *TESTS_DEPS, *TYPES_DEPS, *DOCS_DEPS, "nox")

    session.log("✅ Setup complete!\n")

    python_path = shutil.which("python", path=str(session.virtualenv.bin)) or "Not found"
    session.log(f"📍 Python interpreter path for IDEs:\n   {python_path}")

    venv_dir = session.virtualenv.location
    if sys.platform.startswith("win"):
        activate_cmd = f"{venv_dir}\\Scripts\\activate"
    else:
        activate_cmd = f"source {venv_dir}/bin/activate"

    session.log(f"\n💡 To activate the virtual environment manually, run:\n   {activate_cmd}\n")
    session.log("🧪 You're now ready to run tests, type checks, and build docs!\n")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """
    🧪 Run the full test suite using pytest.

    Installs the project in editable mode and all test dependencies.
    You can pass additional pytest options via `--`.

    Examples:
        nox -s tests
        nox -s tests -- -k "test_core"
        nox -s tests -- --maxfail=1 -v
    """
    session.log("🧪 Running test suite with pytest...\n")
    session.install("-e", ".", *TESTS_DEPS)
    session.run("pytest", *session.posargs, external=True)
    session.log("✅ Tests completed.\n")


@nox.session
def lint(session: nox.Session) -> None:
    """
    🧹 Run code style and lint checks using Ruff.

    Uses configuration from pyproject.toml.
    Fails if style or import errors are found.

    Example:
        nox -s lint
    """
    session.log("🧹 Running ruff linter...\n")
    session.install("ruff")
    session.run("ruff", "check", external=True)
    session.log("✅ Linting complete.\n")


@nox.session
def typecheck(session: nox.Session) -> None:
    """
    🧠 Run MyPy static type checking.

    Ensures all modules conform to typing annotations and consistency.
    You can limit checks to specific modules or files.

    Examples:
        nox -s typecheck
        nox -s typecheck -- src/escapist/core
        nox -s typecheck -- src/escapist/cli/__init__.py
    """
    session.log("🧠 Running type checks with MyPy...\n")
    session.install("-e", ".", "mypy", *TESTS_DEPS, *TYPES_DEPS)
    session.run("mypy", "--install-types", "--non-interactive", *session.posargs, external=True)
    session.log("✅ Type checking complete.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def check(session: nox.Session) -> None:
    """
    ✅ Run both lint and typecheck sessions sequentially.

    Useful for quick validation before committing or pushing code.

    Example:
        nox -s check
    """
    session.log("✅ Running lint and typecheck sessions...\n")
    session.notify("lint")
    session.notify("typecheck")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def build(session: nox.Session) -> None:
    """
    📦 Build source and wheel distributions using Hatch.

    Produces build artifacts in the `dist/` directory.

    Example:
        nox -s build
    """
    session.log("📦 Building distribution using Hatch...\n")
    session.install("hatch")
    session.run("python", "-m", "hatch", "build", external=True)
    session.log("\n✅ Build complete. Artifacts are available in the 'dist/' directory.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def changelog(session: nox.Session) -> None:
    """
    📝 Generate a changelog from Towncrier fragments.

    Requires a version number as an argument.

    Example:
        nox -s changelog -- 1.3.0
    """
    if not session.posargs:
        session.error("❌ Missing version argument for changelog (e.g., 1.2.3)")

    version = session.posargs[0]
    session.log(f"\n📝 Generating changelog for version: {version}...\n")
    session.install("towncrier")
    session.run("towncrier", "build", "--version", version, "--yes", external=True)
    session.log(f"\n✅ Changelog generated for version {version}.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def docs_serve(session: nox.Session) -> None:
    """
    🚀 Serve documentation locally with MkDocs.

    Automatically rebuilds on changes and includes a draft changelog preview.

    Example:
        nox -s docs_serve
    """
    session.log("📥 Installing documentation dependencies...\n")
    session.install(*DOCS_DEPS, ".")

    draft_changelog = _draft_changelog(session)
    if draft_changelog.exists() and draft_changelog.read_text().strip():
        session.log("📝 Draft changelog generated for preview.")
    else:
        session.log("📝 No significant changes found for changelog draft.")

    session.log("🚀 Starting MkDocs server with auto-reload...\n")
    session.run("mkdocs", "serve", "--livereload", external=True)

    if draft_changelog.exists():
        draft_changelog.unlink()
        session.log("🧹 Cleaned up draft changelog.\n")


@nox.session(python=DEFAULT_PYTHON_VERSION)
def deploy_docs(session: nox.Session) -> None:
    """
    🌐 Deploy documentation to GitHub Pages via Mike.

    Requires a version argument and optionally an alias (like "stable").

    Examples:
        nox -s deploy_docs -- 1.2.0
        nox -s deploy_docs -- 1.2.0 stable
    """
    session.install(*DOCS_DEPS, ".")

    version = session.posargs[0] if session.posargs else "dev"
    alias = session.posargs[1] if len(session.posargs) > 1 else None

    session.log(f"📚 Deploying docs for version: {version}")
    if alias:
        session.log(f"🔗 Using alias: {alias}")
        session.run("mike", "deploy", "--update-aliases", version, alias, external=True)
        session.run("mike", "set-default", alias, external=True)
    else:
        session.run("mike", "deploy", version, external=True)

    session.log("🚀 Documentation deployed successfully.")

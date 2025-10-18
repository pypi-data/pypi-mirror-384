# 🤝 Contributing

We welcome contributions from everyone — whether you're fixing a typo, improving tests, or building new features!

This guide will walk you through setting up the project locally and contributing with confidence. Let’s build something great together! 🚀

> ⭐️ **Star the repo** to show your support:
> [https://github.com/jd-35656/resumake](https://github.com/jd-35656/resumake)

---

## 📌 How to Contribute

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a new branch** for your feature or fix
4. **Make your changes**
5. **Run tests and checks**
6. **Push** to your fork
7. **Open a Pull Request**

Please use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for commit messages.

---

## 🧪 Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jd-35656/resumake.git
cd resumake
```

### 2. Install Development Tooling

We use [nox](https://nox.thea.codes) to automate development tasks:

```bash
pipx install nox
```

### 3. Create a Virtual Environment

```bash
nox -s develop-3.13
```

This sets up a virtual environment in `.nox/develop-3.13`.

### 4. Activate the Environment

```bash
source .nox/develop-3-13/bin/activate
```

### 5. Deactivate the Environment

```bash
deactivate
```

!!! info "Using a Different Python Version?"
    Run `nox -l` to see available Python versions (e.g., 3.9–3.13) and run:

    ```bash
    nox -s develop-3.12
    ```

## 🧠 IDE Setup

=== "VS Code"

    1. Open the project folder
    2. Press `Ctrl+Shift+P` → “Python: Select Interpreter”
    3. Select `.nox/develop-3-13/bin/python`
    4. Recommended Extensions:

        * Python
        * Pylance
        * Ruff

=== "PyCharm"

    1. File → Settings → Project → Python Interpreter
    2. Add: `.nox/develop-3-13/bin/python`
    3. Apply and OK

---

## ✅ Verify Your Setup

Make sure everything is working correctly:

```bash
nox            # Run tests, lint, and type checks
nox -s tests   # Just run tests
nox -s lint    # Run formatter and linter
nox -s check   # Lint + type check
```

---

## 🛠️ Development Workflow

1. Make your changes
2. Run `nox` to ensure all checks pass
3. Add a changelog entry (if needed)
4. Commit using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
5. Push to your fork
6. Open a PR on GitHub

---

## 📝 Changelog Entries

For user-facing changes, add a changelog fragment using [towncrier](https://towncrier.readthedocs.io):

```bash
changelog.d/<issue_number>.<type>.rst
```

**Types**: `added`, `changed`, `deprecated`, `removed`, `fixed`, `security`

**Example:**

```bash
changelog.d/123.added.rst     # Adds a new feature
```

---

## 🧹 Code Standards

!!! note "Style Guide"

    * Line length: **121 characters**
    * Code formatting: **[ruff](https://docs.astral.sh/ruff/)**
    * Type hints: Required for public APIs
    * Docstrings: [Google-style](https://google.github.io/styleguide/pyguide.html)
    * Commits: [Conventional Commits](https://www.conventionalcommits.org)

---

## 🗂️ Project Structure

```text
src/resumake/
├── __main__.py         # CLI entry
├── __version__.py      # Auto-generated
├── cli/
│   └── app.py          # Typer app
└── core/
    └── __init__.py

tests/
├── test_cli.py
├── test_app.py
├── test_main.py
├── test_version.py
└── test_package.py
```

---

## 📄 Key Files

!!! abstract "Important Files"

    * `noxfile.py` – Dev automation (lint, tests, etc.)
    * `pyproject.toml` – Dependencies and tool configs
    * `docs/` – MkDocs documentation
    * `.github/workflows/` – CI/CD automation
    * `changelog.d/` – Changelog fragments

---

## 🛠️ Troubleshooting

!!! warning "Common Problems & Fixes"

    | Issue            | Solution                               |
    | ---------------- | -------------------------------------- |
    | Tests failing    | `nox -s tests -- -v`                   |
    | Lint errors      | `nox -s lint` (auto-fixable with Ruff) |
    | Type errors      | `nox -s typecheck`                     |
    | Coverage too low | Add more tests!                        |
    | CI build fails   | Check GitHub Actions logs              |

---

## 🙌 Thank You

Your contributions make this project better!
Even small improvements make a big impact.
Feel free to [open an issue](https://github.com/jd-35656/resumake/issues) or start a discussion.

> ⭐️ Star the project: [https://github.com/jd-35656/resumake](https://github.com/jd-35656/resumake)

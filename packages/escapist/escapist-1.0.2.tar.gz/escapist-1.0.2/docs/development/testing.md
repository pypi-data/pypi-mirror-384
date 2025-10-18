# 🧪 Testing

## 📋 Available Nox Sessions

!!! info "List Available Sessions"
    Run this to list all available Nox sessions:

    ```bash
    nox -l
    ```

    Example output:

    ```
    Sessions defined in noxfile.py:

    - develop-3.8     # Create development environment
    - develop-3.9
    - develop-3.10
    - develop-3.11
    - develop-3.12
    - develop-3.13
    * tests-3.8       # Run tests with coverage
    * tests-3.9
    * tests-3.10
    * tests-3.11
    * tests-3.12
    * tests-3.13
    - lint            # Code formatting and linting
    - typecheck       # Type checking with mypy
    * check           # Run lint + typecheck
    - build           # Build package distributions
    - changelog       # Generate changelog
    - docs_serve      # Serve documentation locally
    - docs_deploy     # Deploy documentation to GitHub Pages

    Sessions marked with * are selected; - are available but skipped.
    ```

---

## ✅ Running Tests

=== "Basic Usage"
    ```bash
    # Run tests across all supported Python versions
    nox -s tests

    # Run tests on a specific Python version
    nox -s tests-3.13

    # Run the default sessions (tests + code checks)
    nox
    ```

=== "Custom Arguments"
    ```bash
    # Verbose output
    nox -s tests-3.13 -- -v

    # Run tests matching a pattern
    nox -s tests-3.13 -- -k test_version

    # Run a specific test file
    nox -s tests-3.13 -- tests/test_cli.py

    # Use short traceback
    nox -s tests-3.13 -- --tb=short

    # Generate HTML coverage report
    nox -s tests-3.13 -- --cov-report=html

    # Combine multiple arguments
    nox -s tests-3.13 -- -v -k test_cli --tb=short
    ```

!!! tip "Common `pytest` Arguments"
    ```bash
    -v                  # Verbose output
    -s                  # Show print() output
    -x                  # Stop after first failure
    -k EXPRESSION       # Filter tests by substring
    --tb=short|long|no  # Control traceback format
    --lf                # Run only last failed tests
    --ff                # Run failed tests first
    ```

---

## 🧹 Code Quality Checks

=== "Linting"
    ```bash
    # Run all linting checks
    nox -s lint

    # Includes:
    # - ruff (formatting/linting)
    # - codespell (spell checks)
    # - pre-commit hooks
    ```

=== "Type Checking"
    ```bash
    # Type check using mypy
    nox -s typecheck

    # With arguments
    nox -s typecheck -- --strict
    nox -s typecheck -- src/resumake/cli/
    ```

=== "Combined"
    ```bash
    # Run both linting and type checking
    nox -s check

    # Run all default quality checks and tests
    nox
    ```

---

## 📈 Coverage Reports

!!! success "Coverage Summary"
    Test sessions include coverage reporting:

    - 📊 **Terminal Output**: shows % covered and missing lines
    - 📁 **HTML Report**: viewable with `--cov-report=html`
    - ✅ **Minimum Required**: 90%
    - 🟢 **Current**: 100% coverage

---

## 📚 Documentation Development

!!! note "Serve Docs Locally"
    ```bash
    nox -s docs_serve
    ```

    - Starts a local server with live reload
    - Available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ⚙️ Requirements

!!! abstract "Testing Requirements"
    - **Python**: 3.8 or newer (up to 3.13 supported)
    - **Coverage Threshold**: 90% minimum
    - **Test Layout**:
        - Files: `tests/test_*.py`
        - Classes: `Test*` format

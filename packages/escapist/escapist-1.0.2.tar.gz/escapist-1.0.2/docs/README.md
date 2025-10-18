# Escapist: Simplify Jinja2 Template Rendering

Escapist is a lightweight Python tool designed to render Jinja2 templates using JSON or dict data and flexible environment settings. It can be used both as a CLI for quick template rendering tasks and as a Python library for programmatic integration.

For detailed usage and documentation, visit: [**Escapist Documentation**](https://jd-35656.github.io/escapist)

---

## Features

* **Customizable Jinja2 environment**: Configure block delimiters, autoescaping, whitespace trimming, and more through JSON or dict settings.
* **Supports JSON data**: Provide template data via JSON files or Python dictionaries.
* **CLI & API**: Use via command line or import as a Python library.
* **Batch rendering**: Render multiple templates in one command.
* **Cross-platform**: Works on Windows, macOS, and Linux.

---

## Installation

To install Escapist, run:

```bash
pipx install escapist
```

---

## Usage

### Command-Line Interface (CLI)

Escapist provides simple commands to render Jinja2 templates with JSON data and custom settings.

#### Render a Single Template

```bash
escapist render TEMPLATE_PATH \
  --data DATA_JSON_FILE \
  --settings SETTINGS_JSON_FILE \
  --output OUTPUT_FILE_PATH
```

* `TEMPLATE_PATH`: Path to your Jinja2 template file.
* `--data`: (Optional) Path to a JSON file containing data for rendering.
* `--settings`: (Optional) Path to a JSON file with Jinja environment settings.
* `--output`: (Optional) Path to save the rendered output. If omitted, output is printed to stdout.

#### Render Multiple Templates in Batch

```bash
escapist batch TEMPLATE_DIR \
  --pattern '*.html' \
  --data DATA_JSON_FILE \
  --settings SETTINGS_JSON_FILE \
  --output-dir OUTPUT_DIRECTORY \
  --force
```

* `TEMPLATE_DIR`: Directory containing your templates.
* `--pattern`: (Optional) File pattern to match templates, e.g., `*.html`.
* `--data`: (Optional) JSON data file for all templates.
* `--settings`: (Optional) Jinja environment settings file.
* `--output-dir`: Directory to save rendered templates.
* `--force`: (Optional) Overwrite existing output files.

---

### Python Library Usage

You can also use Escapist as a Python library for programmatic rendering.

```python
from escapist import Escapist

# Initialize renderer with optional settings
renderer = Escapist(settings="path/to/settings.json")

# Load template (file path or template string)
renderer.load_template("path/to/template.jinja")

# Render with data (dict or path to JSON file)
output = renderer.render(data={"name": "Alice", "version": "1.0.0"})

print(output)
```

---

## Settings Format

Escapist supports flexible Jinja2 environment configuration via JSON settings files. Below is an example structure of a settings JSON file you can use to customize the rendering environment:

{% raw %}

```json
{
  "environment": {
    "block_start_string": "{%",
    "block_end_string": "%}",
    "variable_start_string": "{{",
    "variable_end_string": "}}",
    "comment_start_string": "{#",
    "comment_end_string": "#}",
    "line_statement_prefix": null,
    "line_comment_prefix": null,
    "trim_blocks": false,
    "lstrip_blocks": false,
    "newline_sequence": "\n",
    "keep_trailing_newline": false
  },
  "globals": {
    "app_name": "Escapist",
    "version": "0.0.1"
  },
  "autoescape": {
    "enabled_extensions": ["html", "htm", "xml"],
    "disabled_extensions": [],
    "default_for_string": true,
    "default": false
  },
  "escape_sequences": {
    ">": "&gt;",
    "<": "&lt;",
    "&": "&amp;",
    "\"": "&quot;",
    "'": "&#39;"
  },
  "treat_missing_variable_as_missing": true
}
```

{% endraw %}

* **environment**: Configures Jinja2 delimiters, whitespace trimming, newline behavior, and other environment options.
* **globals**: Defines default variables accessible in templates; if a variable is missing from provided data, the value here is used.
* **autoescape**: Controls autoescaping of output based on file extensions. Can also be a boolean (`true` or `false`). Default is `false`. Enable to prevent HTML/XSS injection.
* **escape_sequences**: Maps characters to their escaped representations (e.g., replacing `>` with `&gt;`).
* **treat_missing_variable_as_missing**: Determines how missing variables in the template data are handled (e.g., treat as missing instead of erroring).

---

## License

`escapist` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

---

## Contact

Created by Jitesh Sahani (JD)
Email: [jitesh.sahani@outlook.com](mailto:jitesh.sahani@outlook.com)

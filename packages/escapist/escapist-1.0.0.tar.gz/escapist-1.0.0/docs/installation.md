# ✅ **Installation Guide**

## 🚀 Recommended: Using [pipx](https://pypa.github.io/pipx/)

!!! tip "Why pipx?"
    `pipx` installs Python CLI tools in isolated environments, keeping your global Python setup clean while making the command available system-wide.

### 📦 Install pipx (if not already installed)

=== "macOS"
    ```bash
    brew install pipx
    pipx ensurepath
    ```

=== "Ubuntu / Debian"
    ```bash
    sudo apt update
    sudo apt install pipx
    pipx ensurepath
    sudo pipx ensurepath --global  # Optional: enable global usage
    ```

=== "Windows"
    ```powershell
    # Using Scoop
    scoop install pipx

    # Or using pip
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

=== "Other Linux"
    ```bash
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

---

### ✅ Install Escapist with pipx

!!! success "Install Command"
    ```bash
    pipx install escapist
    ```

---

### 🔍 Verify Installation

!!! note ""
    Run the following to confirm it was installed correctly:

    ```bash
    escapist --version
    ```

---

## 🐍 Alternative: Using pip

!!! info "Not using pipx?"
    You can also install Escapist using pip, though it's **strongly recommended** to use a virtual environment.

    ```bash
    pip install escapist
    ```

!!! warning "Use a virtual environment"
    Avoid installing globally with pip. Instead:

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install escapist
    ```

---

## 🔄 Upgrading

=== "With pipx"
    ```bash
    pipx upgrade escapist
    ```

=== "With pip"
    ```bash
    pip install --upgrade escapist
    ```

---

## 🧹 Uninstalling

=== "With pipx"
    ```bash
    pipx uninstall escapist
    ```

=== "With pip"
    ```bash
    pip uninstall escapist
    ```

---

## 🖥️ System Requirements

!!! abstract "Requirements"
    - **Python**: 3.8 or higher
    - **Operating System**: Windows, macOS, Linux
    - **Dependencies**: Automatically installed during setup

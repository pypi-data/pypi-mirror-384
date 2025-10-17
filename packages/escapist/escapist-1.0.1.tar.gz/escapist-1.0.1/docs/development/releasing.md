# 🚀 Releasing

!!! info "Personal Reference"
    Quick reference for future releases

---

## 📝 Quick Release Guide

=== "✅ GitHub Actions (Recommended)"
    1. Go to **GitHub Actions** → **"Create Release"** workflow
    2. Click **"Run workflow"**
    3. Select release type and run

=== "🏷️ PR Labels"
    1. Add `release:patch`, `release:minor`, or `release:major` label to a merged PR
    2. Release workflow triggers automatically

---

## 🧩 Release Types

| Label           | Example           | Purpose                      |
| --------------- | ----------------- | ---------------------------- |
| `release:patch` | `1.0.0` → `1.0.1` | Bug fixes                    |
| `release:minor` | `1.0.0` → `1.1.0` | Backward-compatible features |
| `release:major` | `1.0.0` → `2.0.0` | Breaking changes             |

---

## ⚙️ What Happens Automatically

1. 🔢 **Version calculation** – Based on label or workflow input
2. 📝 **Changelog generation** – Using [`towncrier`](https://towncrier.readthedocs.io/) from `changelog.d/`
3. 🌿 **Git operations** – Commits version bump & tags release
4. 🐙 **GitHub Release** – Drafted with generated changelog notes
5. 📦 **PyPI publishing** – Uploads release to PyPI
6. 🌐 **Documentation deployment** – Builds & updates docs via GitHub Pages

---

## ✅ Before Releasing

!!! warning "Prerequisites"
    - ✅ All CI checks pass
    - ✅ Changelog fragments exist — or PR has `no-changelog` label
    - ✅ `main` branch is up to date and clean

---

## 🧯 If Something Goes Wrong

!!! danger "Emergency Response"

    === "🩹 Quick Fix"
        - 🔒 **Yank release from PyPI** (prevents new installs)
        - 📝 **Add a warning** to the GitHub release notes

    === "🔥 Major Issues"
        - ❌ **Delete release** and corresponding Git tag
        - 🛠️ **Create a hotfix** release with patch bump
        - ⏪ **Revert commits** if necessary

---

## 📂 Important Files

| File / Path                     | Purpose                                           |
| ------------------------------- | ------------------------------------------------- |
| `changelog.d/*.md`              | Changelog fragments (`.feature`, `.bugfix`, etc.) |
| `.github/workflows/release.yml` | Release automation workflow                       |
| `.github/workflows/publish.yml` | PyPI publishing & deployment                      |
| `nox -s changelog`              | Generate changelog                                |
| `nox -s build`                  | Build Python distribution                         |
| `nox -s docs_deploy`            | Deploy documentation                              |

---

## 🔐 Secrets Required

!!! note "GitHub Repository Secrets"

- `PYPI_API_TOKEN` – PyPI publish access
- `PAT_TOKEN` – GitHub token with release permissions

---

## 🧰 Troubleshooting

!!! tip "Common Issues"

| Problem              | Solution                                          |
| -------------------- | ------------------------------------------------- |
| ❌ Release failed     | Check GitHub Actions logs for errors              |
| 📦 PyPI upload failed | Check version uniqueness and API token            |
| 📄 Changelog empty    | Ensure valid fragments exist in `changelog.d/`    |
| 🌐 Docs not updating  | Check `gh-pages` branch or deploy workflow status |

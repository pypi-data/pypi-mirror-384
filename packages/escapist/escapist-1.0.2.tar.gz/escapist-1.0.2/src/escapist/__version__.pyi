# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT

# Version as a PEP 440-compliant string, e.g., "0.0.1" or "0.0.1.dev1+g97717df2f.d20250905"

version: str
__version__: str

# Version as a tuple for programmatic use:
#   - Release version: (major, minor, patch), e.g., (0, 0, 1)
#   - Development version: (major, minor, patch, dev_tag, local_node), e.g., (0, 0, 1, "dev1", "g97717df2f.d20250905")
version_tuple: tuple[int, int, int] | tuple[int, int, int, str, str]
__version_tuple__: tuple[int, int, int] | tuple[int, int, int, str, str]

# Git commit ID for dev builds; None for releases
commit_id: str | None
__commit_id__: str | None

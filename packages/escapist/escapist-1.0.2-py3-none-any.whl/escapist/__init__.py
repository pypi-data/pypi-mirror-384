# SPDX-FileCopyrightText: 2025-present Jitesh Sahani (JD) <jitesh.sahani@outlook.com>
#
# SPDX-License-Identifier: MIT

"""
Main API entry point for the Escapist library.

This module exposes the `Escapist` class, which serves as the primary interface
for rendering templates based on user-defined settings.

Usage:
    ```python
    from escapist import Escapist

    renderer = Escapist(settings="path/to/settings.yaml")

    ```
"""

from escapist.core import Escapist

__all__ = ["Escapist"]

# __init__.py
#
# Copyright (c) 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from wretched_tower.app import TowerApp

__version__ = "0.1.2"


def main() -> None:  # no cov
    tower_app = TowerApp()
    tower_app.run()

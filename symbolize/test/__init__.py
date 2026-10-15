"""Tests for the top-level modules (`groups`, `natural`, `utility`), and the
discovery runner for the whole suite.

Tests live in a `test/` subfolder of the package they exercise, so discovery
starts from the `symbolize` package with the repository root as the
top-level directory.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import os
import unittest


def main() -> None:
    """Discover and run every test in the project."""
    package = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=package, top_level_dir=os.path.dirname(package)
    )
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    main()

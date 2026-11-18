"""Smoke test: the package is installed in the environment and importable."""

import qec


def test_package_has_a_version() -> None:
    assert isinstance(qec.__version__, str)
    assert qec.__version__

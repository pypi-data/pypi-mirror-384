"""Pytest configuration"""

# pylint: disable=wrong-import-position, wrong-import-order, missing-function-docstring

import os
# Adding source path to sys path
import pathlib
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
sys.path.append(f"{pathlib.Path(__file__).parent.parent}")
sys.path.append(f"{pathlib.Path(__file__).parent}")
# pylint: enable=wrong-import-position, wrong-import-order

import pytest

os.environ["DEBUG"] = "True"

def pytest_addoption(parser):
    parser.addoption(
        "--skip-linting", action="store_true", default=False, help="skip the pylint test"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-linting"):
        skip_pylint = pytest.mark.skip(reason="skipping code linting due to --skip-linting arg")
        for item in items:
            if item.name in ["test_pylint", "test_mypy"]:
                item.add_marker(skip_pylint)

# pylint: disable-next=unused-wildcard-import, wildcard-import, wrong-import-order
from test.fixtures import *

"""Module containing tests for the abllib.log module"""

import os
import re

import pytest

from abllib import error, general

# pylint: disable=unused-argument

def test_try_import_module():
    """Ensure that try_import_module works as expected"""

    assert callable(general.try_import_module)

    assert general.try_import_module("os") == os
    assert general.try_import_module("abllib.general") == general

    assert general.try_import_module("doesnt_exist") is None

def test_try_import_module_error_msg(capture_logs):
    """Ensure that try_import_module considers given error messages"""

    assert general.try_import_module("doesnt_exist") is None

    assert not os.path.isfile("test.log")

    assert general.try_import_module("doesnt_exist", "The doesnt_exist module in fact doesn't exist") is None

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 1
        assert re.match(r"\[.*\] \[WARNING \] general: The doesnt_exist module in fact doesn't exist", content[0])

def test_try_import_module_raise_error():
    """Ensure that try_import_module raises an error"""

    assert general.try_import_module("doesnt_exist", enforce=False) is None

    with pytest.raises(error.MissingRequiredModuleError, match="The required module 'doesnt_exist' is not installed."):
        general.try_import_module("doesnt_exist", enforce=True)

    with pytest.raises(error.MissingRequiredModuleError, match="The doesnt_exist module in fact doesn't exist"):
        general.try_import_module("doesnt_exist", "The doesnt_exist module in fact doesn't exist", enforce=True)

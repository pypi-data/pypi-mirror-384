"""Module containing tests for the abllib.wrapper.deprecated functionality"""

import pytest

from abllib import error, wrapper

# pylint: disable=function-redefined, consider-using-with, unused-argument, missing-class-docstring

def test_callable():
    """Ensure that wrapper.deprecated is callable"""

    assert hasattr(wrapper, "deprecated")
    assert callable(wrapper.deprecated)

def test_defaultmessage(capture_logs):
    """Ensure that wrapper.deprecated logs a warning"""

    @wrapper.deprecated
    def func1():
        pass
    func1()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'func1' is deprecated" in f.read()

def test_defaultmessage_class(capture_logs):
    """Ensure that wrapper.deprecated logs a warning"""

    @wrapper.deprecated
    class A():
        pass
    A()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'A' is deprecated" in f.read()

def test_warning_defaultmessage(capture_logs):
    """Ensure that wrapper.deprecated.warning logs a warning"""

    @wrapper.deprecated.warning
    def func1():
        pass
    func1()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'func1' is deprecated" in f.read()

def test_warning_defaultmessage_class(capture_logs):
    """Ensure that wrapper.deprecated.warning logs a warning"""

    @wrapper.deprecated.warning
    class A():
        pass
    A()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'A' is deprecated" in f.read()

def test_custommessage(capture_logs):
    """Ensure that wrapper.deprecated with a custom message logs that message"""

    @wrapper.deprecated("A custom deprecation message")
    def func1():
        pass
    func1()
    with open("test.log", "r", encoding="utf8") as f:
        assert "A custom deprecation message" in f.read()

def test_custommessage_class(capture_logs):
    """Ensure that wrapper.deprecated with a custom message logs that message"""

    @wrapper.deprecated("A custom deprecation message")
    class A():
        pass
    A()
    with open("test.log", "r", encoding="utf8") as f:
        assert "A custom deprecation message" in f.read()

def test_warning_custommessage(capture_logs):
    """Ensure that wrapper.deprecated.warning with a custom message logs that message"""

    @wrapper.deprecated.warning("A custom deprecation message")
    def func1():
        pass
    func1()
    with open("test.log", "r", encoding="utf8") as f:
        assert "A custom deprecation message" in f.read()

def test_warning_custommessage_class(capture_logs):
    """Ensure that wrapper.deprecated.warning with a custom message logs that message"""

    @wrapper.deprecated.warning("A custom deprecation message")
    class A():
        pass
    A()
    with open("test.log", "r", encoding="utf8") as f:
        assert "A custom deprecation message" in f.read()

def test_reassign_func_defaultmessage(capture_logs):
    """Ensure that reassigning a function to a different name logs that name"""

    def func1():
        pass
    def func2():
        return func1()
    func2 = wrapper.deprecated.warning(func2)
    func2()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'func2' is deprecated" in f.read()

def test_inherit_class_defaultmessage(capture_logs):
    """Ensure that reassigning a function to a different name logs that name"""

    class A():
        pass
    @wrapper.deprecated.warning
    class B(A):
        pass
    B()
    with open("test.log", "r", encoding="utf8") as f:
        assert "The functionality 'B' is deprecated" in f.read()

def test_error_defaultmessage():
    """Ensure that wrapper.deprecated.error raises an error"""

    @wrapper.deprecated.error
    def func1():
        pass
    with pytest.raises(error.DeprecatedError):
        func1()

def test_custommessage_as_error():
    """Ensure that wrapper.deprecated as error with a custom message uses that message"""

    @wrapper.deprecated("A custom deprecation message", True)
    def func1():
        pass
    with pytest.raises(error.DeprecatedError):
        func1()

def test_error_custommessage():
    """Ensure that wrapper.deprecated.error with a custom message uses that message"""

    @wrapper.deprecated.error("A custom deprecation message")
    def func1():
        pass
    with pytest.raises(error.DeprecatedError):
        func1()

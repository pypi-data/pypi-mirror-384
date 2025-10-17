"""Module containing tests for the abllib.log module"""

import os
import re

import pytest

from abllib import log
from abllib.error import NameNotFoundError

def test_initialize():
    """Ensure that log initialization works as expected"""

    assert callable(log.initialize)

    log.initialize(log.LogLevel.DEBUG)
    log.add_console_handler()

    logger = log.get_logger("testlogger")

    logger.info("test1234")
    # logging output in console can't be tested cause pylint consumes it first

def test_file_handler():
    """Ensure that file handler works as expected"""

    # cleanup if file is left from previous run
    if os.path.isfile("test.log"):
        os.remove("test.log")

    log.initialize(log.LogLevel.DEBUG)
    log.add_file_handler("test.log")

    logger = log.get_logger()
    logger.debug("the debug message")
    logger.critical("this is critical")

    logger = log.get_logger("submodule")
    logger.info("just an info")
    logger.warning("and a warning")

    logger = log.get_logger("submodule2")
    logger.debug("the final message")

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 5
        assert re.match(r"\[.*\] \[DEBUG   \] root: the debug message", content[0])
        assert re.match(r"\[.*\] \[CRITICAL\] root: this is critical", content[1])
        assert re.match(r"\[.*\] \[INFO    \] submodule: just an info", content[2])
        assert re.match(r"\[.*\] \[WARNING \] submodule: and a warning", content[3])
        assert re.match(r"\[.*\] \[DEBUG   \] submodule2: the final message", content[4])

    # cleanup and remove the file handler
    log.initialize()
    os.remove("test.log")

def test_exception_logging():
    """Ensure logging an exception looks beautiful"""

    # cleanup if file is left from previous run
    if os.path.isfile("test.log"):
        os.remove("test.log")

    log.initialize(log.LogLevel.INFO)
    log.add_file_handler("test.log")

    logger = log.get_logger()
    try:
        raise RuntimeError("my message")
    except RuntimeError as err:
        logger.exception(err)

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 5
        assert re.match(r"\[.*\] \[ERROR   \] root: my message", content[0])
        assert re.match(r"Traceback \(most recent call last\):", content[1])
        assert re.match(r"  File \".*log_test.py\", line \d+, in test_exception_logging", content[2])
        assert re.match(r"    raise RuntimeError\(\"my message\"\)", content[3])
        assert re.match(r"RuntimeError: my message", content[4])

    # cleanup and remove the file handler
    log.initialize()
    os.remove("test.log")

def test_file_handler_delay():
    """Ensure that file handler only creates logfile when needed"""

    # cleanup if file is left from previous run
    if os.path.isfile("test.log"):
        os.remove("test.log")

    log.initialize(log.LogLevel.WARNING)
    assert not os.path.isfile("test.log")

    log.add_file_handler("test.log")
    assert not os.path.isfile("test.log")

    logger = log.get_logger()
    assert not os.path.isfile("test.log")

    logger.debug("debugmsg")
    assert not os.path.isfile("test.log")

    logger.info("infomsg")
    assert not os.path.isfile("test.log")

    logger.warning("warnmsg")
    assert os.path.isfile("test.log")

    with open("test.log", "r", encoding="utf8") as f:
        content = f.read()
        assert content != ""
        assert re.match(r"\[.*\] \[WARNING \] root: warnmsg\n", content)

    # cleanup and remove the file handler
    log.initialize()
    os.remove("test.log")

def test_deprecated_levels():
    """Ensure that LogLevel.WARN and LogLevel.FATAL cannot be used"""

    assert hasattr(log.LogLevel, "WARNING")
    assert not hasattr(log.LogLevel, "WARN")

    assert hasattr(log.LogLevel, "CRITICAL")
    assert not hasattr(log.LogLevel, "FATAL")

def test_initialize_invalidtypes():
    """Ensure that initialize only accepts valid arguments"""

    # to be added when abllib.type module is implemented

def test_loglevel_fromstr():
    """Ensure that LogLevel.from_str works correctly"""

    assert callable(log.LogLevel.from_str)
    assert log.LogLevel.from_str("CRITICAL") is log.LogLevel.CRITICAL
    assert log.LogLevel.from_str("ERROR") is log.LogLevel.ERROR
    assert log.LogLevel.from_str("WARNING") is log.LogLevel.WARNING
    assert log.LogLevel.from_str("INFO") is log.LogLevel.INFO
    assert log.LogLevel.from_str("DEBUG") is log.LogLevel.DEBUG
    assert log.LogLevel.from_str("ALL") is log.LogLevel.ALL

    with pytest.raises(NameNotFoundError):
        log.LogLevel.from_str("INVALID")

def test_loglevel_fromstr_mixedcase():
    """Ensure that LogLevel.from_str ignores text case"""

    assert callable(log.LogLevel.from_str)
    assert log.LogLevel.from_str("crITiCaL") is log.LogLevel.CRITICAL
    assert log.LogLevel.from_str("error") is log.LogLevel.ERROR
    assert log.LogLevel.from_str("Warning") is log.LogLevel.WARNING
    assert log.LogLevel.from_str("iNFO") is log.LogLevel.INFO
    assert log.LogLevel.from_str("deBuG") is log.LogLevel.DEBUG
    assert log.LogLevel.from_str("alL") is log.LogLevel.ALL

def test_file_handler_filemodes():
    """Ensure that file handler works with different file modes"""

    # cleanup if file is left from previous run
    if os.path.isfile("test.log"):
        os.remove("test.log")

    log.initialize(log.LogLevel.DEBUG)
    log.add_file_handler("test.log")
    logger = log.get_logger()

    logger.debug("the debug message")

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 1
        assert re.match(r"\[.*\] \[DEBUG   \] root: the debug message", content[0])

    # initialize to overwrite logfile
    log.initialize(log.LogLevel.DEBUG)
    log.add_file_handler("test.log", filemode="w")
    logger = log.get_logger()

    logger.critical("this is critical")

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 1
        assert re.match(r"\[.*\] \[CRITICAL\] root: this is critical", content[0])

    # initialize to append to logfile
    log.initialize(log.LogLevel.DEBUG)
    log.add_file_handler("test.log", filemode="a")
    logger = log.get_logger()

    logger.debug("the debug message")

    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()
        assert len(content) == 2
        assert re.match(r"\[.*\] \[CRITICAL\] root: this is critical", content[0])
        assert re.match(r"\[.*\] \[DEBUG   \] root: the debug message", content[1])

    # cleanup and remove the file handler
    log.initialize()
    os.remove("test.log")

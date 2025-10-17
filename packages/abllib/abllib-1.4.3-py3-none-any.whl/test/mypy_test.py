"""Module containing the pylint test"""

import os

import pytest

from abllib import fs, log

logger = log.get_logger("mypy")

def test_mypy():
    """Checks if all git-tracked python files adhere to mypy rules"""

    ROOTDIR = fs.absolute(__file__, "..", "..", "..")
    PREV_DIR = os.getcwd()
    os.chdir(ROOTDIR)

    if os.name == "nt":
        files = os.popen("git ls-files *.py").read()
        files = " ".join([file.strip() for file in files.split("\n")])

        mypy_output = []
        for line in os.popen(f"python -m mypy {files}").readlines():
            if line.strip().strip("-") != "":
                mypy_output.append(line.strip())

        os.chdir(PREV_DIR)

        if len(mypy_output) == 0:
            pytest.fail("Detected error during test. Is mypy installed?")

        if not "Success: no issues found" in mypy_output[-1]:
            for line in mypy_output:
                logger.warning(line)

            pytest.fail(mypy_output[-1])
    else:
        # logging mypy errors on linux doesn't work
        mypy_output = os.popen("python3 -m mypy $(git ls-files '*.py')").read()

        os.chdir(PREV_DIR)

        assert "Success: no issues found" in mypy_output

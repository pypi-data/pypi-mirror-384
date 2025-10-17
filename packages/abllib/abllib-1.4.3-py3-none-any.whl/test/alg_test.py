"""Module containing tests for the abllib.alg module"""

import pytest

from abllib import alg, error

def test_levenshtein_distance():
    """Ensure that alg.levenshtein_distance works as expected"""

    assert alg.levenshtein_distance("fox", "fox") == 0
    assert alg.levenshtein_distance("fox", "fof") == 1
    assert alg.levenshtein_distance("the brown fox", "the green fox") == 3
    assert alg.levenshtein_distance("", "a") == 1

    assert isinstance(alg.levenshtein_distance("dog", "god"), int)

    with pytest.raises((error.WrongTypeError, TypeError)):
        alg.levenshtein_distance("test", None)
    with pytest.raises((error.WrongTypeError, TypeError)):
        alg.levenshtein_distance(None, "test")
    with pytest.raises((error.WrongTypeError, TypeError)):
        alg.levenshtein_distance("test", 12)

"""A module containing fuzzy matching-related functionality"""

from abllib.fuzzy._all import match_all
from abllib.fuzzy._closest import match_closest
from abllib.fuzzy._matchresult import MatchResult
from abllib.fuzzy._similarity import Similarity

def similarity(target: str, candidate: str) -> float:
    """
    Checks how closely two strings match. (Version 2)

    Returns a float value between 0.0 and 1.0 (inclusive), where 1.0 is a perfect match.
    """

    return Similarity(target, candidate).calculate()

__exports__ = [
    match_all,
    match_closest,
    MatchResult,
    Similarity,
    similarity
]

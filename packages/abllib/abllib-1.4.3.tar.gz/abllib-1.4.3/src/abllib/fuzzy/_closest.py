"""A module containing the fuzzy match function"""

from abllib.fuzzy._matchresult import MatchResult
from abllib.fuzzy._similarity import Similarity

def match_closest(target: str, candidates: list[str | tuple[str, ...]], threshold: int = 5) -> MatchResult:
    """
    Match the target to the most similar candidate. Applies fuzzy logic when comparing.

    In order to successfully match a candidate, at least one of two conditions need to be true:
    * the edit distance (levenshtein distance) needs to be smaller than *threshold*
    * a single word (*target* split at ' ') needs to have an edit distance smaller than (len(*word*) / 3) + 1

    After that, it chooses the closest-matching candidate.

    Returns a MatchResult
    """

    # TODO: type checking with abllib.type module

    if threshold < 0:
        raise ValueError("Threshold needs to be >= 0")

    result = MatchResult(0.0)
    for i, candidate in enumerate(candidates):
        curr_result = _matches_single_candidate(target, candidate, threshold)
        if curr_result.score > result.score:
            result = MatchResult(curr_result.score, curr_result.value, i, curr_result.inner_index)

    return result

def _matches_single_candidate(target: str, candidate: str | tuple[str, ...], threshold: int) -> MatchResult:
    if isinstance(candidate, str):
        score = Similarity(target, candidate, threshold).calculate()
        return MatchResult(score, candidate)

    result = MatchResult(0.0)
    for i, inner_candidate in enumerate(candidate):
        score = Similarity(target, inner_candidate, threshold).calculate()
        if score > result.score:
            result = MatchResult(score, candidate, inner_index=i)

    return result

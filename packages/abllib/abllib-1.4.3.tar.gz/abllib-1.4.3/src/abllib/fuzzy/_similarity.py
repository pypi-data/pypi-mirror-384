"""Module containing the similarity function"""

import numpy as np

from abllib import error
from abllib.alg import levenshtein_distance

class Similarity():
    """
    Checks how closely two strings match. (Version 2)

    Returns a float value between 0.0 and 1.0 (inclusive), where 1.0 is a perfect match.
    """

    def __init__(self, target: str, candidate: str, threshold: int = 5) -> None:
        targets = target.split(" ")
        candidates = candidate.split(" ")

        # ensure that targets is always smaller than candidates
        if len(targets) > len(candidates):
            target, candidate = candidate, target
            targets, candidates = candidates, targets

        self._target = target
        self._candidate = candidate

        self._targets = targets
        self._candidates = candidates

        self._threshold = threshold

        self.scores_array = self._construct_scores_array()

    def _construct_scores_array(self) -> np.typing.NDArray:
        """
        The returned 2D scores_array is structured as follows:
                    candidate1  candidate2  candidate3  candidate4
        target1     0.75        0.5         0.0         0.0
        target2     0.0         0.0         1.0         0.0
        target3     1.0         0.0         0.0         0.8
        such that scores[2][3] == 0.8.
        """

        scores_array = np.full((len(self._targets), len(self._candidates)), fill_value=0.0)

        # construct scores_array 2d array
        for i_target, inner_target in enumerate(self._targets):
            for i_candidate, inner_candidate in enumerate(self._candidates):
                edit_dist = levenshtein_distance(inner_target, inner_candidate)

                max_dist_by_target = (len(inner_target) // 3) + 1
                max_dist_by_candidate = (len(inner_candidate) // 3) + 1
                max_allowed_dist = min(max_dist_by_target, max_dist_by_candidate, self._threshold)

                # check if edit distance is within bounds
                if edit_dist <= max_allowed_dist:
                    # we take either inner_target or inner_candidate, depending on which has more characters
                    # this ensures that swapping target and candidate results in the same score
                    max_inner_len = max(len(inner_target), len(inner_candidate))
                    similar_chars = max_inner_len - edit_dist
                    divisor = max_inner_len
                    score = similar_chars / divisor
                    scores_array[i_target][i_candidate] = score

        return scores_array

    def calculate(self) -> float:
        """Calculate the similarity"""

        score = max(
            self._calculate_simple(),
            self._calculate_complex()
        )
        score = np.round(score, 2).item()

        if score < 0.0 or score > 1.0:
            raise error.InternalCalculationError(f"Score {score} is not in acceptable range 0.0 <= score <= 1.0")

        return score

    def _calculate_simple(self) -> float:
        edit_dist = levenshtein_distance(self._target, self._candidate)

        if edit_dist > self._threshold:
            return 0.0

        max_len = max(len(self._target), len(self._candidate))
        similar_chars = max_len - edit_dist
        divisor = max_len
        score = similar_chars / divisor
        return score

    def _calculate_complex(self) -> float:
        score_divisor = len(self._candidates)

        if not _contains_duplicates(self._construct_primitive_indexes()):
            # the target words don't interfere with each other, so we can use the best score for each

            total_score = 0.0
            for row in self.scores_array:
                total_score += row.max()
            return total_score / score_divisor

        indexes = self._construct_overlapping_indexes()

        optimal_indexes = self._construct_optimal_indexes(indexes)

        total_score = 0.0
        for row_i, col_i in enumerate(optimal_indexes):
            total_score += self.scores_array[row_i][col_i]

        return total_score / score_divisor

    def _construct_primitive_indexes(self) -> list[np.intp]:
        indexes = []

        for row in self.scores_array:
            index = np.argmax(row)
            if row[index] != 0.0:
                indexes.append(index)

        return indexes

    def _construct_overlapping_indexes(self) -> dict[int, list[int]]:
        indexes: dict[int, list[int]] = {}

        for row_i, row in enumerate(self.scores_array):
            index = np.argmax(row).item()
            if row[index] == 0.0:
                index = -1

            if index not in indexes:
                indexes[index] = []
            indexes[index].append(row_i)

        return indexes

    def _construct_optimal_indexes(self, indexes: dict[int, list[int]]) -> list[int]:
        """
        This class will create a list which maximizes the total score, so that each target is used once.
        For example:
                    index
        target1     0
        target2     2
        target3     3
        such that the total score equals 0.75 + 1.0 + 0.8 = 2.55.
        """

        while not self._optional_calc_is_done(indexes):
            curr_index = self._optional_calc_get_next_index(indexes)

            curr_target_indexes = indexes[curr_index]
            del indexes[curr_index]

            curr_scores: np.typing.NDArray[np.float64] = np.ndarray((len(curr_target_indexes),
                                                                     self.scores_array.shape[1]),
                                                                    dtype=np.ndarray)

            scores_i = 0
            for row_i, row in enumerate(self.scores_array):
                if row_i in curr_target_indexes:
                    curr_scores[scores_i] = row
                    scores_i += 1

            _, ind = _alg_with_index(curr_scores, 0.0)

            for target_i, candidate_i in zip(curr_target_indexes, ind):
                if candidate_i not in indexes:
                    indexes[candidate_i] = []
                indexes[candidate_i].append(target_i)

        number_of_targets = sum((len(item) for item in indexes.values()))
        optimal_indexes = np.full(number_of_targets, dtype=int, fill_value=-1)
        for candidate_i, target_is in indexes.items():
            if candidate_i != -1:
                optimal_indexes[target_is[0]] = candidate_i

        if -1 in indexes:
            # fill up remaining slots with target_i which didn't match (candidate_1 == -1)
            for target_i in indexes[-1]:
                for i, item in enumerate(optimal_indexes):
                    if item == -1:
                        optimal_indexes[i] = target_i

        return optimal_indexes.tolist()

    def _optional_calc_is_done(self, indexes: dict[int, list[int]]) -> bool:
        for i, l in indexes.items():
            if i != -1 and len(l) > 1:
                return False
        return True

    def _optional_calc_get_next_index(self, indexes: dict[int, list[int]]) -> int:
        for i in indexes.keys():
            if i != -1 and len(indexes[i]) > 1:
                return i

        raise RuntimeError()

def _contains_duplicates(arr: list[np.intp]) -> bool:
    seen = set()

    for item in arr:
        if item in seen:
            return True

        seen.add(item)

    return False

def _alg_with_index(data: np.ndarray, combined_score: float) -> tuple[float, list[int]]:
    """
    I have no idea what to call this algorithm.

    It generates all unique combinations of a 2d input array such that in each combination,
    each row and each column only occurs once.

    This process is done recursively and is quite costly,
    as the number of combinations equals !n, where n is (number of rows / number of columns).
    """

    if data.shape[0] == 1:
        # take the maximum score of all current scores
        index = int(data.argmax())
        if data[0][index] > 0.0:
            return (combined_score + data[0][index], [index])
        return (combined_score, [-1])

    max_score, max_indexes = _alg_with_index(_reduce(data, 0), combined_score + data[0][0])
    max_row_index = 0
    for row_index in range(1, data.shape[0]):
        reduced_data = _reduce(data, row_index)

        score, indexes = _alg_with_index(reduced_data, combined_score + data[row_index][0])

        # branching with if is much faster than max, because max_score only rarely changes
        # pylint: disable-next=consider-using-max-builtin
        if score > max_score:
            max_score = score
            max_indexes = indexes
            max_row_index = row_index

    # shift indexes
    for i, item in enumerate(max_indexes):
        if item != -1:
            max_indexes[i] = item + 1

    # store current index
    if data[max_row_index][0] != 0.0:
        max_indexes.insert(max_row_index, 0)
    else:
        max_indexes.insert(max_row_index, -1)

    return (max_score, max_indexes)

def _reduce(data: np.ndarray, r_index: int) -> np.ndarray:
    new_array = np.empty((data.shape[0] - 1, data.shape[1] - 1))

    row_i = 0
    for orig_row_i in range(data.shape[0]):
        if orig_row_i != r_index:
            # we can copy the whole row, excluding the first element
            new_array[row_i] = data[orig_row_i][1:]
            row_i += 1

    return new_array

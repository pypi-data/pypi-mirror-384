"""A module containing the levenshtein_distance function"""

import numpy

from abllib.error import WrongTypeError

def levenshtein_distance(token1: str, token2: str) -> int:
    """
    Calculate the levenshtein distance between token1 and token2

    This represents the edit distance between two strings
    """

    if not isinstance(token1, str):
        raise WrongTypeError.with_values(token1, str)
    if not isinstance(token2, str):
        raise WrongTypeError.with_values(token2, str)

    distances = numpy.zeros((len(token1) + 1, len(token2) + 1), dtype=int)

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    a = 0
    b = 0
    c = 0

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1-1] == token2[t2-1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]

                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    final_dist = distances[len(token1)][len(token2)]
    # cast np.int64 to int
    return final_dist.item()

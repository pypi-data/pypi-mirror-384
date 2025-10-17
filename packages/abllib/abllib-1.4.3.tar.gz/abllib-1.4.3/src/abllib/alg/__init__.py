"""A module containing general-purpose algorithms"""

from typing import Callable

from abllib.general import try_import_module

Levenshtein = try_import_module("Levenshtein")

# mypy: disable-error-code="no-redef"

if Levenshtein is None:
    from abllib.alg._levenshtein import levenshtein_distance
else:
    # use C implementation
    levenshtein_distance = Levenshtein.distance

levenshtein_distance: Callable[[str, str], int]

__exports__ = [
    levenshtein_distance
]

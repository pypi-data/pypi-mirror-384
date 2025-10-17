"""Module containing the MatchResult dataclass"""

from dataclasses import dataclass

@dataclass
class MatchResult():
    """Dataclass representing a single matched candidate"""

    score: float
    value: str | tuple[str, ...] | None = None
    index: int | None = None
    inner_index: int | None = None

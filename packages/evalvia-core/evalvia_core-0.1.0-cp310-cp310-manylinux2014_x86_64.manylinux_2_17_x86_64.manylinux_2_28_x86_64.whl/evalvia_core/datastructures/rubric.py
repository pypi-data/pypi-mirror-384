from dataclasses import dataclass, field
from typing import List

@dataclass
class Criterion:
    """
    Represents a single criterion in a rubric.
    """
    statement: str
    mark: float
    is_fulfilled: bool = field(default=False)

    def __post_init__(self):
        if self.mark < 0:
            raise ValueError("Mark must be non-negative.")

    def set_fulfill(self, fulfilled: bool):
        if not isinstance(fulfilled, bool):
            raise TypeError("fulfilled must be a bool")
        self.is_fulfilled = fulfilled

    def __repr__(self):
        return f"Criterion(statement={self.statement!r}, mark={self.mark}, is_fulfilled={self.is_fulfilled})"


class Rubric:
    """
    Represents a rubric consisting of multiple criteria.
    """
    def __init__(self, criteria: List[Criterion]):
        if not all(isinstance(c, Criterion) for c in criteria):
            raise TypeError("All items in criteria must be instances of Criterion.")
        self._criteria = criteria

    @property
    def criteria(self) -> List[Criterion]:
        return self._criteria

    def add_criterion(self, criterion: Criterion) -> None:
        if not isinstance(criterion, Criterion):
            raise TypeError("criterion must be an instance of Criterion")
        self._criteria.append(criterion)

    def total_marks(self) -> float:
        return sum(c.mark for c in self._criteria)

    def awarded_marks(self) -> float:
        return sum(c.mark for c in self._criteria if c.is_fulfilled)
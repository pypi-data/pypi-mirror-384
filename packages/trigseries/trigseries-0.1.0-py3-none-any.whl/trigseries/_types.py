from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TypeAlias


@dataclass(frozen=True)
class SeriesInfo:
    """
    error_estimate : Optional[float]
        Magnitude of the first neglected term (simple bound on truncation error),
        if available; otherwise ``None``.
    n_terms : Optional[int]
        Number of terms included in the partial sum, if applicable; otherwise ``None``.
    capped : Optional[bool]
        Whether the computation hit the ``max_terms`` cap rather than the tolerance.
    """

    error_estimate: Optional[float]
    n_terms: Optional[int]
    capped: Optional[bool]


# Public result type when returning metadata alongside a scalar value
SeriesResult: TypeAlias = tuple[float, SeriesInfo]

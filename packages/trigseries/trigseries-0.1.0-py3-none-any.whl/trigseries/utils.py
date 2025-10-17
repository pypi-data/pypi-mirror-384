"""
For Trig.:

``reduce_angle`` maps any real angle to a small range around 0 so the
Maclaurin series behave nicely. Note: for very large ``abs(x)`` we are still
limited by ``float64`` precision when subtracting multiples of π/2.
"""

from __future__ import annotations

import math
from typing import Final

# Half pi as a handy constant for quadrant math
HALF_PI: Final[float] = math.pi / 2.0


def reduce_angle(x: float) -> float:
    """
    Map x (radians) into a small "safe" interval near 0.

    Idea:
    - Work out how many half–pis (π/2) fit in x: q ≈ round(x/(π/2)).
    - Subtract that many half–pis: y = x - q*(π/2).

    This keeps ``y`` small (about ``[-π/4, π/4]``) so the series for sin/cos
    converges fast.

    Caveat: for very large ``abs(x)``, ``float64`` cannot represent multiples
    of π/2 exactly, so ``y`` may pick up tiny rounding error.

    Parameters
    ----------
    x : float
        Angle in radians.

    Returns
    -------
    float
        Reduced angle y ≈ x modulo (π/2), typically in [-π/4, π/4].
    """
    # how many half–pis fit in x
    q: int = int(round(x / HALF_PI))
    # subtract that many to keep the angle small
    y: float = x - q * HALF_PI
    return y


def _reduce_with_quadrant(x: float) -> tuple[float, int]:
    """
    Like `reduce_angle`, but also return q mod 4 (which π/2 quadrant we were in).

    Useful for putting signs back when rebuilding sin/cos/tan after series eval.

    Returns
    -------
    (y, q_mod4)
    """
    q: int = int(round(x / HALF_PI))
    y: float = x - q * HALF_PI
    return y, (q % 4)


def series_term(name: str, n: int, x: float) -> float:
    """
    Return the nth Maclaurin term a_n(x) for a series at x.
    Here sinc(x) = sin(x)/x, with a_0 = 1 and only even powers after that.
    """
    if n < 0:
        raise ValueError("n must be non-negative")

    series = name.strip().lower()

    def factorial_as_float(k: int) -> float:
        result = 1.0
        if k <= 1:
            return result
        for i in range(2, k + 1):
            result *= float(i)
        return result

    if series == "exp":
        return (x**n) / factorial_as_float(n)

    if series == "sin":
        power = 2 * n + 1
        sign = (-1.0) ** n
        return sign * (x**power) / factorial_as_float(power)

    if series == "cos":
        power = 2 * n
        sign = (-1.0) ** n
        return sign * (x**power) / factorial_as_float(power)

    if series == "sinc":
        power = 2 * n
        sign = (-1.0) ** n
        return sign * (x**power) / factorial_as_float(2 * n + 1)

    raise ValueError(f"Unsupported series name: {name}")

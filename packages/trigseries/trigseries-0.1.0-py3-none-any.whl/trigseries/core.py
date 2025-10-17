from __future__ import annotations

from typing import Tuple, overload

from .utils import _reduce_with_quadrant, HALF_PI
from ._types import SeriesInfo, SeriesResult


def _sin_series(
    y: float, tol: float = 1e-12, max_terms: int = 1000
) -> Tuple[float, float, int, bool]:
    """
    sin(y) via the Maclaurin series with a stop rule.

    Builds terms iteratively (no factorial calls) and stops when the next term
    is tiny relative to the current partial sum. Caps the number of terms as a
    safeguard. Returns `(value, error_estimate, n_terms)`.
    """
    # Maclaurin: sin(y) = sum_{k=0..∞} (-1)^k y^{2k+1}/(2k+1)!
    # Iterate terms via recurrence to avoid factorials.
    term = y  # first term (k=0)
    running_sum = term
    k = 0  # term index

    # Termination based on |next_term| < tol * max(1, |sum|)
    # It will compute next_term from current term to assess stopping.
    capped = False
    while True:
        # Prepare next term using recurrence: t_{k+1} = -t_k * y^2 / ((2k+2)(2k+3))
        denom = (2 * k + 2) * (2 * k + 3)
        next_term = -term * (y * y) / denom

        # Check termination criterion relative to current partial sum
        if abs(next_term) < tol * max(1.0, abs(running_sum)):
            error_estimate = abs(next_term)
            break

        running_sum += next_term
        term = next_term
        k += 1

        if k + 1 >= max_terms:
            # Cap reached; use last term magnitude as error estimate
            error_estimate = abs(term)
            capped = True
            break

    n_terms = k + 1  # number of terms used
    return running_sum, error_estimate, n_terms, capped


def _cos_series(
    y: float, tol: float = 1e-12, max_terms: int = 1000
) -> Tuple[float, float, int, bool]:
    """
    cos(y) via the Maclaurin series with a stop rule.

    Uses iterative recurrence (no factorial calls). Returns
    ``(value, error_estimate, n_terms, capped)``.
    """
    # Maclaurin: cos(y) = sum_{k=0..∞} (-1)^k y^{2k}/(2k)!
    term = 1.0  # k=0
    running_sum = term
    k = 0

    capped = False
    while True:
        # t_{k+1} = -t_k * y^2 / ((2k+1)(2k+2))
        denom = (2 * k + 1) * (2 * k + 2)
        next_term = -term * (y * y) / denom

        if abs(next_term) < tol * max(1.0, abs(running_sum)):
            error_estimate = abs(next_term)
            break

        running_sum += next_term
        term = next_term
        k += 1

        if k + 1 >= max_terms:
            error_estimate = abs(term)
            capped = True
            break

    n_terms = k + 1
    return running_sum, error_estimate, n_terms, capped


def _sinc_series(
    y: float, tol: float = 1e-12, max_terms: int = 1000
) -> Tuple[float, float, int, bool]:
    """
    Formula: sinc(y) = sin(y)/y = sum_{k=0..∞} (-1)^k y^{2k}/(2k+1)!
    Iterate terms via recurrence to avoid factorials.

    Returns `(value, error_estimate, n_terms)`.
    """
    # First term (k=0) is 1
    term = 1.0
    running_sum = term
    k = 0

    capped = False
    while True:
        # t_{k+1} = -t_k * y^2 / ((2k+2)(2k+3))
        denom = (2 * k + 2) * (2 * k + 3)
        next_term = -term * (y * y) / denom

        if abs(next_term) < tol * max(1.0, abs(running_sum)):
            error_estimate = abs(next_term)
            break

        running_sum += next_term
        term = next_term
        k += 1

        if k + 1 >= max_terms:
            error_estimate = abs(term)
            capped = True
            break

    n_terms = k + 1
    return running_sum, error_estimate, n_terms, capped


def _exp_series(
    x: float, tol: float = 1e-12, max_terms: int = 1000
) -> Tuple[float, float, int, bool]:
    """
    exp(x) via the Maclaurin series with a stop rule.

    Builds terms iteratively (no factorial calls) and stops when the next term
    is tiny relative to the current partial sum. Caps the number of terms as a
    safeguard. Returns `(value, error_estimate, n_terms)`.
    """
    # Maclaurin: exp(x) = sum_{k=0..∞} x^k/k!
    # Iterate terms via recurrence to avoid factorials.
    term = 1.0  # first term (k=0)
    running_sum = term
    k = 0  # term index

    capped = False
    while True:
        # Recurrence: t_{k+1} = t_k * x / (k+1)
        next_term = term * (x / (k + 1))

        if abs(next_term) < tol * max(1.0, abs(running_sum)):
            error_estimate = abs(next_term)
            break

        running_sum += next_term
        term = next_term
        k += 1

        if k + 1 >= max_terms:
            error_estimate = abs(term)
            capped = True
            break

    n_terms = k + 1
    return running_sum, error_estimate, n_terms, capped


@overload
def exp(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False
) -> float: ...


@overload
def exp(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = True
) -> SeriesResult: ...


def exp(x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False):
    """
    Compute exp(x) with a Maclaurin series using iterative term updates.

    Stop rule: ``abs(next_term) < tol * max(1, abs(partial_sum))``.
    """
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")

    value, err, n_terms, capped = _exp_series(x, tol=tol, max_terms=max_terms)
    if return_info:
        return value, SeriesInfo(error_estimate=err, n_terms=n_terms, capped=capped)
    return value


@overload
def sin(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False
) -> float: ...


@overload
def sin(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = True
) -> SeriesResult: ...


def sin(x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False):
    """
    Compute sin(x) with reduction and a Maclaurin series on the reduced value.

    Uses π/2 quadrants to rebuild signs and `cos(y) = sin(π/2 - y)`.
    """
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")

    y, q_mod4 = _reduce_with_quadrant(x)
    s_y, err_s, n_s, cap_s = _sin_series(y, tol=tol, max_terms=max_terms)
    c_y, err_c, n_c, cap_c = _cos_series(y, tol=tol, max_terms=max_terms)

    if q_mod4 == 0:
        value = s_y
        info = SeriesInfo(error_estimate=err_s, n_terms=n_s, capped=cap_s)
    elif q_mod4 == 1:
        value = c_y
        info = SeriesInfo(error_estimate=err_c, n_terms=n_c, capped=cap_c)
    elif q_mod4 == 2:
        value = -s_y
        info = SeriesInfo(error_estimate=err_s, n_terms=n_s, capped=cap_s)
    else:  # q_mod4 == 3
        value = -c_y
        info = SeriesInfo(error_estimate=err_c, n_terms=n_c, capped=cap_c)

    if return_info:
        return value, info
    return value


@overload
def sinc(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    small_x_threshold: float = 1e-4,
    return_info: bool = False,
) -> float: ...


@overload
def sinc(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    small_x_threshold: float = 1e-4,
    return_info: bool = True,
) -> SeriesResult: ...


def sinc(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    small_x_threshold: float = 1e-4,
    return_info: bool = False,
):
    """
    Normalized sinc: sinc(x) = sin(x)/x with stable handling at x≈0.

    Behaviour:
    - ``x == 0`` → 1.0 (series limit)
    - ``abs(x) < small_x_threshold`` → evaluate via the Maclaurin series for improved stability
    - otherwise compute ``sin(x)/x`` using the reduced-angle sine
    """
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")

    if x == 0.0:
        if return_info:
            return 1.0, SeriesInfo(error_estimate=0.0, n_terms=0, capped=False)
        return 1.0

    if abs(x) < small_x_threshold:
        value, err, n_terms, capped = _sinc_series(x, tol=tol, max_terms=max_terms)
        if return_info:
            return value, SeriesInfo(error_estimate=err, n_terms=n_terms, capped=capped)
        return value

    sin_value, sin_info = sin(x, tol=tol, max_terms=max_terms, return_info=True)
    value = sin_value / x
    if return_info:
        # error(|f/x|) <= error(|f|)/|x|
        err = (abs(sin_info.error_estimate) if sin_info.error_estimate is not None else 0.0) / abs(
            x
        )
        capped = bool(sin_info.capped)
        return value, SeriesInfo(error_estimate=err, n_terms=sin_info.n_terms, capped=capped)
    return value


@overload
def tan(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    pole_threshold: float = 1e-12,
    return_info: bool = False,
) -> float: ...


@overload
def tan(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    pole_threshold: float = 1e-12,
    return_info: bool = True,
) -> SeriesResult: ...


def tan(
    x: float,
    tol: float = 1e-12,
    max_terms: int = 1000,
    pole_threshold: float = 1e-12,
    return_info: bool = False,
):
    """
    tan(x) via sin/cos with the reduced-angle series.

    Raises if ``abs(cos(x))`` is too small (near poles).
    """
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")

    y, q_mod4 = _reduce_with_quadrant(x)
    s_y, err_sy, n_sy, cap_sy = _sin_series(y, tol=tol, max_terms=max_terms)
    c_y, err_cy, n_cy, cap_cy = _cos_series(y, tol=tol, max_terms=max_terms)

    # Map (s_y, c_y) to full-angle (sin, cos) using quadrant
    if q_mod4 == 0:
        s_x, c_x = s_y, c_y
        err_sx, err_cx = err_sy, err_cy
        n_sx, n_cx = n_sy, n_cy
        cap_sx, cap_cx = cap_sy, cap_cy
    elif q_mod4 == 1:
        s_x, c_x = c_y, -s_y
        err_sx, err_cx = err_cy, err_sy
        n_sx, n_cx = n_cy, n_sy
        cap_sx, cap_cx = cap_cy, cap_sy
    elif q_mod4 == 2:
        s_x, c_x = -s_y, -c_y
        err_sx, err_cx = err_sy, err_cy
        n_sx, n_cx = n_sy, n_cy
        cap_sx, cap_cx = cap_sy, cap_cy
    else:  # q_mod4 == 3
        s_x, c_x = -c_y, s_y
        err_sx, err_cx = err_cy, err_sy
        n_sx, n_cx = n_cy, n_sy
        cap_sx, cap_cx = cap_cy, cap_sy

    if abs(c_x) < pole_threshold:
        raise ValueError("tan undefined near (π/2 + kπ): |cos(x)| too small")

    value = s_x / c_x
    if return_info:
        # First-order propagation: d(s/c) ≈ (ds)/c + s * (dc)/c^2
        err = abs(err_sx / c_x) + abs((s_x * err_cx) / (c_x * c_x))
        capped = bool(cap_sx or cap_cx)
        n_terms = max(n_sx, n_cx)
        return value, SeriesInfo(error_estimate=err, n_terms=n_terms, capped=capped)
    return value


@overload
def cos(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False
) -> float: ...


@overload
def cos(
    x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = True
) -> SeriesResult: ...


def cos(x: float, tol: float = 1e-12, max_terms: int = 1000, return_info: bool = False):
    """
    cos(x) via sine: cos(x) = sin(π/2 - x).

    Thin wrapper around sin with a phase shift.
    """
    if max_terms <= 0:
        raise ValueError("max_terms must be positive")

    # Delegate to sin with phase shift
    return sin(HALF_PI - x, tol=tol, max_terms=max_terms, return_info=return_info)

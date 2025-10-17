import math

from trigseries import reduce_angle, series_term


def test_reduce_angle_within_primary_interval_and_quasi_periodicity():
    # Values spaced by multiples of π/2 should reduce to nearly same y
    base = 0.3
    y0 = reduce_angle(base)
    for k in range(-5, 6):
        yk = reduce_angle(base + k * (math.pi / 2))
        assert math.isclose(y0, yk, rel_tol=0, abs_tol=1e-12)


def test_series_term_basic_sequences():
    # exp: sum x^n/n!
    x = 0.5
    assert series_term("exp", 0, x) == 1.0
    assert math.isclose(series_term("exp", 1, x), x)
    # sin: odd powers with alternating signs
    assert series_term("sin", 0, x) == x
    assert math.isclose(series_term("sin", 1, x), -(x**3) / 6)
    # cos: even powers with alternating signs
    assert series_term("cos", 0, x) == 1.0
    assert math.isclose(series_term("cos", 1, x), -(x**2) / 2)
    # sinc: a_0 = 1 and only even powers thereafter divided by (2n+1)!
    assert series_term("sinc", 0, x) == 1.0
    assert math.isclose(series_term("sinc", 1, x), -(x**2) / 6)


def test_series_term_errors():
    # n negative
    try:
        series_term("exp", -1, 0.0)
        assert False, "expected ValueError"
    except ValueError:
        pass

    # unsupported name
    try:
        series_term("unknown", 0, 0.0)
        assert False, "expected ValueError"
    except ValueError:
        pass

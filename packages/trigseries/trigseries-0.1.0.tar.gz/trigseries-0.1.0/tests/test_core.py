from trigseries import sin, cos, tan, sinc, exp
import pytest
import math


def test_sin_cos_identity_small_grid():
    xs = [i * 0.1 for i in range(-20, 21)]
    for x in xs:
        s = sin(x)
        c = cos(x)
        assert abs(s * s + c * c - 1.0) < 1e-9


def test_cos_equals_shifted_sin():
    xs = [i * 0.2 for i in range(-10, 11)]
    for x in xs:
        assert math.isclose(cos(x), sin(math.pi / 2 - x), rel_tol=0, abs_tol=1e-12)


@pytest.mark.parametrize("x", [i * 0.2 for i in range(-10, 11)])
def test_cos_equals_shifted_sin_parametrized(x):
    assert math.isclose(cos(x), sin(math.pi / 2 - x), rel_tol=0, abs_tol=1e-12)


def test_tan_near_zero_matches_math():
    xs = [i * 1e-3 for i in range(-5, 6)]
    for x in xs:
        assert math.isclose(tan(x), math.tan(x), rel_tol=1e-9, abs_tol=1e-12)


def test_sinc_zero_and_evenness_and_match():
    # zero case
    assert sinc(0.0) == 1.0

    # evenness: sinc(-x) == sinc(x)
    xs = [i * 1e-3 for i in range(1, 11)]
    for x in xs:
        assert math.isclose(sinc(-x), sinc(x), rel_tol=0, abs_tol=1e-15)

    # compare to sin(x)/x away from 0
    xs2 = [i * 0.1 for i in range(1, 51)]  # 0.1 .. 5.0
    for x in xs2:
        assert math.isclose(sinc(x), math.sin(x) / x, rel_tol=1e-10, abs_tol=1e-12)


def test_exp_matches_math_on_moderate_grid():
    xs = [i * 0.5 for i in range(-10, 11)]  # -5.0 .. 5.0
    for x in xs:
        assert math.isclose(exp(x), math.exp(x), rel_tol=1e-12, abs_tol=1e-12)


def test_exp_zero_is_one_exact():
    assert exp(0.0) == 1.0


def test_exp_tolerance_monotonic_improvement():
    x = 3.0
    err_loose = abs(exp(x, tol=1e-6) - math.exp(x))
    err_tight = abs(exp(x, tol=1e-12) - math.exp(x))
    assert err_tight <= err_loose


def test_exp_additivity_property_small_values():
    # e^{x+y} = e^x * e^y; check for small values where truncation is mild
    for i in range(-10, 11):
        x = i / 10.0
        for j in range(-10, 11):
            y = j / 10.0
            lhs = exp(x + y)
            rhs = exp(x) * exp(y)
            assert math.isclose(lhs, rhs, rel_tol=1e-11, abs_tol=1e-12)

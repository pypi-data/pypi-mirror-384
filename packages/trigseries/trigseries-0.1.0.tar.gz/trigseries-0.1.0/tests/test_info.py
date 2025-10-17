import math

import pytest

from trigseries import sin, cos, tan, sinc, exp


@pytest.mark.parametrize(
    "func,arg",
    [
        (sin, 0.3),
        (cos, 1.0),
        (tan, 0.1),
        (sinc, 0.2),
        (exp, 0.7),
    ],
)
def test_return_info_meta(func, arg):
    # All public APIs accept return_info=True and provide SeriesInfo metadata
    value1 = func(arg)
    value2, meta = func(arg, return_info=True)  # type: ignore[arg-type]
    assert math.isclose(value1, value2, rel_tol=0, abs_tol=1e-15)
    assert meta.n_terms is None or meta.n_terms > 0
    # error_estimate should be non-negative
    assert meta.error_estimate is None or meta.error_estimate >= 0.0


def test_tan_pole_raises():
    # Just inside  π/2 should raise
    with pytest.raises(ValueError):
        tan(math.pi / 2 * 0.999999, pole_threshold=1.0)


def test_capped_series():
    # Force cap by setting max_terms very low
    val, info = exp(10.0, max_terms=3, return_info=True)
    assert info.capped is True
    assert info.n_terms == 3


def test_sinc_zero_with_info():
    val, info = sinc(0.0, return_info=True)
    assert val == 1.0
    assert info.error_estimate == 0.0
    assert info.n_terms == 0
    assert info.capped is False


def test_sinc_small_x_series_branch():
    # Force small |x| series path
    val, info = sinc(1e-5, small_x_threshold=1e-4, return_info=True)
    assert info.n_terms is not None and info.n_terms > 0


def test_sinc_large_x_fallback():
    # Force sin(x)/x fallback path
    val, info = sinc(1.0, small_x_threshold=1e-4, return_info=True)
    assert abs(val - math.sin(1.0) / 1.0) < 1e-10


def test_negative_max_terms_raises():
    with pytest.raises(ValueError):
        exp(1.0, max_terms=0)
    with pytest.raises(ValueError):
        sin(1.0, max_terms=-1)
    with pytest.raises(ValueError):
        cos(1.0, max_terms=0)
    with pytest.raises(ValueError):
        tan(1.0, max_terms=-5)
    with pytest.raises(ValueError):
        sinc(1.0, max_terms=0)

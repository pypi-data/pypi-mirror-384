import math

from trigseries import tan, sinc


def test_tan_raises_near_pole():
    # Near π/2, tan should raise per implementation policy
    x = math.pi / 2
    # Step slightly toward the pole but keep it extremely close
    eps = 1e-15
    try:
        tan(x - eps)
        assert False, "expected ValueError near pole"
    except ValueError:
        pass


def test_sinc_small_x_uses_series_and_is_close_to_one():
    # For small |x| the series path is used; ensure accuracy
    for k in range(1, 10):
        x = k * 1e-6
        val = sinc(x)
        assert math.isclose(val, 1.0 - (x * x) / 6.0, rel_tol=0, abs_tol=1e-12)

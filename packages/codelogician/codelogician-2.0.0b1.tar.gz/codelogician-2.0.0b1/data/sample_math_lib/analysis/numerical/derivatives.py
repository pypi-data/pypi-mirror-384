"""Numerical derivative calculations - Level 4"""

from core.arithmetic import add, divide, multiply, subtract


def numerical_derivative(func, x: float, h: float = 1e-8) -> float:
    """Calculate numerical derivative using central difference."""
    x_plus_h = add(x, h)
    x_minus_h = subtract(x, h)

    f_plus = func(x_plus_h)
    f_minus = func(x_minus_h)

    numerator = subtract(f_plus, f_minus)
    denominator = multiply(2.0, h)

    return divide(numerator, denominator)


def second_derivative(func, x: float, h: float = 1e-6) -> float:
    """Calculate second derivative."""
    x_plus_h = add(x, h)
    x_minus_h = subtract(x, h)

    f_center = func(x)
    f_plus = func(x_plus_h)
    f_minus = func(x_minus_h)

    # f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h²
    numerator = subtract(add(f_plus, f_minus), multiply(2.0, f_center))
    denominator = multiply(h, h)

    return divide(numerator, denominator)

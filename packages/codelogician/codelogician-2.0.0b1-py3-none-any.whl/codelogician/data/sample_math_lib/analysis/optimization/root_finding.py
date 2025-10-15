"""Root finding algorithms - Level 4"""

from analysis.numerical.derivatives import numerical_derivative
from core.arithmetic import add, divide, multiply, subtract
from core.comparison import absolute_value


def bisection_method(func, a: float, b: float, tolerance: float = 1e-6) -> float:
    """Find root using bisection method."""
    if func(a) * func(b) > 0:
        raise ValueError("Function must have opposite signs at endpoints")

    for _ in range(100):  # Maximum iterations
        c = divide(add(a, b), 2.0)
        fc = func(c)

        if absolute_value(fc) < tolerance:
            return c

        if func(a) * fc < 0:
            b = c
        else:
            a = c

        if absolute_value(subtract(b, a)) < tolerance:
            return divide(add(a, b), 2.0)

    return divide(add(a, b), 2.0)


def newton_method(func, x0: float, tolerance: float = 1e-6) -> float:
    """Find root using Newton's method."""
    x = x0

    for _ in range(50):  # Maximum iterations
        fx = func(x)

        if absolute_value(fx) < tolerance:
            return x

        # Calculate derivative numerically
        fpx = numerical_derivative(func, x)

        if absolute_value(fpx) < tolerance:
            raise ValueError("Derivative too close to zero")

        x_new = subtract(x, divide(fx, fpx))

        if absolute_value(subtract(x_new, x)) < tolerance:
            return x_new

        x = x_new

    return x


def find_minimum_golden_section(
    func, a: float, b: float, tolerance: float = 1e-6
) -> float:
    """Find minimum using golden section search."""
    phi = 1.618033988749895  # Golden ratio
    resphi = subtract(2.0, phi)

    # Initial points
    x1 = add(a, multiply(resphi, subtract(b, a)))
    x2 = subtract(b, multiply(resphi, subtract(b, a)))

    f1 = func(x1)
    f2 = func(x2)

    while absolute_value(subtract(b, a)) > tolerance:
        if f1 < f2:
            b = x2
            x2 = x1
            f2 = f1
            x1 = add(a, multiply(resphi, subtract(b, a)))
            f1 = func(x1)
        else:
            a = x1
            x1 = x2
            f1 = f2
            x2 = subtract(b, multiply(resphi, subtract(b, a)))
            f2 = func(x2)

    return divide(add(a, b), 2.0)

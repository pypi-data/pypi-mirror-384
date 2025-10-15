from basic import add, multiply
from math_ops import square


def sum_three(a: float, b: float, c: float) -> float:
    """Add three numbers."""
    return add(add(a, b), c)


def max_of_three(a: float, b: float, c: float) -> float:
    """Find maximum of three numbers."""
    if a >= b and a >= c:
        return a
    elif b >= c:
        return b
    else:
        return c


def circle_area(radius: float) -> float:
    """Calculate area of circle."""
    pi = 3.14159
    return multiply(pi, square(radius))


def is_even(n: int) -> bool:
    """Check if integer is even."""
    return n % 2 == 0

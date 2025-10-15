"""Numerical integration methods - Level 4"""

from core.arithmetic import add, divide, multiply, subtract


def trapezoidal_rule(func, a: float, b: float, n: int = 100) -> float:
    """Calculate definite integral using trapezoidal rule."""
    if n <= 0:
        raise ValueError("Number of intervals must be positive")

    h = divide(subtract(b, a), n)

    # Calculate function values
    values = []
    for i in range(n + 1):
        x = add(a, multiply(i, h))
        values.append(func(x))

    # Apply trapezoidal rule
    total = add(values[0], values[-1])  # First and last terms

    # Add middle terms (multiplied by 2)
    for i in range(1, n):
        total = add(total, multiply(2.0, values[i]))

    return multiply(divide(h, 2.0), total)


def simpson_rule(func, a: float, b: float, n: int = 100) -> float:
    """Calculate definite integral using Simpson's rule."""
    if n % 2 != 0:
        n = n + 1  # Make n even

    h = divide(subtract(b, a), n)

    total = add(func(a), func(b))

    # Odd-indexed terms (coefficient 4)
    for i in range(1, n, 2):
        x = add(a, multiply(i, h))
        total = add(total, multiply(4.0, func(x)))

    # Even-indexed terms (coefficient 2)
    for i in range(2, n, 2):
        x = add(a, multiply(i, h))
        total = add(total, multiply(2.0, func(x)))

    return multiply(divide(h, 3.0), total)

"""Utility functions - Level 3 (depends on multiple packages)"""

from core.advanced import factorial
from core.arithmetic import add, divide, multiply
from stats.basic import mean
from stats.measures import standard_deviation


def polynomial_evaluate(coefficients: list[float], x: float) -> float:
    """Evaluate polynomial at x using Horner's method."""
    if not coefficients:
        return 0.0

    result = coefficients[0]
    for i in range(1, len(coefficients)):
        result = add(multiply(result, x), coefficients[i])

    return result


def combinations(n: int, r: int) -> int:
    """Calculate combinations C(n,r)."""
    if r < 0 or r > n or n < 0:
        return 0

    if r == 0 or r == n:
        return 1

    return int(divide(factorial(n), multiply(factorial(r), factorial(n - r))))


def normalize_data(data: list[float]) -> list[float]:
    """Normalize data to have mean 0 and std 1."""
    if not data:
        return []

    data_mean = mean(data)
    data_std = standard_deviation(data)

    if data_std == 0:
        return [0.0] * len(data)

    normalized = []
    for value in data:
        normalized_value = divide(add(value, multiply(-1.0, data_mean)), data_std)
        normalized.append(normalized_value)

    return normalized

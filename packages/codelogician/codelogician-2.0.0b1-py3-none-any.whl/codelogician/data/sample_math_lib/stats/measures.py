"""Statistical measures - Level 3 (depends on stats.basic and core)"""

from core.advanced import square_root
from core.arithmetic import divide, multiply, subtract

from .basic import mean, sum_list


def variance(numbers: list[float]) -> float:
    """Calculate variance."""
    if not numbers:
        raise ValueError("Cannot calculate variance of empty list")
    if len(numbers) == 1:
        return 0.0

    avg = mean(numbers)
    squared_diffs = []

    for num in numbers:
        diff = subtract(num, avg)
        squared_diff = multiply(diff, diff)
        squared_diffs.append(squared_diff)

    return divide(sum_list(squared_diffs), subtract(len(numbers), 1))


def standard_deviation(numbers: list[float]) -> float:
    """Calculate standard deviation."""
    return square_root(variance(numbers))


def range_value(numbers: list[float]) -> float:
    """Calculate range (max - min)."""
    if not numbers:
        raise ValueError("Cannot calculate range of empty list")

    max_val = numbers[0]
    min_val = numbers[0]

    for num in numbers[1:]:
        if num > max_val:
            max_val = num
        if num < min_val:
            min_val = num

    return subtract(max_val, min_val)

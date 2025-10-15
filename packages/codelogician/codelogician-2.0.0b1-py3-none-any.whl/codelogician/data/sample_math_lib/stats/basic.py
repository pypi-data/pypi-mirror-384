"""Basic statistical operations - Level 2 (depends on core)"""

from core.arithmetic import add, divide
from core.comparison import maximum, minimum


def sum_list(numbers: list[float]) -> float:
    """Calculate sum of a list of numbers."""
    total = 0.0
    for num in numbers:
        total = add(total, num)
    return total


def mean(numbers: list[float]) -> float:
    """Calculate arithmetic mean."""
    if not numbers:
        raise ValueError("Cannot calculate mean of empty list")
    return divide(sum_list(numbers), len(numbers))


def count_values(numbers: list[float]) -> int:
    """Count number of values."""
    return len(numbers)


# check that find_max(numbers) is larger or equal to every value in numbers
def find_max(numbers: list[float]) -> float:
    """Find maximum value in list."""
    if not numbers:
        raise ValueError("Cannot find max of empty list")

    max_val = numbers[0]
    for num in numbers[1:]:
        max_val = maximum(max_val, num)
    return max_val


def find_min(numbers: list[float]) -> float:
    """Find minimum value in list."""
    if not numbers:
        raise ValueError("Cannot find min of empty list")

    min_val = numbers[0]
    for num in numbers[1:]:
        min_val = minimum(min_val, num)
    return min_val

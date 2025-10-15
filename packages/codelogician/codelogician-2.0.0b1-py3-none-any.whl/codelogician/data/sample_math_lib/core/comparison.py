"""Comparison and utility operations - Level 1 (no dependencies)"""


# decompose the function maximum(a, b)
def maximum(a: float, b: float) -> float:
    """Return the maximum of two numbers."""
    return a if a > b else b


# decompose the function minimum(a, b)
def minimum(a: float, b: float) -> float:
    """Return the minimum of two numbers."""
    return a if a < b else b


# decompose the function absolute_value(x)
def absolute_value(x: float) -> float:
    """Return absolute value of x."""
    return x if x >= 0 else -x


# decompose the function sign(x)
def sign(x: float) -> int:
    """Return sign of x (-1, 0, or 1)."""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

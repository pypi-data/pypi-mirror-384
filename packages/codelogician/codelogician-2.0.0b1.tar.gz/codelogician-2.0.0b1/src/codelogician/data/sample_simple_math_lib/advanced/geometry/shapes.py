from basic import add, multiply, is_positive
from utils.helpers import max_of_three


def rectangle_area(width: float, height: float) -> float:
    """Calculate area of rectangle."""
    return multiply(width, height)


def rectangle_perimeter(width: float, height: float) -> float:
    """Calculate perimeter of rectangle."""
    return multiply(2.0, add(width, height))


def square_area(side: float) -> float:
    """Calculate area of square."""
    return multiply(side, side)


def triangle_area(base: float, height: float) -> float:
    """Calculate area of triangle using base and height."""
    half = 0.5
    return multiply(half, multiply(base, height))


def is_valid_triangle(a: float, b: float, c: float) -> bool:
    """Check if three sides can form a valid triangle."""
    all_positive = is_positive(a) and is_positive(b) and is_positive(c)
    triangle_inequality = (
        add(a, b) > c and
        add(b, c) > a and
        add(a, c) > b
    )
    return all_positive and triangle_inequality


def max_side_length(a: float, b: float, c: float) -> float:
    """Find the maximum side length among three sides."""
    return max_of_three(a, b, c)
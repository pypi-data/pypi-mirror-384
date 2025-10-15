from basic import add, absolute, multiply, subtract, is_positive


def square(x: float) -> float:
    """Calculate square of x."""
    return multiply(x, x)


def cube(x: float) -> float:
    """Calculate cube of x."""
    return multiply(multiply(x, x), x)



def distance_1d(x1: float, x2: float) -> float:
    """Calculate distance between two points on a line."""
    return absolute(subtract(x2, x1))


def average(a: float, b: float) -> float:
    """Calculate average of two numbers."""
    return multiply(add(a, b), 0.5)


def sum_of_squares(a: float, b: float) -> float:
    """Calculate sum of squares of two numbers."""
    return add(square(a), square(b))


def is_negative(x: float) -> bool:
    """Check if number is negative."""
    return not is_positive(x) and x != 0


def sign(x: float) -> float:
    """Return sign of number: 1.0 for positive, -1.0 for negative, 0.0 for zero."""
    if is_positive(x):
        return 1.0
    elif x == 0:
        return 0.0
    else:
        return -1.0
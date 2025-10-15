def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def is_positive(x: float) -> bool:
    """Check if number is positive."""
    return x > 0


def absolute(x: float) -> float:
    """Return absolute value."""
    return x if x >= 0 else -x

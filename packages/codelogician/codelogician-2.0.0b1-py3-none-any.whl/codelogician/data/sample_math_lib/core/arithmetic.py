"""Basic arithmetic operations - Level 1 (no dependencies)"""


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base**exponent

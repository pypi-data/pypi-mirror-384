"""Advanced mathematical operations - Level 2 (depends on core.arithmetic)"""

from .arithmetic import add, divide, multiply, subtract
from .comparison import absolute_value


def square_root(x: float) -> float:
    """Calculate square root using Newton's method."""
    if x < 0:
        raise ValueError("Square root not defined for negative numbers")
    if x == 0:
        return 0.0

    guess = divide(x, 2.0)

    for _ in range(20):  # Simple iteration limit
        new_guess = divide(add(guess, divide(x, guess)), 2.0)
        if absolute_value(subtract(new_guess, guess)) < 1e-10:
            break
        guess = new_guess

    return new_guess


def factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1

    result = 1
    for i in range(2, n + 1):
        result = int(multiply(result, i))
    return result


def is_even(n: int) -> bool:
    """Check if number is even."""
    return n % 2 == 0


def is_prime(n: int) -> bool:
    """Check if number is prime."""
    if n < 2:
        return False
    return all(n % i != 0 for i in range(2, int(square_root(n)) + 1))

"""Numerical analysis subpackage."""

from .derivatives import numerical_derivative
from .integration import trapezoidal_rule

__all__ = ["numerical_derivative", "trapezoidal_rule"]

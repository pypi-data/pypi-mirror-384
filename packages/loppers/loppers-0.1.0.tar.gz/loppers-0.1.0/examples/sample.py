from abc import ABC, abstractmethod
from typing import Protocol

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

class Arithmetic(ABC):
    """Abstract base class for arithmetic operations."""

    @abstractmethod
    def calculate(self, x: int, y: int) -> int:
        """Calculate operation."""
        pass

class Calculator(Arithmetic):
    """A simple calculator."""

    def __init__(self, name: str):
        """Initialize calculator."""
        self.name = name
        self._initialized = True

    def calculate(self, x: int, y: int) -> int:
        """Calculate sum."""
        return self.add(x, y)

    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        result = x + y
        return result

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        result = x * y
        return result

    def __str__(self) -> str:
        """String representation."""
        return f"Calculator({self.name})"

class AdvancedCalculator(Calculator):
    """Extended calculator with more operations."""

    def power(self, x: int, y: int) -> int:
        """Calculate power."""
        return x ** y

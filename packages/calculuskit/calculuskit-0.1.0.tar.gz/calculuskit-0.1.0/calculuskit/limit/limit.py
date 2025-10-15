"""Limit class module."""

from typing import Callable, Literal, Optional

import numpy as np


class Limit:
    """Class-based interface for calculating limits."""

    def __init__(self, func: Callable[[float], float], epsilon: float = 1e-10) -> None:
        """
        Initialize a Limit calculator for a function.

        Args:
            func: The function to evaluate
            epsilon: Small value to approach the point

        Examples:
            >>> def f(x): return (x**2 - 1) / (x - 1)
            >>> lim = Limit(f)
            >>> lim.at(1.0)
            2.0
        """
        self.func = func
        self.epsilon = epsilon

    def at(self, x0: float, direction: Literal["left", "right", "both"] = "both") -> float:
        """
        Calculate the limit at a specific point.

        Args:
            x0: The point to approach
            direction: Direction to approach from

        Returns:
            The limit value
        """
        if direction == "right":
            return self.func(x0 + self.epsilon)
        elif direction == "left":
            return self.func(x0 - self.epsilon)
        elif direction == "both":
            left_limit = self.func(x0 - self.epsilon)
            right_limit = self.func(x0 + self.epsilon)
            if np.isclose(left_limit, right_limit, rtol=1e-5):
                return (left_limit + right_limit) / 2
            else:
                raise ValueError(f"Left and right limits differ: {left_limit} != {right_limit}")
        else:
            raise ValueError(f"Unknown direction: {direction}")

    def left(self, x0: float) -> float:
        """
        Calculate the left-hand limit.

        Args:
            x0: The point to approach from the left

        Returns:
            The left-hand limit value
        """
        return self.at(x0, "left")

    def right(self, x0: float) -> float:
        """
        Calculate the right-hand limit.

        Args:
            x0: The point to approach from the right

        Returns:
            The right-hand limit value
        """
        return self.at(x0, "right")

    def exists(self, x0: float) -> bool:
        """
        Check if the limit exists at a point.

        Args:
            x0: The point to check

        Returns:
            True if the limit exists, False otherwise
        """
        try:
            self.at(x0, "both")
            return True
        except ValueError:
            return False

    def is_continuous(self, x0: float) -> bool:
        """
        Check if the function is continuous at a point.

        Args:
            x0: The point to check

        Returns:
            True if continuous, False otherwise
        """
        try:
            lim_val = self.at(x0, "both")
            func_val = self.func(x0)
            return bool(np.isclose(lim_val, func_val, rtol=1e-5))
        except (ValueError, ZeroDivisionError, OverflowError):
            return False

    def as_x_approaches_infinity(
        self, direction: Literal["positive", "negative"] = "positive"
    ) -> Optional[float]:
        """
        Calculate the limit as x approaches infinity.

        Args:
            direction: 'positive' for +infinity, 'negative' for -infinity

        Returns:
            The limit value if it exists, None otherwise
        """
        large_value = 1e10 if direction == "positive" else -1e10
        try:
            return self.func(large_value)
        except (ZeroDivisionError, OverflowError):
            return None

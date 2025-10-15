"""Derivative class module."""

from typing import Callable, Literal

import numpy as np


class Derivative:
    """Class-based interface for calculating derivatives."""

    def __init__(
        self,
        func: Callable[[float], float],
        h: float = 1e-7,
        method: Literal["forward", "backward", "central"] = "central",
    ) -> None:
        """
        Initialize a Derivative calculator for a function.

        Args:
            func: The function to differentiate
            h: The step size for numerical differentiation
            method: The method to use ('forward', 'backward', or 'central')

        Examples:
            >>> def f(x): return x**2
            >>> df = Derivative(f)
            >>> df.at(3.0)
            6.0
        """
        self.func = func
        self.h = h
        self.method = method

    def at(self, x: float) -> float:
        """
        Calculate the derivative at a specific point.

        Args:
            x: The point at which to calculate the derivative

        Returns:
            The derivative value at point x
        """
        if self.method == "forward":
            return (self.func(x + self.h) - self.func(x)) / self.h
        elif self.method == "backward":
            return (self.func(x) - self.func(x - self.h)) / self.h
        elif self.method == "central":
            return (self.func(x + self.h) - self.func(x - self.h)) / (2 * self.h)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def __call__(self, x: float) -> float:
        """
        Allow calling the derivative object as a function.

        Args:
            x: The point at which to calculate the derivative

        Returns:
            The derivative value at point x
        """
        return self.at(x)

    def gradient(
        self, x: float, dx: float = 0.1, n_points: int = 100
    ) -> tuple[list[float], list[float]]:
        """
        Calculate derivative values over a range of points.

        Args:
            x: Center point
            dx: Range around the center point
            n_points: Number of points to calculate

        Returns:
            Tuple of (x_values, derivative_values)
        """
        x_vals = np.linspace(x - dx, x + dx, n_points)
        deriv_vals = [self.at(xi) for xi in x_vals]
        return x_vals.tolist(), deriv_vals

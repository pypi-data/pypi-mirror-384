"""Integral class module."""

from typing import Callable, Literal

import numpy as np


class Integral:
    """Class-based interface for calculating integrals."""

    def __init__(
        self,
        func: Callable[[float], float],
        n: int = 1000,
        method: Literal["trapezoidal", "simpson", "midpoint"] = "simpson",
    ) -> None:
        """
        Initialize an Integral calculator for a function.

        Args:
            func: The function to integrate
            n: Number of subdivisions
            method: Integration method ('trapezoidal', 'simpson', or 'midpoint')

        Examples:
            >>> def f(x): return x**2
            >>> integral = Integral(f)
            >>> integral.between(0, 1)
            0.333...
        """
        self.func = func
        self.n = n
        self.method = method

    def _integrate(self, a: float, b: float) -> float:
        """
        Internal integration method.

        Args:
            a: Lower bound
            b: Upper bound

        Returns:
            The integral value
        """
        n = self.n
        method = self.method

        if method == "trapezoidal":
            x = np.linspace(a, b, n + 1)
            y = np.array([self.func(xi) for xi in x])
            h = (b - a) / n
            return float(h * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1]))

        elif method == "simpson":
            if n % 2 != 0:
                n += 1  # Simpson's rule requires even number of intervals
            x = np.linspace(a, b, n + 1)
            y = np.array([self.func(xi) for xi in x])
            h = (b - a) / n
            return float((h / 3) * (y[0] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-1:2]) + y[-1]))

        elif method == "midpoint":
            x = np.linspace(a, b, n + 1)
            midpoints = (x[:-1] + x[1:]) / 2
            y = np.array([self.func(xi) for xi in midpoints])
            h = (b - a) / n
            return h * np.sum(y)

        else:
            raise ValueError(f"Unknown method: {method}")

    def between(self, a: float, b: float) -> float:
        """
        Calculate the definite integral between two bounds.

        Args:
            a: Lower bound
            b: Upper bound

        Returns:
            The integral value
        """
        return self._integrate(a, b)

    def definite(self, a: float, b: float) -> float:
        """
        Alias for between method.

        Args:
            a: Lower bound
            b: Upper bound

        Returns:
            The integral value
        """
        return self.between(a, b)

    def cumulative(
        self, a: float, b: float, num_points: int = 100
    ) -> tuple[list[float], list[float]]:
        """
        Calculate cumulative integral values over a range.

        Args:
            a: Starting point
            b: Ending point
            num_points: Number of points to calculate

        Returns:
            Tuple of (x_values, cumulative_integral_values)
        """
        x_vals = np.linspace(a, b, num_points)
        cumulative_vals = [self.between(a, xi) for xi in x_vals]
        return x_vals.tolist(), cumulative_vals

    def average_value(self, a: float, b: float) -> float:
        """
        Calculate the average value of the function over an interval.

        Args:
            a: Lower bound
            b: Upper bound

        Returns:
            Average value of the function
        """
        return self.between(a, b) / (b - a)

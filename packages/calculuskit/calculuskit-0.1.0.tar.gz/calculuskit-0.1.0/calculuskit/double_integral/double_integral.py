"""Double integral class module."""

from typing import Callable, Literal

import numpy as np


class DoubleIntegral:
    """Class-based interface for calculating double integrals."""

    def __init__(
        self,
        func: Callable[[float, float], float],
        n: int = 100,
        method: Literal["trapezoidal", "simpson", "midpoint"] = "simpson",
    ) -> None:
        """
        Initialize a DoubleIntegral calculator for a two-variable function.

        Args:
            func: The two-variable function to integrate
            n: Number of subdivisions per dimension
            method: Integration method

        Examples:
            >>> def f(x, y): return x * y
            >>> dbl_integral = DoubleIntegral(f)
            >>> dbl_integral.over(0, 1, 0, 1)
            0.25
        """
        self.func = func
        self.n = n
        self.method = method

    def _integrate_1d(self, func: Callable[[float], float], a: float, b: float) -> float:
        """
        Internal 1D integration helper method.

        Args:
            func: Function to integrate
            a: Lower bound
            b: Upper bound

        Returns:
            The integral value
        """
        n = self.n
        method = self.method

        if method == "trapezoidal":
            x = np.linspace(a, b, n + 1)
            y = np.array([func(xi) for xi in x])
            h = (b - a) / n
            return float(h * (0.5 * y[0] + np.sum(y[1:-1]) + 0.5 * y[-1]))

        elif method == "simpson":
            if n % 2 != 0:
                n += 1  # Simpson's rule requires even number of intervals
            x = np.linspace(a, b, n + 1)
            y = np.array([func(xi) for xi in x])
            h = (b - a) / n
            return float((h / 3) * (y[0] + 4 * np.sum(y[1:-1:2]) + 2 * np.sum(y[2:-1:2]) + y[-1]))

        elif method == "midpoint":
            x = np.linspace(a, b, n + 1)
            midpoints = (x[:-1] + x[1:]) / 2
            y = np.array([func(xi) for xi in midpoints])
            h = (b - a) / n
            return h * np.sum(y)

        else:
            raise ValueError(f"Unknown method: {method}")

    def over(self, x_min: float, x_max: float, y_min: float, y_max: float) -> float:
        """
        Calculate the double integral over a rectangular region.

        Args:
            x_min: Lower x bound
            x_max: Upper x bound
            y_min: Lower y bound
            y_max: Upper y bound

        Returns:
            The double integral value
        """

        # Inner integral with respect to y
        def inner_integral(x: float) -> float:
            def inner_func(y: float) -> float:
                return self.func(x, y)

            return self._integrate_1d(inner_func, y_min, y_max)

        # Outer integral with respect to x
        return self._integrate_1d(inner_integral, x_min, x_max)

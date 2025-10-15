"""Maclaurin series class module."""

from typing import Callable

from calculuskit.taylor_series.taylor_series import TaylorSeries


class MaclaurinSeries:
    """Class-based interface for Maclaurin series (Taylor series centered at 0)."""

    def __init__(self, func: Callable[[float], float], n: int = 10) -> None:
        """
        Initialize a MaclaurinSeries calculator for a function.

        Args:
            func: The function to expand
            n: Number of terms in the series

        Examples:
            >>> import math
            >>> maclaurin = MaclaurinSeries(math.sin, n=10)
            >>> maclaurin.at(0.5)
            0.479...
        """
        self.func = func
        self.n = n
        self._taylor = TaylorSeries(func, n)

    def at(self, x: float) -> float:
        """
        Evaluate the Maclaurin series at a point.

        Args:
            x: The point at which to evaluate

        Returns:
            The Maclaurin series approximation
        """
        return self._taylor.at(x, center=0.0)

    def coefficients(self) -> list[float]:
        """
        Calculate the Maclaurin series coefficients.

        Returns:
            List of coefficients
        """
        return self._taylor.coefficients(center=0.0)

    def polynomial_string(self) -> str:
        """
        Generate a string representation of the Maclaurin polynomial.

        Returns:
            String representation of the polynomial
        """
        return self._taylor.polynomial_string(center=0.0)

    def error_estimate(self, x: float) -> float:
        """
        Estimate the error of the Maclaurin approximation.

        Args:
            x: The point to evaluate

        Returns:
            Estimated error
        """
        return self._taylor.error_estimate(x, center=0.0)

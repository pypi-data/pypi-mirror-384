"""Fourier series class module."""

from typing import Callable

import numpy as np

from calculuskit.integral.integral import Integral


class FourierSeries:
    """Class-based interface for Fourier series expansions."""

    def __init__(
        self, func: Callable[[float], float], period: float = 2 * np.pi, n: int = 10
    ) -> None:
        """
        Initialize a FourierSeries calculator for a periodic function.

        Args:
            func: The periodic function to expand
            period: The period of the function
            n: Number of harmonics to include

        Examples:
            >>> def square_wave(x): return 1 if x % (2*np.pi) < np.pi else -1
            >>> fourier = FourierSeries(square_wave, period=2*np.pi, n=5)
        """
        self.func = func
        self.period = period
        self.n = n
        self.L = period / 2  # Half period

    def a0(self) -> float:
        """
        Calculate the a0 coefficient (DC component).

        Returns:
            The a0 coefficient
        """
        integral = Integral(self.func, n=1000)
        return (1 / self.period) * integral.between(0, self.period)

    def an(self, n: int) -> float:
        """
        Calculate the nth cosine coefficient.

        Args:
            n: The harmonic number

        Returns:
            The an coefficient
        """

        def integrand(x: float) -> float:
            return float(self.func(x) * np.cos(n * np.pi * x / self.L))

        integral = Integral(integrand, n=1000)
        return (1 / self.L) * integral.between(0, self.period)

    def bn(self, n: int) -> float:
        """
        Calculate the nth sine coefficient.

        Args:
            n: The harmonic number

        Returns:
            The bn coefficient
        """

        def integrand(x: float) -> float:
            return float(self.func(x) * np.sin(n * np.pi * x / self.L))

        integral = Integral(integrand, n=1000)
        return (1 / self.L) * integral.between(0, self.period)

    def at(self, x: float) -> float:
        """
        Evaluate the Fourier series at a point.

        Args:
            x: The point to evaluate

        Returns:
            The Fourier series approximation
        """
        result = self.a0() / 2
        for i in range(1, self.n + 1):
            result += self.an(i) * np.cos(i * np.pi * x / self.L)
            result += self.bn(i) * np.sin(i * np.pi * x / self.L)
        return result

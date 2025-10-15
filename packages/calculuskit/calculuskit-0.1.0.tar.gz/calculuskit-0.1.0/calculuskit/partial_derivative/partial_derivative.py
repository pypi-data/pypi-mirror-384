"""Partial derivative class module."""

from typing import Callable


class PartialDerivative:
    """Class-based interface for calculating partial derivatives."""

    def __init__(self, func: Callable[..., float], h: float = 1e-7) -> None:
        """
        Initialize a PartialDerivative calculator for a multivariable function.

        Args:
            func: The multivariable function
            h: The step size for numerical differentiation

        Examples:
            >>> def f(x, y): return x**2 + y**2
            >>> pdf = PartialDerivative(f)
            >>> pdf.at((2.0, 3.0), 0)  # df/dx at (2, 3)
            4.0
        """
        self.func = func
        self.h = h

    def at(self, point: tuple[float, ...], var_index: int) -> float:
        """
        Calculate the partial derivative at a specific point.

        Args:
            point: The point at which to calculate the partial derivative
            var_index: The index of the variable to differentiate with respect to

        Returns:
            The partial derivative value
        """
        point_plus = list(point)
        point_minus = list(point)
        point_plus[var_index] += self.h
        point_minus[var_index] -= self.h

        return (self.func(*point_plus) - self.func(*point_minus)) / (2 * self.h)

    def gradient_vector(self, point: tuple[float, ...]) -> list[float]:
        """
        Calculate the gradient vector (all partial derivatives) at a point.

        Args:
            point: The point at which to calculate the gradient

        Returns:
            List of partial derivatives for each variable
        """
        return [self.at(point, i) for i in range(len(point))]

    def jacobian(self, point: tuple[float, ...]) -> list[list[float]]:
        """
        Calculate the Jacobian matrix (for vector-valued functions).

        Args:
            point: The point at which to calculate the Jacobian

        Returns:
            Jacobian matrix as a list of lists
        """
        # For single-output function, return gradient as 1xN matrix
        gradient = self.gradient_vector(point)
        return [gradient]

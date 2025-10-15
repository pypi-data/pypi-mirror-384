"""Taylor series class module."""

import math
from typing import Callable


class TaylorSeries:
    """Class-based interface for Taylor series expansions."""

    def __init__(self, func: Callable[[float], float], n: int = 10) -> None:
        """
        Initialize a TaylorSeries calculator for a function.

        Args:
            func: The function to expand
            n: Number of terms in the series

        Examples:
            >>> import math
            >>> taylor = TaylorSeries(math.exp, n=10)
            >>> taylor.at(1.0, center=0)
            2.718...
        """
        self.func = func
        self.n = n

    def _derivative(self, func: Callable[[float], float], x: float, h: float = 1e-7) -> float:
        """
        Calculate numerical derivative.

        Args:
            func: Function to differentiate
            x: Point at which to calculate derivative
            h: Step size

        Returns:
            Derivative value
        """
        return (func(x + h) - func(x - h)) / (2 * h)

    def _nth_derivative(self, n: int, x: float) -> float:
        """
        Calculate the nth derivative of the function at point x using finite differences.

        Uses a multipoint stencil for better accuracy on higher derivatives.

        Args:
            n: Order of derivative
            x: Point at which to calculate

        Returns:
            The nth derivative value
        """
        if n == 0:
            return self.func(x)

        # Use optimal step size that balances truncation and roundoff error
        # h ≈ (ε_mach)^(1/(n+1)) where ε_mach ≈ 1e-16
        h = (1e-16) ** (1 / (n + 1))

        if n == 1:
            # Central difference for first derivative
            return float((self.func(x + h) - self.func(x - h)) / (2 * h))
        elif n == 2:
            # Central difference for second derivative
            return float((self.func(x + h) - 2 * self.func(x) + self.func(x - h)) / (h**2))
        elif n == 3:
            # Central difference for third derivative
            return float(
                (
                    self.func(x + 2 * h)
                    - 2 * self.func(x + h)
                    + 2 * self.func(x - h)
                    - self.func(x - 2 * h)
                )
                / (2 * h**3)
            )
        elif n == 4:
            # Central difference for fourth derivative
            return float(
                (
                    self.func(x + 2 * h)
                    - 4 * self.func(x + h)
                    + 6 * self.func(x)
                    - 4 * self.func(x - h)
                    + self.func(x - 2 * h)
                )
                / (h**4)
            )
        else:
            # For higher derivatives (n >= 5), use recursive approach with optimal h
            # This becomes increasingly unstable, so we use larger h
            h_large = h * (n / 2)

            def nth_minus_1(t: float) -> float:
                return self._nth_derivative(n - 1, t)

            return float((nth_minus_1(x + h_large) - nth_minus_1(x - h_large)) / (2 * h_large))

    def at(self, x: float, center: float = 0.0) -> float:
        """
        Evaluate the Taylor series at a point.

        Args:
            x: The point at which to evaluate
            center: The center point of expansion

        Returns:
            The Taylor series approximation
        """
        result = 0.0

        for i in range(self.n):
            # Calculate i-th derivative at center
            deriv = self._nth_derivative(i, center)

            # Add term to series
            term = (deriv * (x - center) ** i) / math.factorial(i)
            result += term

        return result

    def coefficients(self, center: float = 0.0) -> list[float]:
        """
        Calculate the Taylor series coefficients.

        Args:
            center: The center point of expansion

        Returns:
            List of coefficients
        """
        coeffs = []
        for i in range(self.n):
            deriv = self._nth_derivative(i, center)
            coeffs.append(deriv / math.factorial(i))
        return coeffs

    def polynomial_string(self, center: float = 0.0) -> str:
        """
        Generate a string representation of the Taylor polynomial.

        Args:
            center: The center point of expansion

        Returns:
            String representation of the polynomial
        """
        coeffs = self.coefficients(center)
        terms = []
        for i, coeff in enumerate(coeffs):
            if abs(coeff) < 1e-10:
                continue
            if i == 0:
                terms.append(f"{coeff:.4f}")
            elif i == 1:
                if center == 0:
                    terms.append(f"{coeff:.4f}*x")
                else:
                    terms.append(f"{coeff:.4f}*(x-{center})")
            else:
                if center == 0:
                    terms.append(f"{coeff:.4f}*x^{i}")
                else:
                    terms.append(f"{coeff:.4f}*(x-{center})^{i}")
        return " + ".join(terms)

    def error_estimate(self, x: float, center: float = 0.0) -> float:
        """
        Estimate the error (remainder) of the Taylor approximation.

        Args:
            x: The point to evaluate
            center: The center of expansion

        Returns:
            Estimated error
        """
        approx = self.at(x, center)
        actual = self.func(x)
        return abs(actual - approx)

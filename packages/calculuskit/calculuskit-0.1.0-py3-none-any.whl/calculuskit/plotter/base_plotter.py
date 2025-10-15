"""Base plotter class with common functionality."""

from typing import Any, Callable, Optional

import numpy as np


class BasePlotter:
    """Base class for all plotter types with common functionality."""

    def __init__(
        self,
        func: Callable[[float], float],
        x_range: tuple[float, float] = (-10, 10),
        n_points: int = 1000,
    ) -> None:
        """
        Initialize a BasePlotter with common settings.

        Args:
            func: The function to plot (must accept a float and return a float)
            x_range: Tuple of (min, max) values for x-axis
            n_points: Number of points to use for plotting
        """
        self.func = func
        self.x_range = x_range
        self.n_points = n_points
        self._x_values: Optional[np.ndarray[Any, Any]] = None
        self._y_values: Optional[np.ndarray[Any, Any]] = None

    def _compute_values(self) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        """
        Compute x and y values for the function.

        Returns:
            Tuple of (x_values, y_values) as numpy arrays
        """
        if self._x_values is None or self._y_values is None:
            self._x_values = np.linspace(self.x_range[0], self.x_range[1], self.n_points)
            # Vectorize the function to handle numpy arrays
            vectorized_func = np.vectorize(self.func)
            self._y_values = vectorized_func(self._x_values)

        # Type narrowing: after the if block, both are guaranteed to be non-None
        assert self._x_values is not None and self._y_values is not None
        return self._x_values, self._y_values

    def get_values(self) -> tuple[list[float], list[float]]:
        """
        Get the computed x and y values as lists.

        Returns:
            Tuple of (x_values, y_values) as lists

        Examples:
            >>> def f(x): return x**2
            >>> plotter = BasePlotter(f, x_range=(0, 5))
            >>> x, y = plotter.get_values()
        """
        x_vals, y_vals = self._compute_values()
        return x_vals.tolist(), y_vals.tolist()

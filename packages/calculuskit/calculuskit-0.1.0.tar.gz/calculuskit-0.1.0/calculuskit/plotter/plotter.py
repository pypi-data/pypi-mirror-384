"""Function Plotter class module.

This module provides a unified interface for all plotting functionality.
The FunctionPlotter class combines functionality from specialized plotter classes
for easy access to all plotting methods.
"""

from typing import Callable

from .animation_plotter import AnimationPlotter
from .plotter_2d import Plotter2D
from .plotter_3d import Plotter3D
from .vector_field_plotter import VectorFieldPlotter


class FunctionPlotter(Plotter2D, Plotter3D, VectorFieldPlotter, AnimationPlotter):
    """
    Class-based interface for plotting mathematical functions.

    This class provides a comprehensive interface for plotting various types
    of mathematical functions including:
    - 2D plots (line plots, parametric, polar, scatter)
    - 3D plots (surface plots, contour plots)
    - Vector fields (quiver plots)
    - Animations (series approximations, limit convergence)

    All methods are inherited from specialized plotter classes:
    - Plotter2D: Basic 2D plotting functionality
    - Plotter3D: 3D surface and contour plots
    - VectorFieldPlotter: Vector field visualizations
    - AnimationPlotter: Animated visualizations

    Examples:
        >>> import math
        >>> # Basic 2D plot
        >>> plotter = FunctionPlotter(math.sin, x_range=(-2*math.pi, 2*math.pi))
        >>> plotter.plot(title="Sine Function")

        >>> # 3D surface plot
        >>> def f(x, y): return x**2 + y**2
        >>> plotter = FunctionPlotter(lambda x: x)
        >>> plotter.surface_plot_3d(f, x_range=(-5, 5), y_range=(-5, 5))

        >>> # Vector field plot
        >>> def u(x, y): return -y
        >>> def v(x, y): return x
        >>> plotter = FunctionPlotter(lambda x: x)
        >>> plotter.quiver_plot(u, v, x_range=(-3, 3), y_range=(-3, 3))
    """

    def __init__(
        self,
        func: Callable[[float], float],
        x_range: tuple[float, float] = (-10, 10),
        n_points: int = 1000,
    ) -> None:
        """
        Initialize a FunctionPlotter for a mathematical function.

        Args:
            func: The function to plot (must accept a float and return a float)
            x_range: Tuple of (min, max) values for x-axis
            n_points: Number of points to use for plotting

        Examples:
            >>> def f(x): return x**2
            >>> plotter = FunctionPlotter(f, x_range=(-5, 5))
            >>> plotter.plot()
        """
        # Call parent class __init__
        # Using Plotter2D as it's the first in MRO after FunctionPlotter
        super().__init__(func, x_range, n_points)

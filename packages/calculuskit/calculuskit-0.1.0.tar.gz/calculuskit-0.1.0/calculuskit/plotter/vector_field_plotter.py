"""Vector field plotting functionality."""

from typing import Any, Callable, Optional

import matplotlib.pyplot as plt
import numpy as np

from .base_plotter import BasePlotter


class VectorFieldPlotter(BasePlotter):
    """Class for vector field plotting methods."""

    def quiver_plot(
        self,
        u_func: Callable[[float, float], float],
        v_func: Callable[[float, float], float],
        x_range: Optional[tuple[float, float]] = None,
        y_range: Optional[tuple[float, float]] = None,
        density: int = 20,
        title: str = "Vector Field",
        xlabel: str = "x",
        ylabel: str = "y",
        color: Optional[str] = None,
        scale: Optional[float] = None,
        width: float = 0.003,
        normalize: bool = False,
        show_magnitude: bool = False,
        colormap: str = "viridis",
        grid: bool = True,
        figsize: tuple[float, float] = (10, 8),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Create a quiver plot (vector field) for 2D vector functions.

        Args:
            u_func: Function for x-component of vector field u(x, y)
            v_func: Function for y-component of vector field v(x, y)
            x_range: Range for x-axis (min, max). Defaults to self.x_range
            y_range: Range for y-axis (min, max). Defaults to self.x_range
            density: Number of arrows in each direction
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            color: Single color for all arrows (overrides magnitude coloring)
            scale: Scale factor for arrow length (None for auto-scaling)
            width: Width of arrow shaft
            normalize: If True, normalize all vectors to unit length
            show_magnitude: If True, color arrows by magnitude
            colormap: Colormap for magnitude coloring
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> # Gradient field of f(x,y) = x^2 + y^2
            >>> def u(x, y): return 2*x
            >>> def v(x, y): return 2*y
            >>> plotter = VectorFieldPlotter(lambda x: x)
            >>> plotter.quiver_plot(u, v, x_range=(-5, 5), y_range=(-5, 5))

            >>> # Circular rotation field
            >>> def u(x, y): return -y
            >>> def v(x, y): return x
            >>> plotter = VectorFieldPlotter(lambda x: x)
            >>> plotter.quiver_plot(u, v, normalize=True, show_magnitude=True)
        """
        # Use default ranges if not provided
        if x_range is None:
            x_range = self.x_range
        if y_range is None:
            y_range = self.x_range

        # Create grid
        x = np.linspace(x_range[0], x_range[1], density)
        y = np.linspace(y_range[0], y_range[1], density)
        X, Y = np.meshgrid(x, y)

        # Compute vector components
        vectorized_u = np.vectorize(u_func)
        vectorized_v = np.vectorize(v_func)
        U = vectorized_u(X, Y)
        V = vectorized_v(X, Y)

        # Calculate magnitude for coloring
        M = np.sqrt(U**2 + V**2)

        # Normalize vectors if requested
        if normalize:
            # Avoid division by zero
            M_safe = np.where(M > 0, M, 1)
            U = U / M_safe
            V = V / M_safe

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create quiver plot
        if show_magnitude and color is None:
            # Color by magnitude
            quiver = ax.quiver(X, Y, U, V, M, cmap=colormap, scale=scale, width=width, alpha=0.8)
            cbar = plt.colorbar(quiver, ax=ax)
            cbar.set_label("Magnitude", fontsize=12)
        else:
            # Single color
            plot_color = color if color is not None else "blue"
            quiver = ax.quiver(X, Y, U, V, color=plot_color, scale=scale, width=width, alpha=0.8)

        # Set labels and title
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_aspect("equal")

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        # Add axis lines
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

"""3D plotting functionality."""

from typing import Any, Callable, Optional

import matplotlib.pyplot as plt
import numpy as np

from .base_plotter import BasePlotter


class Plotter3D(BasePlotter):
    """Class for 3D plotting methods."""

    def contour_plot(
        self,
        func: Callable[[float, float], float],
        x_range: Optional[tuple[float, float]] = None,
        y_range: Optional[tuple[float, float]] = None,
        n_points: Optional[int] = None,
        title: str = "Contour Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        levels: int = 20,
        colormap: str = "viridis",
        show_colorbar: bool = True,
        filled: bool = True,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 8),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Create a contour plot for a multivariable function z = f(x, y).

        Args:
            func: Function that takes two arguments (x, y) and returns z
            x_range: Range for x-axis (min, max). Defaults to self.x_range
            y_range: Range for y-axis (min, max). Defaults to self.x_range
            n_points: Number of points in each direction. Defaults to self.n_points
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            levels: Number of contour levels or list of specific levels
            colormap: Colormap to use ('viridis', 'plasma', 'coolwarm', etc.)
            show_colorbar: Whether to show the colorbar
            filled: If True, create filled contours; if False, create line contours
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> def f(x, y): return x**2 + y**2
            >>> plotter = Plotter3D(lambda x: x)
            >>> plotter.contour_plot(f, x_range=(-5, 5), y_range=(-5, 5))

            >>> import math
            >>> def saddle(x, y): return x**2 - y**2
            >>> plotter = Plotter3D(lambda x: x)
            >>> plotter.contour_plot(saddle, levels=30, colormap='coolwarm')
        """
        # Use default ranges if not provided
        if x_range is None:
            x_range = self.x_range
        if y_range is None:
            y_range = self.x_range
        if n_points is None:
            n_points = self.n_points

        # Create grid
        x = np.linspace(x_range[0], x_range[1], n_points)
        y = np.linspace(y_range[0], y_range[1], n_points)
        X, Y = np.meshgrid(x, y)

        # Compute Z values
        vectorized_func = np.vectorize(func)
        Z = vectorized_func(X, Y)

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create contour plot
        if filled:
            contour = ax.contourf(X, Y, Z, levels=levels, cmap=colormap)
        else:
            contour = ax.contour(X, Y, Z, levels=levels, cmap=colormap)
            ax.clabel(contour, inline=True, fontsize=8)

        # Add colorbar
        if show_colorbar:
            cbar = plt.colorbar(contour, ax=ax)
            cbar.set_label("z", fontsize=12)

        # Set labels and title
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def surface_plot_3d(
        self,
        func: Callable[[float, float], float],
        x_range: Optional[tuple[float, float]] = None,
        y_range: Optional[tuple[float, float]] = None,
        n_points: Optional[int] = None,
        title: str = "3D Surface Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        zlabel: str = "z",
        colormap: str = "viridis",
        alpha: float = 0.9,
        show_contour: bool = False,
        figsize: tuple[float, float] = (12, 9),
        elevation: float = 30,
        azimuth: float = 45,
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Create a 3D surface plot for a multivariable function z = f(x, y).

        Args:
            func: Function that takes two arguments (x, y) and returns z
            x_range: Range for x-axis (min, max). Defaults to self.x_range
            y_range: Range for y-axis (min, max). Defaults to self.x_range
            n_points: Number of points in each direction. Defaults to self.n_points
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            zlabel: Label for z-axis
            colormap: Colormap to use ('viridis', 'plasma', 'coolwarm', etc.)
            alpha: Transparency of the surface (0-1)
            show_contour: Whether to show contour lines projected on the bottom
            figsize: Figure size as (width, height) in inches
            elevation: Viewing elevation angle in degrees
            azimuth: Viewing azimuth angle in degrees
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> def f(x, y): return np.sin(np.sqrt(x**2 + y**2))
            >>> plotter = Plotter3D(lambda x: x)
            >>> plotter.surface_plot_3d(f, x_range=(-5, 5), y_range=(-5, 5))

            >>> def paraboloid(x, y): return x**2 + y**2
            >>> plotter = Plotter3D(lambda x: x)
            >>> plotter.surface_plot_3d(paraboloid, show_contour=True)
        """
        # Use default ranges if not provided
        if x_range is None:
            x_range = self.x_range
        if y_range is None:
            y_range = self.x_range
        if n_points is None:
            n_points = self.n_points

        # Create grid
        x = np.linspace(x_range[0], x_range[1], n_points)
        y = np.linspace(y_range[0], y_range[1], n_points)
        X, Y = np.meshgrid(x, y)

        # Compute Z values
        vectorized_func = np.vectorize(func)
        Z = vectorized_func(X, Y)

        # Create 3D figure
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection="3d")

        # Create surface plot
        surf = ax.plot_surface(X, Y, Z, cmap=colormap, alpha=alpha, linewidth=0, antialiased=True)

        # Add contour lines at the bottom if requested
        if show_contour:
            z_min: float = float(np.min(Z))
            ax.contour(X, Y, Z, levels=15, cmap=colormap, offset=z_min, alpha=0.5)

        # Set labels and title
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_zlabel(zlabel, fontsize=12)

        # Set viewing angle
        ax.view_init(elev=elevation, azim=azimuth)

        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

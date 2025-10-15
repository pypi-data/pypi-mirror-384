"""2D plotting functionality."""

from typing import Any, Callable, Optional

import matplotlib.pyplot as plt
import numpy as np

from .base_plotter import BasePlotter


class Plotter2D(BasePlotter):
    """Class for 2D plotting methods."""

    def plot(
        self,
        title: str = "Function Plot",
        xlabel: str = "x",
        ylabel: str = "f(x)",
        color: str = "blue",
        linestyle: str = "-",
        linewidth: float = 2.0,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Plot the function.

        Args:
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            color: Color of the plot line
            linestyle: Style of the line ('-', '--', '-.', ':')
            linewidth: Width of the plot line
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> import math
            >>> plotter = Plotter2D(math.sin, x_range=(-2*math.pi, 2*math.pi))
            >>> plotter.plot(title="Sine Function", color="red")
        """
        x_vals, y_vals = self._compute_values()

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x_vals, y_vals, color=color, linestyle=linestyle, linewidth=linewidth)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        # Add axis lines at y=0 and x=0
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_with_derivative(
        self,
        derivative_func: Callable[[float], float],
        title: str = "Function and Derivative",
        func_label: str = "f(x)",
        deriv_label: str = "f'(x)",
        func_color: str = "blue",
        deriv_color: str = "red",
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Plot the function along with its derivative.

        Args:
            derivative_func: The derivative function to plot
            title: Title of the plot
            func_label: Label for the original function
            deriv_label: Label for the derivative
            func_color: Color for the function plot
            deriv_color: Color for the derivative plot
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> def f(x): return x**2
            >>> def df(x): return 2*x
            >>> plotter = Plotter2D(f, x_range=(-3, 3))
            >>> plotter.plot_with_derivative(df)
        """
        x_vals, y_vals = self._compute_values()

        # Compute derivative values
        vectorized_deriv = np.vectorize(derivative_func)
        deriv_vals = vectorized_deriv(x_vals)

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x_vals, y_vals, color=func_color, linewidth=2, label=func_label)
        ax.plot(x_vals, deriv_vals, color=deriv_color, linewidth=2, label=deriv_label)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("x", fontsize=12)
        ax.set_ylabel("y", fontsize=12)
        ax.legend(fontsize=10)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_multiple(
        self,
        functions: list[tuple[Callable[[float], float], str]],
        title: str = "Multiple Functions",
        xlabel: str = "x",
        ylabel: str = "y",
        colors: Optional[list[str]] = None,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Plot multiple functions on the same axes.

        Args:
            functions: List of tuples (function, label)
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            colors: Optional list of colors for each function
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> import math
            >>> funcs = [(math.sin, "sin(x)"), (math.cos, "cos(x)")]
            >>> plotter = Plotter2D(math.sin)  # dummy function
            >>> plotter.plot_multiple(funcs, title="Trigonometric Functions")
        """
        if colors is None:
            colors = ["blue", "red", "green", "orange", "purple", "brown", "pink"]

        x_vals = np.linspace(self.x_range[0], self.x_range[1], self.n_points)

        fig, ax = plt.subplots(figsize=figsize)

        for idx, (func, label) in enumerate(functions):
            color = colors[idx % len(colors)]
            vectorized_func = np.vectorize(func)
            y_vals = vectorized_func(x_vals)
            ax.plot(x_vals, y_vals, color=color, linewidth=2, label=label)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(fontsize=10)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_parametric(
        self,
        x_func: Callable[[float], float],
        y_func: Callable[[float], float],
        t_range: tuple[float, float] = (0, 2 * np.pi),
        title: str = "Parametric Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        color: str = "blue",
        linewidth: float = 2.0,
        grid: bool = True,
        figsize: tuple[float, float] = (8, 8),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Plot a parametric curve defined by x(t) and y(t).

        Args:
            x_func: Function for x coordinate
            y_func: Function for y coordinate
            t_range: Range for parameter t
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            color: Color of the plot line
            linewidth: Width of the plot line
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> import math
            >>> x = lambda t: math.cos(t)
            >>> y = lambda t: math.sin(t)
            >>> plotter = Plotter2D(lambda x: x)
            >>> plotter.plot_parametric(x, y, title="Unit Circle")
        """
        t_vals = np.linspace(t_range[0], t_range[1], self.n_points)

        vectorized_x = np.vectorize(x_func)
        vectorized_y = np.vectorize(y_func)

        x_vals = vectorized_x(t_vals)
        y_vals = vectorized_y(t_vals)

        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x_vals, y_vals, color=color, linewidth=linewidth)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_aspect("equal")

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def plot_polar(
        self,
        r_func: Callable[[float], float],
        theta_range: tuple[float, float] = (0, 2 * np.pi),
        title: str = "Polar Plot",
        color: str = "blue",
        linewidth: float = 2.0,
        grid: bool = True,
        figsize: tuple[float, float] = (8, 8),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Plot a function in polar coordinates r(theta).

        Args:
            r_func: Function for radius as a function of angle
            theta_range: Range for angle theta in radians
            title: Title of the plot
            color: Color of the plot line
            linewidth: Width of the plot line
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> import math
            >>> r = lambda theta: 1 + math.cos(theta)
            >>> plotter = Plotter2D(lambda x: x)
            >>> plotter.plot_polar(r, title="Cardioid")
        """
        theta_vals = np.linspace(theta_range[0], theta_range[1], self.n_points)

        vectorized_r = np.vectorize(r_func)
        r_vals = vectorized_r(theta_vals)

        fig, ax = plt.subplots(figsize=figsize, subplot_kw={"projection": "polar"})
        ax.plot(theta_vals, r_vals, color=color, linewidth=linewidth)

        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        if show:
            plt.show()

        return fig

    def scatter_plot(
        self,
        x_data: list[float],
        y_data: list[float],
        title: str = "Scatter Plot",
        xlabel: str = "x",
        ylabel: str = "y",
        color: str = "blue",
        marker: str = "o",
        size: float = 50,
        alpha: float = 0.7,
        show_fit: bool = False,
        fit_degree: int = 1,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> Any:
        """
        Create a scatter plot of data points.

        Args:
            x_data: List of x coordinates
            y_data: List of y coordinates
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            color: Color of the scatter points
            marker: Marker style ('o', 's', '^', etc.)
            size: Size of the markers
            alpha: Transparency of markers (0-1)
            show_fit: Whether to show polynomial fit line
            fit_degree: Degree of polynomial for fitting
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            show: Whether to display the plot immediately
            save_path: Optional path to save the plot image

        Returns:
            Matplotlib figure object

        Examples:
            >>> x = [1, 2, 3, 4, 5]
            >>> y = [2, 4, 5, 4, 5]
            >>> plotter = Plotter2D(lambda x: x)
            >>> plotter.scatter_plot(x, y, show_fit=True)
        """
        fig, ax = plt.subplots(figsize=figsize)

        ax.scatter(x_data, y_data, color=color, marker=marker, s=size, alpha=alpha, label="Data")

        if show_fit and len(x_data) > fit_degree:
            coeffs = np.polyfit(x_data, y_data, fit_degree)
            poly = np.poly1d(coeffs)
            x_fit = np.linspace(min(x_data), max(x_data), 100)
            y_fit = poly(x_fit)
            ax.plot(x_fit, y_fit, color="red", linewidth=2, label=f"Fit (degree {fit_degree})")
            ax.legend()

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

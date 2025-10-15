"""Animation plotting functionality."""

from typing import Any, Callable, Optional

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from .base_plotter import BasePlotter


class AnimationPlotter(BasePlotter):
    """Class for animation plotting methods."""

    def animate_series_approximation(
        self,
        func: Callable[[float], float],
        approximation_func: Callable[[float, int], float],
        x_range: Optional[tuple[float, float]] = None,
        n_points: Optional[int] = None,
        max_terms: int = 20,
        title_func: Optional[Callable[[int], str]] = None,
        xlabel: str = "x",
        ylabel: str = "y",
        func_label: str = "Original Function",
        approx_label: str = "Approximation",
        func_color: str = "blue",
        approx_color: str = "red",
        interval: int = 500,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        save_path: Optional[str] = None,
    ) -> animation.FuncAnimation:
        """
        Create an animation showing series approximation convergence.

        This method animates how a series approximation (Taylor, Fourier, etc.)
        converges to the original function as the number of terms increases.

        Args:
            func: The original function to approximate
            approximation_func: Function that takes (x, n_terms) and returns approximation
            x_range: Range for x-axis (min, max). Defaults to self.x_range
            n_points: Number of points to plot. Defaults to self.n_points
            max_terms: Maximum number of terms to animate
            title_func: Function to generate title based on term count
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            func_label: Label for original function
            approx_label: Label for approximation
            func_color: Color for original function
            approx_color: Color for approximation
            interval: Delay between frames in milliseconds
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            save_path: Optional path to save animation (as .gif or .mp4)

        Returns:
            Matplotlib FuncAnimation object

        Examples:
            >>> import math
            >>> # Animate Taylor series convergence
            >>> def f(x): return math.exp(x)
            >>> def taylor_approx(x, n):
            ...     return sum(x**k / math.factorial(k) for k in range(n+1))
            >>> plotter = AnimationPlotter(f, x_range=(-2, 2))
            >>> anim = plotter.animate_series_approximation(
            ...     f, taylor_approx, max_terms=10,
            ...     title_func=lambda n: f"Taylor Series: {n} terms"
            ... )

            >>> # Animate Fourier series convergence
            >>> def square_wave(x): return 1 if x % (2*math.pi) < math.pi else -1
            >>> def fourier_approx(x, n):
            ...     # Simplified square wave Fourier approximation
            ...     return sum((4/math.pi) * math.sin((2*k-1)*x)/(2*k-1)
            ...                for k in range(1, n+1))
            >>> plotter = AnimationPlotter(square_wave, x_range=(0, 2*math.pi))
            >>> anim = plotter.animate_series_approximation(square_wave, fourier_approx)
        """
        # Use default ranges if not provided
        if x_range is None:
            x_range = self.x_range
        if n_points is None:
            n_points = self.n_points

        # Generate x values
        x_vals = np.linspace(x_range[0], x_range[1], n_points)

        # Compute original function values
        vectorized_func = np.vectorize(func)
        y_vals = vectorized_func(x_vals)

        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)

        # Plot original function
        (line_func,) = ax.plot(
            x_vals, y_vals, color=func_color, linewidth=2, label=func_label, alpha=0.7
        )

        # Initialize approximation line
        (line_approx,) = ax.plot([], [], color=approx_color, linewidth=2, label=approx_label)

        # Setup axes
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.legend(fontsize=10)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.axvline(x=0, color="black", linewidth=0.5)

        # Set axis limits
        y_min: float = float(np.min(y_vals))
        y_max: float = float(np.max(y_vals))
        y_margin = (y_max - y_min) * 0.1
        ax.set_xlim(x_range[0], x_range[1])
        ax.set_ylim(y_min - y_margin, y_max + y_margin)

        plt.tight_layout()

        # Animation update function
        def update(n: int) -> tuple[Any, ...]:
            # Compute approximation for current number of terms
            approx_vals = np.array([approximation_func(x, n + 1) for x in x_vals])

            # Update approximation line
            line_approx.set_data(x_vals, approx_vals)

            # Update title
            if title_func is not None:
                ax.set_title(title_func(n + 1), fontsize=14, fontweight="bold")
            else:
                ax.set_title(f"{approx_label}: {n + 1} terms", fontsize=14, fontweight="bold")

            return (line_approx,)

        # Create animation
        anim = animation.FuncAnimation(
            fig, update, frames=max_terms, interval=interval, blit=True, repeat=True
        )

        # Save animation if path provided
        if save_path:
            if save_path.endswith(".gif"):
                anim.save(save_path, writer="pillow", fps=1000 / interval)
            elif save_path.endswith(".mp4"):
                anim.save(save_path, writer="ffmpeg", fps=1000 / interval)
            else:
                print("Warning: Unsupported format. Use .gif or .mp4")

        plt.show()

        return anim

    def animate_limit_convergence(
        self,
        sequence_func: Callable[[int], float],
        limit_value: Optional[float] = None,
        max_n: int = 50,
        title: str = "Sequence Convergence",
        xlabel: str = "n",
        ylabel: str = "a_n",
        sequence_color: str = "blue",
        limit_color: str = "red",
        marker: str = "o",
        interval: int = 200,
        grid: bool = True,
        figsize: tuple[float, float] = (10, 6),
        save_path: Optional[str] = None,
    ) -> animation.FuncAnimation:
        """
        Create an animation showing sequence convergence to a limit.

        Args:
            sequence_func: Function that takes integer n and returns sequence value
            limit_value: The limit value to show (None to omit)
            max_n: Maximum value of n to animate
            title: Title of the plot
            xlabel: Label for x-axis
            ylabel: Label for y-axis
            sequence_color: Color for sequence points
            limit_color: Color for limit line
            marker: Marker style for sequence points
            interval: Delay between frames in milliseconds
            grid: Whether to show grid lines
            figsize: Figure size as (width, height) in inches
            save_path: Optional path to save animation

        Returns:
            Matplotlib FuncAnimation object

        Examples:
            >>> # Animate convergence of 1/n to 0
            >>> def seq(n): return 1/n
            >>> plotter = AnimationPlotter(lambda x: x)
            >>> anim = plotter.animate_limit_convergence(
            ...     seq, limit_value=0, max_n=50,
            ...     title="Convergence of 1/n to 0"
            ... )

            >>> # Animate convergence to e
            >>> def seq(n): return (1 + 1/n)**n
            >>> import math
            >>> plotter = AnimationPlotter(lambda x: x)
            >>> anim = plotter.animate_limit_convergence(
            ...     seq, limit_value=math.e, max_n=100,
            ...     title="Convergence to e"
            ... )
        """
        # Create figure and axis
        fig, ax = plt.subplots(figsize=figsize)

        # Compute all sequence values
        n_vals = np.arange(1, max_n + 1)
        seq_vals = np.array([sequence_func(n) for n in n_vals])

        # Initialize scatter plot
        (scatter,) = ax.plot(
            [], [], color=sequence_color, marker=marker, linestyle="-", linewidth=1
        )

        # Plot limit line if provided
        if limit_value is not None:
            ax.axhline(
                y=limit_value,
                color=limit_color,
                linestyle="--",
                linewidth=2,
                label=f"Limit = {limit_value:.4f}",
                alpha=0.7,
            )
            ax.legend(fontsize=10)

        # Setup axes
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        # Set axis limits
        y_min: float = float(np.min(seq_vals))
        y_max: float = float(np.max(seq_vals))
        y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
        ax.set_xlim(0, max_n + 1)
        ax.set_ylim(y_min - y_margin, y_max + y_margin)

        plt.tight_layout()

        # Animation update function
        def update(frame: int) -> tuple[Any, ...]:
            # Show sequence up to current frame
            scatter.set_data(n_vals[: frame + 1], seq_vals[: frame + 1])
            return (scatter,)

        # Create animation
        anim = animation.FuncAnimation(
            fig, update, frames=max_n, interval=interval, blit=True, repeat=True
        )

        # Save animation if path provided
        if save_path:
            if save_path.endswith(".gif"):
                anim.save(save_path, writer="pillow", fps=1000 / interval)
            elif save_path.endswith(".mp4"):
                anim.save(save_path, writer="ffmpeg", fps=1000 / interval)
            else:
                print("Warning: Unsupported format. Use .gif or .mp4")

        plt.show()

        return anim

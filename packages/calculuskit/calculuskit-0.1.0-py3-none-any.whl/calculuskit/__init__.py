"""CalculusKit - A Python library for mathematical calculus operations.

Package Structure:
    - derivative: Derivative calculations
    - partial_derivative: Partial derivative calculations
    - integral: Integration operations
    - double_integral: Double integral calculations
    - limit: Limit calculations
    - taylor_series: Taylor series expansions
    - maclaurin_series: Maclaurin series expansions
    - fourier_series: Fourier series expansions
    - plotter: Function plotting and visualization
"""

__version__ = "0.1.0"

# Core calculus operations - Class-based API
from calculuskit.derivative.derivative import Derivative
from calculuskit.double_integral.double_integral import DoubleIntegral
from calculuskit.fourier_series.fourier_series import FourierSeries
from calculuskit.integral.integral import Integral
from calculuskit.limit.limit import Limit
from calculuskit.maclaurin_series.maclaurin_series import MaclaurinSeries
from calculuskit.partial_derivative.partial_derivative import PartialDerivative
from calculuskit.plotter.plotter import FunctionPlotter
from calculuskit.taylor_series.taylor_series import TaylorSeries

__all__ = [
    # Core - Classes
    "Derivative",
    "PartialDerivative",
    "Integral",
    "DoubleIntegral",
    "Limit",
    "TaylorSeries",
    "MaclaurinSeries",
    "FourierSeries",
    "FunctionPlotter",
]

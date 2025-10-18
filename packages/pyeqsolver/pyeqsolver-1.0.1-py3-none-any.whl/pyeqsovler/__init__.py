"""
Equations Solvers - A Python package for matrix operations and solving linear equations
"""

from .matrices.matrices2x2 import Matrices2x2
from .matrices.matrices3x3 import Matrices3x3
from .linear_equations_solver import LinearEquationsSolver
from .matrixerror import InvalidMatrixError

__version__ = "0.1.0"
__author__ = "Hammail Riaz"
__all__ = [
    "Matrices2x2",
    "Matrices3x3", 
    "LinearEquationsSolver",
    "InvalidMatrixError"
]
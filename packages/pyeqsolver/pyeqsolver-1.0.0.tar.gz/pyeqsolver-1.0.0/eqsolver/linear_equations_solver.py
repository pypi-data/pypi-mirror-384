"""
Linear Equations Solver Module

This module provides a robust solver for 2x2 and 3x3 systems of linear equations
using Cramer's rule and matrix inversion methods.

Example:
    >>> solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
    >>> solution = solver.solve()
    >>> print(solution)
    [('x', '11/18'), ('y', '17/18')]
"""

import copy
import re
from typing import List, Tuple, Union, Optional
from .matrices.matrices3x3 import Matrices3x3, InvalidMatrixError
from .matrices.matrices2x2 import Matrices2x2
from fractions import Fraction
from .determinant import Determinant

# Type aliases
Matrix = List[List[Union[int, float]]]
Solution = List[Tuple[str, str]]
EquationData = Tuple[List[str], List[Union[int, float]], Union[int, float]]


class LinearEquationsSolverError(Exception):
    """Base exception for LinearEquationsSolver errors."""
    pass


class ParseError(LinearEquationsSolverError):
    """Raised when equation parsing fails."""
    pass


class ValidationError(LinearEquationsSolverError):
    """Raised when equation validation fails."""
    pass


class LinearEquationsSolver(Matrices3x3, Matrices2x2):
    """
    Solver for systems of 2 or 3 linear equations.
    
    Supports two solution methods:
    - Cramer's Rule: Uses determinants
    - Matrix Inversion: Uses A^(-1) * B
    
    Equation Format:
        - 2x2: "2x + 4y = 5, 3x - 3y = -1"
        - 3x3: "3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0"
        
    Variables must be consistent across all equations.
    Coefficients can be integers or floats (including negative).
    """
    
    SUPPORTED_SYSTEMS = {2, 3}
    
    def __init__(self, equations: str, validate: bool = True) -> None:
        """
        Initialize solver with equations string.
        
        Args:
            equations: Comma-separated string of equations
            validate: If True, perform validation checks (default: True)
            
        Raises:
            ParseError: If equations cannot be parsed
            ValidationError: If equations are invalid
            ValueError: If system size is not 2x2 or 3x3
        """
        if not equations or not equations.strip():
            raise ParseError("Equations string cannot be empty.")
        
        self.equs = equations.strip()
        self.equs_data = self._parse_equations(self.equs)
        
        # Determine system size
        num_equations = len(self.equs_data)
        self.m2x2 = (num_equations == 2)
        self.m3x3 = (num_equations == 3)
        
        if num_equations not in self.SUPPORTED_SYSTEMS:
            raise ValueError(
                f"Only 2x2 and 3x3 systems are supported. "
                f"Got {num_equations} equation(s)."
            )
        
        if validate:
            self._validate_system()
    
    def _parse_equations(self, equations: str) -> List[EquationData]:
        """
        Parse multiple equations from a comma-separated string.
        
        Args:
            equations: String containing comma-separated equations
            
        Returns:
            List of tuples (variables, coefficients, rhs)
            
        Raises:
            ParseError: If any equation cannot be parsed
        """
        parsed = []
        eq_list = [eq.strip() for eq in equations.split(',') if eq.strip()]
        
        if not eq_list:
            raise ParseError("No valid equations found.")
        
        for i, eq in enumerate(eq_list, 1):
            try:
                parsed.append(self._parse_equ(eq))
            except Exception as e:
                raise ParseError(f"Error parsing equation {i} ('{eq}'): {str(e)}")
        
        return parsed

    def _parse_equ(self, equ: str) -> EquationData:
        """
        Parse a single equation into components.
        
        Args:
            equ: Single equation string (e.g., "2x + 4y = 5")
            
        Returns:
            Tuple of (variables, coefficients, rhs_value)
            
        Raises:
            ParseError: If equation format is invalid
        """
        # Remove all whitespace
        equ = equ.replace(" ", "")
        
        if "=" not in equ:
            raise ParseError(f"Equation must contain '=': {equ}")
        
        parts = equ.split("=")
        if len(parts) != 2:
            raise ParseError(f"Equation must have exactly one '=': {equ}")
        
        lhs, rhs = parts
        
        if not lhs or not rhs:
            raise ParseError(f"Both sides of equation must be non-empty: {equ}")
        
        # Parse RHS
        try:
            rhs_value = float(rhs)
        except ValueError:
            raise ParseError(f"Right-hand side must be a number: '{rhs}'")
        
        # Extract variables (alphabetic characters)
        variables = []
        for char in lhs:
            if char.isalpha() and char not in variables:
                variables.append(char)
        
        if not variables:
            raise ParseError(f"No variables found in equation: {equ}")
        
        # Parse terms using regex to handle negative leading terms
        # Pattern matches: optional sign, optional number, required variable
        pattern = r'([+-]?)(\d*\.?\d*)([a-zA-Z])'
        matches = re.findall(pattern, lhs)
        
        if not matches:
            raise ParseError(f"Could not parse terms in: {lhs}")
        
        # Build coefficient mapping
        coef_map = {}
        for sign, num, var in matches:
            # Determine coefficient value
            if num == '':
                coef = 1.0
            else:
                coef = float(num)
            
            # Apply sign
            if sign == '-':
                coef = -coef
            elif sign == '' and var == matches[0][2] and matches[0][1] == '':
                # First term with no explicit sign and no number
                coef = 1.0
            
            coef_map[var] = coef
        
        # Build coefficient list in order of variables
        coefficients = []
        for var in variables:
            coefficients.append(coef_map.get(var, 0.0))
        
        return variables, coefficients, rhs_value
    
    def _validate_system(self) -> None:
        """
        Validate that the system of equations is well-formed.
        
        Raises:
            ValidationError: If system is invalid
        """
        if not self.equs_data:
            raise ValidationError("No equations to validate.")
        
        # Check variable consistency
        expected_vars = self.equs_data[0][0]
        expected_count = len(expected_vars)
        
        for i, (vars_list, coeffs, _) in enumerate(self.equs_data, 1):
            if vars_list != expected_vars:
                raise ValidationError(
                    f"Equation {i} has inconsistent variables. "
                    f"Expected {expected_vars}, got {vars_list}"
                )
            
            if len(coeffs) != expected_count:
                raise ValidationError(
                    f"Equation {i} has wrong number of coefficients. "
                    f"Expected {expected_count}, got {len(coeffs)}"
                )
        
        # Check that number of equations matches number of variables
        if len(self.equs_data) != expected_count:
            raise ValidationError(
                f"Number of equations ({len(self.equs_data)}) must equal "
                f"number of variables ({expected_count})"
            )
    
    def A(self) -> Matrix:
        """
        Get coefficient matrix A.
        
        Returns:
            2D list representing the coefficient matrix
        """
        return [[coef for coef in data[1]] for data in self.equs_data]

    def _get_RHS_matrix(self) -> List[float]:
        """
        Get right-hand side values as a list.
        
        Returns:
            List of RHS values
        """
        return [data[2] for data in self.equs_data]

    def replaced_matrix(self, matrix: Matrix, variable: str) -> Matrix:
        """
        Replace a column in matrix with RHS values (for Cramer's rule).
        
        Args:
            matrix: Original coefficient matrix
            variable: Variable whose column to replace
            
        Returns:
            New matrix with replaced column
            
        Raises:
            ValueError: If variable is invalid
        """
        rhs = self._get_RHS_matrix()
        result = copy.deepcopy(matrix)
        
        variables = self.equs_data[0][0]
        if variable not in variables:
            raise ValueError(
                f"Invalid variable '{variable}'. "
                f"Available variables: {', '.join(variables)}"
            )
        
        var_index = variables.index(variable)
        
        for i in range(len(result)):
            result[i][var_index] = rhs[i]
        
        return result

    def crammers_rule(self) -> Solution:
        """
        Solve system using Cramer's rule.
        
        Returns:
            List of (variable, value) tuples
            
        Raises:
            InvalidMatrixError: If system has no unique solution
        """
        variables = self.equs_data[0][0]
        A = self.A()
        detA = Determinant(A).det()
        
        if abs(detA) < 1e-10:
            raise InvalidMatrixError(
                "System has no unique solution (determinant is zero or near-zero)."
            )
        
        solution = []
        
        for var in variables:
            A_replaced = self.replaced_matrix(A, var)
            det_replaced = Determinant(A_replaced).det()
            
            # Compute as fraction for exact representation
            value = Fraction(det_replaced / detA).limit_denominator()
            solution.append((var, str(value)))
        
        return solution

    def matrix_inversion_rule(self) -> Solution:
        """
        Solve system using matrix inversion: X = A^(-1) * B.
        
        Returns:
            List of (variable, value) tuples
            
        Raises:
            InvalidMatrixError: If matrix is not invertible
        """
        A = self.A()
        
        detA = Determinant(A).det()
        if abs(detA) < 1e-10:
            raise InvalidMatrixError(
                "System has no unique solution (determinant is zero or near-zero). "
                "Matrix is not invertible."
            )
        
        B = [[val] for val in self._get_RHS_matrix()]
        
        # Use appropriate class methods to avoid MRO conflicts
        if self.m3x3:
            temp = Matrices3x3()
            inverse = temp.multiplicative_inverse(A)
            result = temp.matrix_multiply(inverse, B)
        elif self.m2x2:
            temp = Matrices2x2()
            inverse = temp.multiplicative_inverse(A)
            # Check which method name exists
            if hasattr(temp, 'matrix_multiply'):
                result = temp.matrix_multiply(inverse, B)
            else:
                result = temp.multiply(inverse, B)
        else:
            raise InvalidMatrixError("Invalid system size.")
        
        result = [[round(val, 10) for val in row] for row in result]
        
        variables = self.equs_data[0][0]
        solution = []
        for i, var in enumerate(variables):
            frac_value = Fraction(result[i][0]).limit_denominator()
            solution.append((var, str(frac_value)))
        
        return solution
    
    def solve(self, method: str = 'cramer') -> Solution:
        """
        Solve the linear system.
        
        Args:
            method: Solution method - 'cramer' or 'inverse' (default: 'cramer')
            
        Returns:
            List of (variable, value) tuples representing the solution
            
        Raises:
            ValueError: If method is unknown
            InvalidMatrixError: If system has no unique solution
            
        Example:
            >>> solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
            >>> solver.solve()
            [('x', '11/18'), ('y', '17/18')]
        """
        method = method.lower().strip()
        
        if method == 'cramer':
            return self.crammers_rule()
        elif method == 'inverse' or method == 'inversion':
            return self.matrix_inversion_rule()
        else:
            raise ValueError(
                f"Unknown method '{method}'. "
                f"Supported methods: 'cramer', 'inverse'"
            )
    
    def get_variables(self) -> List[str]:
        """Get list of variables in the system."""
        return self.equs_data[0][0] if self.equs_data else []
    
    def __str__(self) -> str:
        """String representation of the system."""
        size = "2x2" if self.m2x2 else "3x3"
        return f"LinearEquationsSolver({size} system with variables {self.get_variables()})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"LinearEquationsSolver('{self.equs}')"


def main():
    """Example usage and testing."""
    print("=" * 60)
    print("LINEAR EQUATIONS SOLVER - PRODUCTION VERSION")
    print("=" * 60)
    
    # Test 2x2 system
    print("\n### 2x2 System ###")
    print("Equations: 2x + 4y = 5, 3x - 3y = -1")
    try:
        solver_2x2 = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
        print(f"System: {solver_2x2}")
        print(f"\nCoefficient matrix A:")
        for row in solver_2x2.A():
            print(f"  {row}")
        
        print(f"\nSolution (Cramer's rule):")
        for var, val in solver_2x2.solve('cramer'):
            print(f"  {var} = {val}")
        
        print(f"\nSolution (Matrix inversion):")
        for var, val in solver_2x2.solve('inverse'):
            print(f"  {var} = {val}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    # Test 3x3 system
    print("\n" + "=" * 60)
    print("### 3x3 System ###")
    print("Equations: 3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0")
    try:
        solver_3x3 = LinearEquationsSolver(
            "3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0"
        )
        print(f"System: {solver_3x3}")
        print(f"\nCoefficient matrix A:")
        for row in solver_3x3.A():
            print(f"  {row}")
        
        print(f"\nSolution (Cramer's rule):")
        for var, val in solver_3x3.solve('cramer'):
            print(f"  {var} = {val}")
        
        print(f"\nSolution (Matrix inversion):")
        for var, val in solver_3x3.solve('inverse'):
            print(f"  {var} = {val}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    # Test error handling
    print("\n" + "=" * 60)
    print("### Error Handling Tests ###")
    
    test_cases = [
        ("", "Empty string"),
        ("2x + 3y", "Missing equals sign"),
        ("x = 5", "Only one equation for 2x2"),
        ("x + y = 1, x + z = 2", "Inconsistent variables"),
    ]
    
    for eq, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: '{eq}'")
        try:
            solver = LinearEquationsSolver(eq)
            print(f"  Result: {solver}")
        except Exception as e:
            print(f"  Caught: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
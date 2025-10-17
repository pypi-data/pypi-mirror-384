from typing import List, Optional, Union
from ..matrixerror import InvalidMatrixError
from ..adjoint import Adjoint
from ..determinant import Determinant

# Type alias for better readability
Matrix = List[List[float]]

class Matrices3x3:
    """
    A comprehensive class for performing operations on 3x3 matrices.
    
    This class provides methods for:
    - Matrix arithmetic (addition, subtraction, multiplication, division)
    - Scalar operations (multiplication, division)
    - Matrix properties (determinant, adjoint, inverse)
    - Input validation and error handling
    
    All matrices must be 3x3 and contain only numeric values (int or float).
    
    Example:
        >>> mat = Matrices3x3()
        >>> m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        >>> result = mat.add(m1, m2)
    """
    
    # ---------------- Validation ---------------- #
    # def _validate_matrices(
    #     self, 
    #     m1: Matrix, 
    #     m2: Optional[Matrix] = None, 
    #     operation: Optional[str] = None
    # ) -> bool:
    #     """
    #     Validates matrix structure and dimensions for various operations.
        
    #     This internal method ensures that matrices meet all requirements:
    #     - Must be a list of lists
    #     - Must not be empty
    #     - All rows must have equal length
    #     - Must be exactly 3x3 dimensions
    #     - All elements must be numeric (int or float)
        
    #     For binary operations (when m2 is provided), both matrices are validated
    #     and their dimensions are checked for compatibility with the operation.
        
    #     Args:
    #         m1: First matrix to validate
    #         m2: Optional second matrix for binary operations (add, sub, mul, div)
    #         operation: Type of operation being performed. Valid values:
    #                   - "add", "sub": Addition/subtraction (requires same dimensions)
    #                   - "mul", "div": Multiplication/division (requires compatible dimensions)
    #                   - "inv", "det", "adj": Inverse/determinant/adjoint (single matrix)
        
    #     Returns:
    #         True if validation passes
        
    #     Raises:
    #         InvalidMatrixError: If any validation check fails with a descriptive message
        
    #     Example:
    #         >>> mat = Matrices3x3()
    #         >>> m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    #         >>> mat._validate_matrices(m)  # Returns True
    #         >>> mat._validate_matrices([[1, 2], [3, 4]])  # Raises InvalidMatrixError
    #     """
    #     # Validate m1 structure
    #     if not isinstance(m1, list) or not all(isinstance(r, list) for r in m1):
    #         raise InvalidMatrixError("Matrix must be a list of lists.")
        
    #     if len(m1) == 0 or len(m1[0]) == 0:
    #         raise InvalidMatrixError("Matrix cannot be empty.")
        
    #     if not all(len(row) == len(m1[0]) for row in m1):
    #         raise InvalidMatrixError("All rows in the matrix must have equal length.")
        
    #     # Validate m1 is 3x3 for this class
    #     if len(m1) != 3 or len(m1[0]) != 3:
    #         raise InvalidMatrixError("Matrix must be 3x3 for this class.")
        
    #     # Validate all elements are numeric
    #     for i, row in enumerate(m1):
    #         for j, val in enumerate(row):
    #             if not isinstance(val, (int, float)):
    #                 raise InvalidMatrixError(f"All matrix elements must be numeric. Found {type(val).__name__} at position [{i}][{j}].")
        
    #     # Single matrix operations
    #     if m2 is None:
    #         if operation in ("inv", "det", "adj"):
    #             if len(m1) != len(m1[0]):
    #                 raise InvalidMatrixError("Matrix must be square for determinant, inverse, or adjoint operations.")
    #         return True
        
    #     # Validate m2 structure
    #     if not isinstance(m2, list) or not all(isinstance(r, list) for r in m2):
    #         raise InvalidMatrixError("Second matrix must be a list of lists.")
        
    #     if len(m2) == 0 or len(m2[0]) == 0:
    #         raise InvalidMatrixError("Second matrix cannot be empty.")
        
    #     if not all(len(row) == len(m2[0]) for row in m2):
    #         raise InvalidMatrixError("All rows in the second matrix must have equal length.")
        
    #     # Validate m2 is 3x3
    #     if len(m2) != 3 or len(m2[0]) != 3:
    #         raise InvalidMatrixError("Second matrix must be 3x3 for this class.")
        
    #     # Validate all elements in m2 are numeric
    #     for i, row in enumerate(m2):
    #         for j, val in enumerate(row):
    #             if not isinstance(val, (int, float)):
    #                 raise InvalidMatrixError(f"All elements in second matrix must be numeric. Found {type(val).__name__} at position [{i}][{j}].")
        
    #     # Operation-specific validations
    #     if operation in ("add", "sub"):
    #         if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
    #             raise InvalidMatrixError("Matrices must have same dimensions for addition/subtraction.")
        
    #     elif operation in ("mul", "div"):
    #         if len(m1[0]) != len(m2):
    #             raise InvalidMatrixError(f"Number of columns in first matrix ({len(m1[0])}) must equal rows in second matrix ({len(m2)}).")
        
    #     return True
    def _validate_matrices(
        self, 
        m1: Matrix, 
        m2: Optional[Matrix] = None, 
        operation: Optional[str] = None
    ) -> bool:
        """
        Validates matrix structure and dimensions for various operations.
        
        This internal method ensures that matrices meet all requirements:
        - Must be a list of lists
        - Must not be empty
        - All rows must have equal length
        - Must be exactly 3x3 dimensions (except for multiplication)
        - All elements must be numeric (int or float)
        
        For binary operations (when m2 is provided), both matrices are validated
        and their dimensions are checked for compatibility with the operation.
        
        Args:
            m1: First matrix to validate
            m2: Optional second matrix for binary operations (add, sub, mul, div)
            operation: Type of operation being performed. Valid values:
                    - "add", "sub": Addition/subtraction (requires same dimensions)
                    - "mul": Multiplication (m1 must have 3 columns, m2 must have 3 rows)
                    - "div": Division (requires compatible dimensions)
                    - "inv", "det", "adj": Inverse/determinant/adjoint (single matrix)
        
        Returns:
            True if validation passes
        
        Raises:
            InvalidMatrixError: If any validation check fails with a descriptive message
        
        Example:
            >>> mat = Matrices3x3()
            >>> m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            >>> mat._validate_matrices(m)  # Returns True
            >>> mat._validate_matrices([[1, 2], [3, 4]])  # Raises InvalidMatrixError
        """
        # Validate m1 structure
        if not isinstance(m1, list) or not all(isinstance(r, list) for r in m1):
            raise InvalidMatrixError("Matrix must be a list of lists.")
        
        if len(m1) == 0 or len(m1[0]) == 0:
            raise InvalidMatrixError("Matrix cannot be empty.")
        
        if not all(len(row) == len(m1[0]) for row in m1):
            raise InvalidMatrixError("All rows in the matrix must have equal length.")
        
        # Validate m1 is 3x3 for this class (EXCEPT for multiplication)
        if operation != "mul":
            if len(m1) != 3 or len(m1[0]) != 3:
                raise InvalidMatrixError("Matrix must be 3x3 for this class.")
        else:
            # For multiplication, m1 must have 3 columns
            if len(m1[0]) != 3:
                raise InvalidMatrixError("First matrix must have 3 columns for multiplication in this class.")
        
        # Validate all elements are numeric
        for i, row in enumerate(m1):
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    raise InvalidMatrixError(f"All matrix elements must be numeric. Found {type(val).__name__} at position [{i}][{j}].")
        
        # Single matrix operations
        if m2 is None:
            if operation in ("inv", "det", "adj"):
                if len(m1) != len(m1[0]):
                    raise InvalidMatrixError("Matrix must be square for determinant, inverse, or adjoint operations.")
            return True
        
        # Validate m2 structure
        if not isinstance(m2, list) or not all(isinstance(r, list) for r in m2):
            raise InvalidMatrixError("Second matrix must be a list of lists.")
        
        if len(m2) == 0 or len(m2[0]) == 0:
            raise InvalidMatrixError("Second matrix cannot be empty.")
        
        if not all(len(row) == len(m2[0]) for row in m2):
            raise InvalidMatrixError("All rows in the second matrix must have equal length.")
        
        # Validate m2 is 3x3 (EXCEPT for multiplication)
        if operation != "mul":
            if len(m2) != 3 or len(m2[0]) != 3:
                raise InvalidMatrixError("Second matrix must be 3x3 for this class.")
        else:
            # For multiplication, m2 must have 3 rows
            if len(m2) != 3:
                raise InvalidMatrixError("Second matrix must have 3 rows for multiplication in this class.")
        
        # Validate all elements in m2 are numeric
        for i, row in enumerate(m2):
            for j, val in enumerate(row):
                if not isinstance(val, (int, float)):
                    raise InvalidMatrixError(f"All elements in second matrix must be numeric. Found {type(val).__name__} at position [{i}][{j}].")
        
        # Operation-specific validations
        if operation in ("add", "sub"):
            if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
                raise InvalidMatrixError("Matrices must have same dimensions for addition/subtraction.")
        
        elif operation in ("mul", "div"):
            if len(m1[0]) != len(m2):
                raise InvalidMatrixError(f"Number of columns in first matrix ({len(m1[0])}) must equal rows in second matrix ({len(m2)}).")
        
        return True

    # ---------------- Core Operations ---------------- #
    
    def determinant(self, m: Matrix) -> Union[int, float]:
        """
        Calculate the determinant of a 3x3 matrix.
        
        The determinant is a scalar value that encodes certain properties of the matrix.
        A determinant of zero indicates a singular (non-invertible) matrix.
        
        Formula for 3x3 matrix:
            det(A) = a(ei−fh) − b(di−fg) + c(dh−eg)
            where A = [[a,b,c], [d,e,f], [g,h,i]]
        
        Args:
            m: A 3x3 matrix represented as a list of lists
        
        Returns:
            The determinant value (int or float)
        
        Raises:
            InvalidMatrixError: If matrix is not 3x3 or not square
        
        Example:
            >>> mat = Matrices3x3()
            >>> identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            >>> mat.determinant(identity)
            1
            >>> singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
            >>> mat.determinant(singular)
            0
        """
        self._validate_matrices(m, operation="det")
        return Determinant(m).det3x3()

    def adjoint(self, m: Matrix) -> Matrix:
        """
        Calculate the adjoint (adjugate) of a 3x3 matrix.
        
        The adjoint is the transpose of the cofactor matrix. It's used in
        calculating the matrix inverse: A^(-1) = (1/det(A)) * adj(A)
        
        Args:
            m: A 3x3 matrix represented as a list of lists
        
        Returns:
            The adjoint matrix as a list of lists
        
        Raises:
            InvalidMatrixError: If matrix is not 3x3 or not square
        
        Example:
            >>> mat = Matrices3x3()
            >>> identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            >>> mat.adjoint(identity)
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        """
        self._validate_matrices(m, operation="adj")
        return Adjoint(m).adj3x3()

    def multiplicative_inverse(self, m: Matrix) -> Matrix:
        """
        Calculate the multiplicative inverse of a 3x3 matrix.
        
        The inverse of matrix A is a matrix A^(-1) such that A * A^(-1) = I,
        where I is the identity matrix.
        
        Formula: A^(-1) = (1/det(A)) * adj(A)
        
        The inverse exists only for non-singular matrices (determinant ≠ 0).
        
        Args:
            m: A 3x3 matrix represented as a list of lists
        
        Returns:
            The inverse matrix as a list of lists
        
        Raises:
            InvalidMatrixError: If matrix is singular (determinant = 0) or not 3x3
        
        Example:
            >>> mat = Matrices3x3()
            >>> identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            >>> mat.multiplicative_inverse(identity)
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            
            >>> # Verify A * A^(-1) = I
            >>> A = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
            >>> A_inv = mat.multiplicative_inverse(A)
            >>> result = mat.matrix_multiply(A, A_inv)
            >>> # result ≈ identity matrix
        """
        self._validate_matrices(m, operation="inv")
        det = self.determinant(m)
        
        if det == 0:
            raise InvalidMatrixError("Matrix is singular and cannot be inverted.")
        
        adj = self.adjoint(m)
        return self.scalar_multiply(adj, 1/det)

    def add(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Add two 3x3 matrices element-wise.
        
        Matrix addition is performed by adding corresponding elements:
        C[i][j] = A[i][j] + B[i][j] for all i, j
        
        Properties:
        - Commutative: A + B = B + A
        - Associative: (A + B) + C = A + (B + C)
        
        Args:
            m1: First 3x3 matrix (addend)
            m2: Second 3x3 matrix (addend)
        
        Returns:
            Resultant matrix after addition
        
        Raises:
            InvalidMatrixError: If matrices are not both 3x3
        
        Example:
            >>> mat = Matrices3x3()
            >>> m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            >>> m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
            >>> mat.add(m1, m2)
            [[10.0, 10.0, 10.0], [10.0, 10.0, 10.0], [10.0, 10.0, 10.0]]
        """
        self._validate_matrices(m1, m2, operation="add")
        
        result: Matrix = [[], [], []]
        for i in range(3):
            for j in range(3):
                result[i].append(float(m1[i][j] + m2[i][j]))
        
        return result

    def subtract(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Subtract second matrix from first matrix element-wise.
        
        Matrix subtraction is performed by subtracting corresponding elements:
        C[i][j] = A[i][j] - B[i][j] for all i, j
        
        Note: Subtraction is NOT commutative: A - B ≠ B - A
        
        Args:
            m1: First 3x3 matrix (minuend)
            m2: Second 3x3 matrix (subtrahend)
        
        Returns:
            Resultant matrix after subtraction (m1 - m2)
        
        Raises:
            InvalidMatrixError: If matrices are not both 3x3
        
        Example:
            >>> mat = Matrices3x3()
            >>> m1 = [[10, 10, 10], [10, 10, 10], [10, 10, 10]]
            >>> m2 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            >>> mat.subtract(m1, m2)
            [[9.0, 8.0, 7.0], [6.0, 5.0, 4.0], [3.0, 2.0, 1.0]]
        """
        self._validate_matrices(m1, m2, operation="sub")
        
        result: Matrix = [[], [], []]
        for i in range(3):
            for j in range(3):
                result[i].append(float(m1[i][j] - m2[i][j]))
        
        return result

    def matrix_multiply(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Multiply two matrices using standard matrix multiplication.
        
        Matrix multiplication follows the row-by-column rule:
        C[i][j] = Σ(A[i][k] * B[k][j]) for k from 0 to n-1
        where n is the number of columns in m1 (or rows in m2).
        
        For multiplication to be valid, the number of columns in m1 
        must equal the number of rows in m2. The resulting matrix will 
        have dimensions: (rows of m1) X (columns of m2).
        
        Properties:
        - NOT commutative: A X B ≠ B X A (in general)
        - Associative: (A X B) X C = A X (B X C)
        - Distributive: A X (B + C) = A X B + A X C
        
        Args:
            m1: First matrix with dimensions mXn (multiplicand)
            m2: Second matrix with dimensions nXp (multiplier)
        
        Returns:
            Resultant matrix with dimensions mXp after multiplication
        
        Raises:
            InvalidMatrixError: If the number of columns in m1 does not 
                            equal the number of rows in m2
        
        Example:
            >>> mat = Matrices3x3()
            >>> m1 = [[2, 3], [1, 4]]  # 2X2 matrix
            >>> m2 = [[5], [3]]         # 2X1 matrix
            >>> mat.matrix_multiply(m1, m2)
            [[19], [17]]                # 2X1 result
            
            >>> m3 = [[1, 2, 3], [4, 5, 6]]  # 2X3 matrix
            >>> m4 = [[7], [8], [9]]          # 3X1 matrix
            >>> mat.matrix_multiply(m3, m4)
            [[50], [122]]                     # 2X1 result
        """
            
        self._validate_matrices(m1, m2, operation="mul")
        rows: int = len(m1)
        cols: int = len(m2[0])
        common: int = len(m2)
        result: Matrix = [[] for _ in range(rows)]

        for i in range(rows):
            for j in range(cols):
                total: Union[int, float] = 0
                for k in range(common):
                    total += m1[i][k] * m2[k][j]
                result[i].append(total)
        
        return result

    def scalar_multiply(self, m: Matrix, scalar: Union[int, float]) -> Matrix:
        """
        Multiply a 3x3 matrix by a scalar value.
        
        Scalar multiplication multiplies every element in the matrix by the scalar:
        C[i][j] = scalar * A[i][j] for all i, j
        
        Properties:
        - Distributive: k(A + B) = kA + kB
        - Associative: k(cA) = (kc)A
        - Identity: 1 * A = A
        - Zero: 0 * A = zero matrix
        
        Args:
            m: A 3x3 matrix
            scalar: Scalar value to multiply with (int or float)
        
        Returns:
            Resultant matrix after scalar multiplication
        
        Raises:
            InvalidMatrixError: If matrix is not 3x3
        
        Example:
            >>> mat = Matrices3x3()
            >>> m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            >>> mat.scalar_multiply(m, 2)
            [[2, 4, 6], [8, 10, 12], [14, 16, 18]]
            
            >>> mat.scalar_multiply(m, 0.5)
            [[0.5, 1.0, 1.5], [2.0, 2.5, 3.0], [3.5, 4.0, 4.5]]
        """
        self._validate_matrices(m)
        
        result: Matrix = [[], [], []]
        for i in range(3):
            for j in range(3):
                result[i].append(m[i][j] * scalar)
        
        return result

    def matrix_divide(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Divide first matrix by second matrix (equivalent to m1 * m2^(-1)).
        
        Matrix division A / B is defined as A * B^(-1), where B^(-1) is the
        multiplicative inverse of B. This operation is only possible when B
        is non-singular (invertible).
        
        Note: Matrix division is NOT commutative: A / B ≠ B / A
        
        Args:
            m1: First 3x3 matrix (dividend)
            m2: Second 3x3 matrix (divisor)
        
        Returns:
            Resultant matrix after division (m1 * m2^(-1))
        
        Raises:
            InvalidMatrixError: If m2 is singular (determinant = 0) or matrices are not 3x3
        
        Example:
            >>> mat = Matrices3x3()
            >>> m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            >>> identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            >>> mat.matrix_divide(m1, identity)
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]]  # Returns m1
            
            >>> # Verify A / A ≈ I
            >>> A = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
            >>> result = mat.matrix_divide(A, A)
            >>> # result ≈ identity matrix
        """
        self._validate_matrices(m1, m2, operation="div")
        
        inv_m2 = self.multiplicative_inverse(m2)
        return self.matrix_multiply(m1, inv_m2)

    def scalar_divide(self, m: Matrix, scalar: Union[int, float]) -> Matrix:
        """
        Divide a 3x3 matrix by a scalar value.
        
        Scalar division divides every element in the matrix by the scalar:
        C[i][j] = A[i][j] / scalar for all i, j
        
        This is equivalent to multiplying by 1/scalar.
        
        Args:
            m: A 3x3 matrix
            scalar: Scalar value to divide by (int or float, cannot be zero)
        
        Returns:
            Resultant matrix after scalar division
        
        Raises:
            InvalidMatrixError: If matrix is not 3x3 or scalar is zero
        
        Example:
            >>> mat = Matrices3x3()
            >>> m = [[2, 4, 6], [8, 10, 12], [14, 16, 18]]
            >>> mat.scalar_divide(m, 2)
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
            
            >>> mat.scalar_divide(m, 0)  # Raises InvalidMatrixError
        """
        if scalar == 0:
            raise InvalidMatrixError("Division by zero is not allowed.")
        
        self._validate_matrices(m)
        
        result: Matrix = [[], [], []]
        for i in range(3):
            for j in range(3):
                result[i].append(m[i][j] / scalar)
        
        return result


if __name__ == "__main__":
    """
    Demonstration of Matrices3x3 class functionality.
    
    This demo showcases all major operations:
    1. Matrix addition and subtraction
    2. Matrix and scalar multiplication
    3. Matrix and scalar division
    4. Determinant calculation
    5. Adjoint matrix
    6. Multiplicative inverse
    7. Verification of mathematical properties
    """
    
    print("=" * 60)
    print("MATRICES 3x3 - DEMONSTRATION")
    print("=" * 60)
    
    # Initialize the class
    mat = Matrices3x3()
    
    # Define sample matrices
    print("\n1. SAMPLE MATRICES")
    print("-" * 60)
    
    m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    print("Matrix A:")
    for row in m1:
        print(f"  {row}")
    
    m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
    print("\nMatrix B:")
    for row in m2:
        print(f"  {row}")
    
    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    print("\nIdentity Matrix (I):")
    for row in identity:
        print(f"  {row}")
    
    # Addition
    print("\n2. ADDITION (A + B)")
    print("-" * 60)
    result_add = mat.add(m1, m2)
    for row in result_add:
        print(f"  {row}")
    
    # Subtraction
    print("\n3. SUBTRACTION (A - B)")
    print("-" * 60)
    result_sub = mat.subtract(m1, m2)
    for row in result_sub:
        print(f"  {row}")
    
    # Matrix multiplication
    print("\n4. MATRIX MULTIPLICATION (A X B)")
    print("-" * 60)
    result_mul = mat.matrix_multiply(m1, m2)
    for row in result_mul:
        print(f"  {row}")
    
    # Verify: A X I = A
    print("\n5. VERIFICATION: A X I = A")
    print("-" * 60)
    result_identity = mat.matrix_multiply(m1, identity)
    print("Result of A X I:")
    for row in result_identity:
        print(f"  {row}")
    print(" Verified: A X I = A")
    
    # Scalar multiplication
    print("\n6. SCALAR MULTIPLICATION (2 X A)")
    print("-" * 60)
    result_scalar = mat.scalar_multiply(m1, 2)
    for row in result_scalar:
        print(f"  {row}")
    
    # Scalar division
    print("\n7. SCALAR DIVISION (A / 2)")
    print("-" * 60)
    result_div_scalar = mat.scalar_divide(result_scalar, 2)
    for row in result_div_scalar:
        print(f"  {row}")
    
    # Determinant
    print("\n8. DETERMINANT")
    print("-" * 60)
    det_m1 = mat.determinant(m1)
    print(f"Determinant of A: {det_m1}")
    
    det_identity = mat.determinant(identity)
    print(f"Determinant of I: {det_identity}")
    
    # Invertible matrix example
    invertible = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
    print("\nInvertible Matrix C:")
    for row in invertible:
        print(f"  {row}")
    
    det_inv = mat.determinant(invertible)
    print(f"Determinant of C: {det_inv}")
    
    # Adjoint
    print("\n9. ADJOINT MATRIX")
    print("-" * 60)
    adj_inv = mat.adjoint(invertible)
    print("Adjoint of C:")
    for row in adj_inv:
        print(f"  {row}")
    
    # Multiplicative inverse
    print("\n10. MULTIPLICATIVE INVERSE")
    print("-" * 60)
    inv_matrix = mat.multiplicative_inverse(invertible)
    print("Inverse of C (C⁻¹):")
    for row in inv_matrix:
        print(f"  {[round(val, 6) for val in row]}")
    
    # Verify: C X C^(-1) = I
    print("\n11. VERIFICATION: C X C⁻¹ = I")
    print("-" * 60)
    verification = mat.matrix_multiply(invertible, inv_matrix)
    print("Result of C X C⁻¹:")
    for row in verification:
        print(f"  {[round(val, 6) for val in row]}")
    print(" Verified: Result is approximately identity matrix")
    
    # Matrix division
    print("\n12. MATRIX DIVISION (C / I)")
    print("-" * 60)
    result_div_mat = mat.matrix_divide(invertible, identity)
    print("Result of C / I:")
    for row in result_div_mat:
        print(f"  {row}")
    print(" Verified: C / I = C")
    
    # Error handling demonstration
    print("\n13. ERROR HANDLING")
    print("-" * 60)
    
    singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
    print("Singular Matrix (non-invertible):")
    for row in singular:
        print(f"  {row}")
    
    try:
        det_singular = mat.determinant(singular)
        print(f"Determinant: {det_singular}")
        inv_singular = mat.multiplicative_inverse(singular)
    except InvalidMatrixError as e:
        print(f" Error caught correctly: {e}")
    
    print("\nAttempting scalar division by zero:")
    try:
        mat.scalar_divide(m1, 0)
    except InvalidMatrixError as e:
        print(f" Error caught correctly: {e}")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
from .matrixerror import InvalidMatrixError

class Adjoint:
    """
    A class to compute the adjoint (adjugate) of 2X2 or 3X3 matrices.

    The adjoint (or adjugate) of a matrix A is defined as the transpose
    of its cofactor matrix. It is a key component for computing the inverse:
        A⁻¹ = adj(A) / det(A)

    Parameters
    ----------
    matrix : list[list[str | int | float]]
        A 2X2 or 3X3 matrix (list of lists). Elements can be numeric strings or numbers.

    Raises
    ------
    InvalidMatrixError
        If the matrix is invalid, not square, not 2X2 or 3X3, or contains non-numeric values.

    Examples
    --------
    >>> m1 = Adjoint([['-2', '+3'], ['-1', '-5']])
    >>> print(m1.adj2x2())
    [[-5.0, -3.0], [1.0, -2.0]]

    >>> m2 = Adjoint([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    >>> print(m2.adj3x3())
    [[-24.0, 18.0, 5.0],
     [20.0, -15.0, -4.0],
     [-5.0, 4.0, 1.0]]
    """

    def __init__(self, matrix: list[list[str | int | float]]):
        """
        Initialize and validate the matrix.

        Ensures the matrix:
        - Is a list of lists
        - Has equal-length rows
        - Has valid dimensions (2X2 or 3X3)
        - Contains only numeric values (int, float, or numeric string)

        Raises
        ------
        InvalidMatrixError
            If the matrix fails validation.
        """
        if not all(isinstance(row, list) for row in matrix):
            raise InvalidMatrixError("Matrix must be a list of lists.")
        if not all(len(row) == len(matrix[0]) for row in matrix):
            raise InvalidMatrixError("All rows must have equal length.")

        rows, cols = len(matrix), len(matrix[0])
        if not ((rows, cols) == (2, 2) or (rows, cols) == (3, 3)):
            raise InvalidMatrixError("Only 2x2 or 3x3 matrices are supported.")

        try:
            self.matrix = [[float(ele) for ele in row] for row in matrix]
        except ValueError:
            raise InvalidMatrixError("Matrix contains non-numeric values.")

    def adj2x2(self):
        """
        Compute the adjoint (adjugate) of a 2X2 matrix.

        Formula:
            For matrix [ [a, b], [c, d] ]
            adj(A) = [ [ d, -b ],
                       [ -c,  a ] ]

        Returns
        -------
        list[list[float]]
            The 2X2 adjoint matrix.

        Raises
        ------
        InvalidMatrixError
            If the matrix is not 2X2.
        """
        if len(self.matrix) != 2:
            raise InvalidMatrixError("Matrix is not 2X2.")
        a, b = self.matrix[0]
        c, d = self.matrix[1]
        return [[d, -b], [-c, a]]

    def adj3x3(self):
        """
        Compute the adjoint (adjugate) of a 3X3 matrix.

        Formula:
            adj(A) = transpose(cofactor(A))

            For matrix:
                [a, b, c]
                [d, e, f]
                [g, h, i]

        Cofactor matrix (before transpose):
            [
                [ e*i - f*h,  -(d*i - f*g),  d*h - e*g ],
                [-(b*i - c*h),  a*i - c*g,  -(a*h - b*g)],
                [ b*f - c*e,  -(a*f - c*d),  a*e - b*d ]
            ]

        Returns
        -------
        list[list[float]]
            The 3X3 adjoint matrix.

        Raises
        ------
        InvalidMatrixError
            If the matrix is not 3X3.
        """
        if len(self.matrix) != 3:
            raise InvalidMatrixError("Matrix is not 3X3.")

        a, b, c = self.matrix[0]
        d, e, f = self.matrix[1]
        g, h, i = self.matrix[2]

        return [
            [(e*i - f*h), -(b*i - c*h), (b*f - c*e)],
            [-(d*i - f*g), (a*i - c*g), -(a*f - c*d)],
            [(d*h - e*g), -(a*h - b*g), (a*e - b*d)]
        ]

    def compute_adjoint(self):
        """
        Automatically compute the adjoint (adjugate) of the stored matrix.

        Detects matrix size (2X2 or 3X3) and calls the correct function.

        Returns
        -------
        list[list[float]]
            The computed adjoint matrix.
        """
        size = len(self.matrix)
        if size == 2:
            return self.adj2x2()
        elif size == 3:
            return self.adj3x3()
        raise InvalidMatrixError("Unsupported matrix size.")


# ==========================
# 🔹 DEMONSTRATION SECTION 🔹
# ==========================

if __name__ == "__main__":
    print("---- Adjoint Demo ----\n")

    # Example 1: 2X2 Matrix
    try:
        m1 = Adjoint([['-2', '+3'], ['-1', '-5']])
        print("Original 2X2 Matrix:")
        for row in m1.matrix:
            print(row)
        print("\nAdjoint of Matrix 1 (using adj2x2):")
        for row in m1.adj2x2():
            print(row)
        print("\nAdjoint (auto-detected via compute_adjoint):")
        for row in m1.compute_adjoint():
            print(row)
    except InvalidMatrixError as e:
        print("Error in Matrix 1:", e)

    print("\n-----------------------------\n")

    # Example 2: 3X3 Matrix
    try:
        m2 = Adjoint([[1, 2, 3],
                      [0, 1, 4],
                      [5, 6, 0]])
        print("Original 3X3 Matrix:")
        for row in m2.matrix:
            print(row)
        print("\nAdjoint of Matrix 2 (using adj3x3):")
        for row in m2.adj3x3():
            print(row)
        print("\nAdjoint (auto-detected via compute_adjoint):")
        for row in m2.compute_adjoint():
            print(row)
    except InvalidMatrixError as e:
        print("Error in Matrix 2:", e)

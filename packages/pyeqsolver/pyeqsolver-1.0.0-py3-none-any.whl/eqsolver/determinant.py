from .matrixerror import InvalidMatrixError

class Determinant:
    """
    A class to calculate the determinant of a 2x2 or 3x3 matrix.

    This class automatically validates the given matrix, ensuring it is properly
    rectangular (all rows have the same length) and contains numeric elements.
    It supports both integer and float (or string representations of numbers).

    You can either call:
        - `det2x2()` to compute a 2x2 determinant
        - `det3x3()` to compute a 3x3 determinant
        - or simply `det()` which auto-detects and chooses the correct one

    Attributes
    ----------
    matrix : list[list[str | int | float]]
        The input matrix. Must be either 2x2 or 3x3.

    Methods
    -------
    det() -> float:
        Automatically computes the determinant depending on matrix size.
    
    det2x2() -> float:
        Computes the determinant of a 2x2 matrix.

    det3x3() -> float:
        Computes the determinant of a 3x3 matrix.

    Examples
    --------
    >>> # Example 1: 2x2 determinant
    >>> m1 = Determinant([[1, 2], [3, 4]])
    >>> print(m1.det())
    -2.0

    >>> # Example 2: 3x3 determinant
    >>> m2 = Determinant([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    >>> print(m2.det())
    1.0

    >>> # Example 3: Invalid matrix
    >>> Determinant([[1, 2], [3]])  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    InvalidMatrixError: All rows must have equal length.
    """

    def __init__(self, matrix: list[list[str | int | float]]):
        """
        Initialize the Determinant object.

        Parameters
        ----------
        matrix : list[list[str | int | float]]
            The matrix to calculate the determinant for.

        Raises
        ------
        InvalidMatrixError
            If the matrix is not 2x2 or 3x3, contains non-numeric data,
            or rows are not of equal length.
        """
        # Validate input is a list of lists
        if not all(isinstance(row, list) for row in matrix):
            raise InvalidMatrixError("Matrix must be a list of lists.")

        # Ensure all rows are the same length
        if not all(len(row) == len(matrix[0]) for row in matrix):
            raise InvalidMatrixError("All rows must have equal length.")

        # Check valid dimensions
        rows, cols = len(matrix), len(matrix[0])
        if not ((rows, cols) == (2, 2) or (rows, cols) == (3, 3)):
            raise InvalidMatrixError("Only 2x2 or 3x3 matrices are supported.")

        # Convert all elements to float
        try:
            self.matrix = [[float(ele) for ele in row] for row in matrix]
        except ValueError:
            raise InvalidMatrixError("Matrix contains non-numeric values.")

    # -------------------- 2x2 Determinant --------------------
    def det2x2(self) -> float:
        """
        Compute the determinant of a 2x2 matrix.

        Returns
        -------
        float
            The determinant value.

        Raises
        ------
        InvalidMatrixError
            If the matrix is not 2x2.
        """
        if len(self.matrix) != 2 or len(self.matrix[0]) != 2:
            raise InvalidMatrixError("Matrix is not 2x2.")

        a, b = self.matrix[0]
        c, d = self.matrix[1]
        det = a * d - b * c
        return round(det, 6)

    # -------------------- 3x3 Determinant --------------------
    def det3x3(self) -> float:
        """
        Compute the determinant of a 3x3 matrix.

        Returns
        -------
        float
            The determinant value.

        Raises
        ------
        InvalidMatrixError
            If the matrix is not 3x3.
        """
        if len(self.matrix) != 3 or len(self.matrix[0]) != 3:
            raise InvalidMatrixError("Matrix is not 3x3.")

        a, b, c = self.matrix[0]
        d, e, f = self.matrix[1]
        g, h, i = self.matrix[2]

        det = (
            a * (e * i - f * h)
            - b * (d * i - f * g)
            + c * (d * h - e * g)
        )
        return round(det, 6)

    # -------------------- Auto Detection --------------------
    def det(self) -> float:
        """
        Automatically compute the determinant based on matrix size.

        Returns
        -------
        float
            The determinant value (2x2 or 3x3).

        Raises
        ------
        InvalidMatrixError
            If matrix size is unsupported.
        """
        size = len(self.matrix)
        if size == 2:
            return self.det2x2()
        elif size == 3:
            return self.det3x3()
        else:
            raise InvalidMatrixError("Unsupported matrix size.")


# ------------------ DEMO ------------------
if __name__ == "__main__":
    #  Example 1: 2x2 determinant
    m1 = Determinant([['-2', '+3'], ['-1', '-5']])
    print("2x2 Matrix:", m1.matrix)
    print("Determinant:", m1.det())

    #  Example 2: 3x3 determinant
    m2 = Determinant([[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    print("\n3x3 Matrix:", m2.matrix)
    print("Determinant:", m2.det())

    #  Example 3: Invalid matrix (uneven rows)
    try:
        m3 = Determinant([[1, 2], [3]])
    except InvalidMatrixError as e:
        print("\nError:", e)

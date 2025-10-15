from typing import List, Optional, Union
from ..matrixerror import InvalidMatrixError
from ..adjoint import Adjoint
from ..determinant import Determinant

# Type alias for better readability
Matrix = List[List[float]]

class Matrices2x2:
    """
    A class for performing mathematical operations on **2x2 matrices**.

    This class supports:
        - Addition and Subtraction of matrices
        - Multiplication (Matrix X Matrix or Matrix X Scalar)
        - Division (Matrix ÷ Matrix or Matrix ÷ Scalar)
        - Determinant calculation
        - Adjoint (Adjugate) matrix
        - Multiplicative inverse (A⁻¹)

    Notes
    -----
    This class is specifically designed for **2x2 matrices**.
    For larger matrices, the determinant and inverse methods must be extended.

    Example
    -------
    >>> from matrixerror import InvalidMatrixError
    >>> from adjoint import Adjoint
    >>> from determinant import Determinant
    >>> from matrices2x2 import Matrices2x2

    >>> m = Matrices2x2()

    >>> A = [[2, 3],
    ...      [1, 4]]

    >>> B = [[5, 2],
    ...      [7, 6]]

    # Matrix addition
    >>> m.add(A, B)
    [[7.0, 5.0], [8.0, 10.0]]

    # Matrix multiplication
    >>> m.multiply(A, B)
    [[31, 22], [33, 26]]

    # Determinant
    >>> m.determinant(A)
    5

    # Inverse
    >>> m.multiplicative_inverse(A)
    [[0.8, -0.6], [-0.2, 0.4]]

    # Scalar division
    >>> m.divide(A, num=2)
    [[1.0, 1.5], [0.5, 2.0]]
    """

    # ---------------- Validation ---------------- #
    def _validate_matrices(
        self, 
        m1: Matrix, 
        m2: Optional[Matrix] = None, 
        operation: Optional[str] = None
    ) -> bool:
        """
        Validates the structure and compatibility of matrices based on operation type.

        Parameters
        ----------
        m1 : list[list[float]]
            The first matrix.
        m2 : list[list[float]], optional
            The second matrix (if required for the operation).
        operation : str, optional
            Type of operation ('add', 'sub', 'mul', 'div', 'det', 'inv').

        Raises
        ------
        InvalidMatrixError
            If the matrices are invalid or incompatible for the specified operation.

        Returns
        -------
        bool
            True if validation passes.
        """
        if not isinstance(m1, list) or not all(isinstance(r, list) for r in m1):
            raise InvalidMatrixError("Matrix must be a list of lists.")

        if not all(len(row) == len(m1[0]) for row in m1):
            raise InvalidMatrixError("All rows in the matrix must have equal length.")

        if m2 is None:
            if operation in ("inv", "det"):
                if len(m1) != len(m1[0]):
                    raise InvalidMatrixError("Matrix must be square for determinant or inverse.")
            return True

        if not isinstance(m2, list) or not all(isinstance(r, list) for r in m2):
            raise InvalidMatrixError("Second matrix must be a list of lists.")

        if not all(len(row) == len(m2[0]) for row in m2):
            raise InvalidMatrixError("All rows in the second matrix must have equal length.")

        if operation in ("add", "sub"):
            if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
                raise InvalidMatrixError("Matrices must have same dimensions for addition/subtraction.")
        elif operation in ("mul", "div"):
            if len(m1[0]) != len(m2):
                raise InvalidMatrixError("Number of columns in first matrix must equal rows in second.")

        return True

    # ---------------- Core Operations ---------------- #
    def determinant(self, m: Matrix) -> Union[int, float]:
        """
        Computes the determinant of a 2x2 matrix.

        Formula:
            det(A) = a*d - b*c

        Parameters
        ----------
        m : list[list[float]]
            Input 2x2 matrix.

        Returns
        -------
        float
            Determinant of the matrix.
        """
        self._validate_matrices(m, operation="det")
        return Determinant(m).det2x2()

    def adjoint(self, m: Matrix) -> Matrix:
        """
        Returns the adjoint (adjugate) of a 2x2 matrix.

        For matrix [[a, b], [c, d]]:
            adj(A) = [[d, -b], [-c, a]]

        Parameters
        ----------
        m : list[list[float]]
            Input 2x2 matrix.

        Returns
        -------
        list[list[float]]
            Adjoint matrix.
        """
        self._validate_matrices(m, operation="adj")
        return Adjoint(m).adj2x2()

    def multiplicative_inverse(self, m: Matrix) -> Matrix:
        """
        Computes the multiplicative inverse of a 2x2 matrix.

        Formula:
            A⁻¹ = (1 / det(A)) X adj(A)

        Parameters
        ----------
        m : list[list[float]]
            Input 2x2 matrix.

        Returns
        -------
        list[list[float]]
            Inverse matrix.

        Raises
        ------
        InvalidMatrixError
            If matrix is singular (det(A) = 0).
        """
        self._validate_matrices(m, operation="inv")
        det = self.determinant(m)
        if det == 0:
            raise InvalidMatrixError("Matrix is singular and cannot be inverted.")
        adj = self.adjoint(m)
        return self.multiply(adj, num=(1/det))

    def add(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Adds two 2x2 matrices element-wise.

        Formula:
            C = A + B

        Returns
        -------
        list[list[float]]
            Resultant matrix after addition.
        """
        self._validate_matrices(m1, m2, operation="add")
        m: Matrix = [[], []]
        i: int = 0
        while i <= 1:
            for j in range(2):
                m[i].append(float(m1[i][j] + m2[i][j]))
            i += 1
        return m

    def subtract(self, m1: Matrix, m2: Matrix) -> Matrix:
        """
        Subtracts the second matrix from the first.

        Formula:
            C = A - B

        Returns
        -------
        list[list[float]]
            Resultant matrix after subtraction.
        """
        self._validate_matrices(m1, m2, operation="sub")
        m: Matrix = [[], []]
        i: int = 0
        while i <= 1:
            for j in range(2):
                m[i].append(float(m1[i][j] - m2[i][j]))
            i += 1
        return m

    def multiply(
        self, 
        m1: Matrix, 
        m2: Optional[Matrix] = None, 
        num: Optional[Union[int, float]] = None
    ) -> Matrix:
        """
        Multiplies a matrix by another matrix or a scalar.

        Supported:
            - A X B   (Matrix X Matrix)
            - A X k   (Matrix X Scalar)

        Parameters
        ----------
        m1 : list[list[float]]
            First matrix.
        m2 : list[list[float]], optional
            Second matrix for matrix multiplication.
        num : float, optional
            Scalar multiplier.

        Returns
        -------
        list[list[float]]
            Resultant matrix.
        """
        # Check for mutual exclusivity
        if m2 is not None and num is not None:
            raise InvalidMatrixError("Provide either m2 or num, not both.")
        
        if m2 is None and num is None:
            raise InvalidMatrixError("You must provide either a matrix (m2) or a scalar (num) for multiplication.")
        
        if num is not None:
            self._validate_matrices(m1)
            m: Matrix = [[] for _ in range(len(m1))]
            for i in range(len(m1)):
                for j in range(len(m1[0])):
                    m[i].append(m1[i][j] * num)
            return m

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

    def divide(
        self, 
        m1: Matrix, 
        m2: Optional[Matrix] = None, 
        num: Optional[Union[int, float]] = None
    ) -> Matrix:
        """
        Divides a matrix by another matrix or a scalar.

        Supports:
            - A ÷ k  =  A X (1/k)
            - A ÷ B  =  A X (B⁻¹)

        Parameters
        ----------
        m1 : list[list[float]]
            Dividend matrix.
        m2 : list[list[float]], optional
            Divisor matrix.
        num : float, optional
            Scalar divisor.

        Returns
        -------
        list[list[float]]
            Resultant matrix after division.
        """
        # Check for mutual exclusivity
        if m2 is not None and num is not None:
            raise InvalidMatrixError("Provide either m2 or num, not both.")
        
        if m2 is None and num is None:
            raise InvalidMatrixError("You must provide either a matrix (m2) or a scalar (num) for division.")
        
        if num is not None:
            if num == 0:
                raise InvalidMatrixError("Division by zero is not allowed.")
            self._validate_matrices(m1)
            m: Matrix = [[] for i in range(len(m1))]
            for i, r in enumerate(m1):
                for c in r:
                    m[i].append(c / num)
            return m

        self._validate_matrices(m1, m2, operation="div")
        inv_b: Matrix = self.multiplicative_inverse(m2)
        return self.multiply(m1, inv_b)


if __name__ == "__main__":
    # ---------------- DEMO: How to use Matrices2x2 ---------------- #
    from pprint import pprint

    # Create an instance
    calc: Matrices2x2 = Matrices2x2()

    # Example matrices
    A: Matrix = [[2, 3],
                 [1, 4]]

    B: Matrix = [[5, 2],
                 [3, 1]]

    print("Matrix A:")
    pprint(A)
    print("\nMatrix B:")
    pprint(B)

    # --- Addition ---
    print("\nA + B =")
    pprint(calc.add(A, B))

    # --- Subtraction ---
    print("\nA - B =")
    pprint(calc.subtract(A, B))

    # --- Multiplication (Matrix × Matrix) ---
    print("\nA × B =")
    pprint(calc.multiply(A, B))

    # --- Multiplication (Matrix × Scalar) ---
    print("\nA × 2 =")
    pprint(calc.multiply(A, num=2))

    # --- Division (Matrix ÷ Scalar) ---
    print("\nA ÷ 2 =")
    pprint(calc.divide(A, num=2))

    # --- Determinant ---
    print("\nDeterminant of A:")
    print(calc.determinant(A))

    # --- Adjoint ---
    print("\nAdjoint of A:")
    pprint(calc.adjoint(A))

    # --- Inverse ---
    print("\nInverse of A:")
    pprint(calc.multiplicative_inverse(A))
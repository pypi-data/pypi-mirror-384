"""
Unit tests for Matrices2x2 class.
Run with: pytest test_matrices2x2.py -v
"""

import pytest
from matrices2x2 import Matrices2x2
from matrixerror import InvalidMatrixError


@pytest.fixture
def calc():
    """Provides a fresh Matrices2x2 instance for each test."""
    return Matrices2x2()


def test_add_basic(calc):
    """Test basic 2x2 matrix addition."""
    A = [[2, 3], [1, 4]]
    B = [[5, 2], [3, 1]]
    result = calc.add(A, B)
    
    # A + B = [[2+5, 3+2], [1+3, 4+1]] = [[7, 5], [4, 5]]
    assert result == [[7.0, 5.0], [4.0, 5.0]]


def test_subtract_basic(calc):
    """Test basic 2x2 matrix subtraction."""
    A = [[2, 3], [1, 4]]
    B = [[5, 2], [3, 1]]
    result = calc.subtract(A, B)
    
    # A - B = [[2-5, 3-2], [1-3, 4-1]] = [[-3, 1], [-2, 3]]
    assert result == [[-3.0, 1.0], [-2.0, 3.0]]


def test_multiply_by_scalar(calc):
    """Test matrix times scalar."""
    A = [[2, 3], [1, 4]]
    result = calc.multiply(A, num=2)
    
    assert result == [[4, 6], [2, 8]]


def test_multiply_matrices(calc):
    """Test matrix multiplication."""
    A = [[2, 3], [1, 4]]
    B = [[5, 2], [3, 1]]
    result = calc.multiply(A, B)
    
    # [2*5+3*3, 2*2+3*1] = [19, 7]
    # [1*5+4*3, 1*2+4*1] = [17, 6]
    assert result == [[19, 7], [17, 6]]


def test_determinant_basic(calc):
    """Test determinant calculation."""
    A = [[2, 3], [1, 4]]
    result = calc.determinant(A)
    
    # det = 2*4 - 3*1 = 5
    assert result == 5


def test_divide_by_scalar(calc):
    """Test matrix divided by scalar."""
    A = [[2, 3], [1, 4]]
    result = calc.divide(A, num=2)
    
    assert result == [[1.0, 1.5], [0.5, 2.0]]


def test_divide_by_zero_raises_error(calc):
    """Test that dividing by zero raises error."""
    A = [[2, 3], [1, 4]]
    
    with pytest.raises(InvalidMatrixError):
        calc.divide(A, num=0)


def test_multiply_both_args_raises_error(calc):
    """Test that providing both m2 and num raises error."""
    A = [[2, 3], [1, 4]]
    B = [[5, 2], [3, 1]]
    
    with pytest.raises(InvalidMatrixError):
        calc.multiply(A, B, num=2)


def test_inverse_singular_raises_error(calc):
    """Test that inverse of singular matrix raises error."""
    singular = [[2, 4], [1, 2]]  # det = 0
    
    with pytest.raises(InvalidMatrixError):
        calc.multiplicative_inverse(singular)


def test_identity_matrix(calc):
    """Test operations with identity matrix."""
    A = [[2, 3], [1, 4]]
    I = [[1, 0], [0, 1]]
    
    # A * I = A
    result = calc.multiply(A, I)
    assert result == [[2, 3], [1, 4]]


if __name__ == "__main__":
    print("Run tests with: pytest test_matrices2x2.py -v")
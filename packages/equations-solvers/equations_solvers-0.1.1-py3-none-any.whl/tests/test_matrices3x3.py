import pytest
from matrices3x3 import Matrices3x3
from matrixerror import InvalidMatrixError


class TestMatrices3x3Validation:
    """Test validation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_valid_3x3_matrix(self):
        """Test that valid 3x3 matrix passes validation"""
        valid_matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        assert self.mat._validate_matrices(valid_matrix) == True
    
    def test_empty_matrix(self):
        """Test that empty matrix raises error"""
        with pytest.raises(InvalidMatrixError, match="Matrix cannot be empty"):
            self.mat._validate_matrices([])
    
    def test_empty_rows(self):
        """Test that matrix with empty rows raises error"""
        with pytest.raises(InvalidMatrixError, match="Matrix cannot be empty"):
            self.mat._validate_matrices([[], [], []])
    
    def test_not_list(self):
        """Test that non-list input raises error"""
        with pytest.raises(InvalidMatrixError, match="Matrix must be a list of lists"):
            self.mat._validate_matrices("not a matrix")
    
    def test_not_3x3_matrix(self):
        """Test that non-3x3 matrix raises error"""
        with pytest.raises(InvalidMatrixError, match="Matrix must be 3x3"):
            self.mat._validate_matrices([[1, 2], [3, 4]])
    
    def test_unequal_row_lengths(self):
        """Test that matrix with unequal row lengths raises error"""
        with pytest.raises(InvalidMatrixError, match="All rows in the matrix must have equal length"):
            self.mat._validate_matrices([[1, 2, 3], [4, 5], [7, 8, 9]])
    
    def test_non_numeric_elements(self):
        """Test that matrix with non-numeric elements raises error"""
        with pytest.raises(InvalidMatrixError, match="All matrix elements must be numeric"):
            self.mat._validate_matrices([[1, 2, 3], [4, "5", 6], [7, 8, 9]])
    
    def test_two_valid_matrices(self):
        """Test validation of two valid matrices"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        assert self.mat._validate_matrices(m1, m2, operation="add") == True
    
    def test_second_matrix_invalid(self):
        """Test that invalid second matrix raises error"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m2 = [[1, 2], [3, 4]]
        with pytest.raises(InvalidMatrixError, match="Second matrix must be 3x3"):
            self.mat._validate_matrices(m1, m2, operation="add")


class TestDeterminant:
    """Test determinant calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_determinant_identity_matrix(self):
        """Test determinant of identity matrix"""
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        assert self.mat.determinant(identity) == 1
    
    def test_determinant_zero_matrix(self):
        """Test determinant of zero matrix"""
        zero = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        assert self.mat.determinant(zero) == 0
    
    def test_determinant_singular_matrix(self):
        """Test determinant of singular matrix"""
        singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        assert self.mat.determinant(singular) == 0
    
    def test_determinant_regular_matrix(self):
        """Test determinant of regular matrix"""
        matrix = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
        result = self.mat.determinant(matrix)
        assert result == 1  # Expected determinant value


class TestAddition:
    """Test matrix addition"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_add_two_matrices(self):
        """Test adding two matrices"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        expected = [[10, 10, 10], [10, 10, 10], [10, 10, 10]]
        result = self.mat.add(m1, m2)
        assert result == expected
    
    def test_add_zero_matrix(self):
        """Test adding zero matrix"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        zero = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = self.mat.add(m1, zero)
        assert result == m1
    
    def test_add_negative_values(self):
        """Test adding matrices with negative values"""
        m1 = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
        m2 = [[-1, 2, -3], [4, -5, 6], [-7, 8, -9]]
        expected = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = self.mat.add(m1, m2)
        assert result == expected


class TestSubtraction:
    """Test matrix subtraction"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_subtract_two_matrices(self):
        """Test subtracting two matrices"""
        m1 = [[10, 10, 10], [10, 10, 10], [10, 10, 10]]
        m2 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        result = self.mat.subtract(m1, m2)
        assert result == expected
    
    def test_subtract_same_matrix(self):
        """Test subtracting matrix from itself"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = self.mat.subtract(m1, m1)
        assert result == expected
    
    def test_subtract_with_floats(self):
        """Test subtraction with floating point values"""
        m1 = [[1.5, 2.5, 3.5], [4.5, 5.5, 6.5], [7.5, 8.5, 9.5]]
        m2 = [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]]
        expected = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        result = self.mat.subtract(m1, m2)
        assert result == expected


class TestMatrixMultiplication:
    """Test matrix multiplication"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_multiply_identity_matrix(self):
        """Test multiplying by identity matrix"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        result = self.mat.matrix_multiply(m1, identity)
        assert result == m1
    
    def test_multiply_zero_matrix(self):
        """Test multiplying by zero matrix"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        zero = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        expected = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = self.mat.matrix_multiply(m1, zero)
        assert result == expected
    
    def test_multiply_two_matrices(self):
        """Test standard matrix multiplication"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        expected = [[30, 24, 18], [84, 69, 54], [138, 114, 90]]
        result = self.mat.matrix_multiply(m1, m2)
        assert result == expected
    
    def test_multiply_non_commutative(self):
        """Test that matrix multiplication is non-commutative"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        m2 = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
        result1 = self.mat.matrix_multiply(m1, m2)
        result2 = self.mat.matrix_multiply(m2, m1)
        assert result1 != result2


class TestScalarMultiplication:
    """Test scalar multiplication"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_scalar_multiply_by_zero(self):
        """Test multiplying by scalar zero"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        result = self.mat.scalar_multiply(m, 0)
        assert result == expected
    
    def test_scalar_multiply_by_one(self):
        """Test multiplying by scalar one"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = self.mat.scalar_multiply(m, 1)
        assert result == m
    
    def test_scalar_multiply_by_integer(self):
        """Test multiplying by integer scalar"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[2, 4, 6], [8, 10, 12], [14, 16, 18]]
        result = self.mat.scalar_multiply(m, 2)
        assert result == expected
    
    def test_scalar_multiply_by_float(self):
        """Test multiplying by float scalar"""
        m = [[2, 4, 6], [8, 10, 12], [14, 16, 18]]
        expected = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        result = self.mat.scalar_multiply(m, 0.5)
        assert result == expected
    
    def test_scalar_multiply_by_negative(self):
        """Test multiplying by negative scalar"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[-1, -2, -3], [-4, -5, -6], [-7, -8, -9]]
        result = self.mat.scalar_multiply(m, -1)
        assert result == expected


class TestScalarDivision:
    """Test scalar division"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_scalar_divide_by_one(self):
        """Test dividing by scalar one"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = self.mat.scalar_divide(m, 1)
        assert result == m
    
    def test_scalar_divide_by_integer(self):
        """Test dividing by integer scalar"""
        m = [[2, 4, 6], [8, 10, 12], [14, 16, 18]]
        expected = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        result = self.mat.scalar_divide(m, 2)
        assert result == expected
    
    def test_scalar_divide_by_float(self):
        """Test dividing by float scalar"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        expected = [[2.0, 4.0, 6.0], [8.0, 10.0, 12.0], [14.0, 16.0, 18.0]]
        result = self.mat.scalar_divide(m, 0.5)
        assert result == expected
    
    def test_scalar_divide_by_zero(self):
        """Test dividing by zero raises error"""
        m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        with pytest.raises(InvalidMatrixError, match="Division by zero is not allowed"):
            self.mat.scalar_divide(m, 0)


class TestMultiplicativeInverse:
    """Test matrix inverse calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_inverse_identity_matrix(self):
        """Test inverse of identity matrix"""
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        result = self.mat.multiplicative_inverse(identity)
        assert result == identity
    
    def test_inverse_singular_matrix(self):
        """Test that singular matrix raises error"""
        singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        with pytest.raises(InvalidMatrixError, match="Matrix is singular and cannot be inverted"):
            self.mat.multiplicative_inverse(singular)
    
    def test_inverse_times_original_equals_identity(self):
        """Test that A * A^(-1) = I"""
        m = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
        inv = self.mat.multiplicative_inverse(m)
        result = self.mat.matrix_multiply(m, inv)
        
        # Check if result is approximately identity matrix
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        for i in range(3):
            for j in range(3):
                assert abs(result[i][j] - identity[i][j]) < 1e-10


class TestMatrixDivision:
    """Test matrix division"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_divide_by_identity(self):
        """Test dividing by identity matrix"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        result = self.mat.matrix_divide(m1, identity)
        assert result == m1
    
    def test_divide_by_singular_matrix(self):
        """Test dividing by singular matrix raises error"""
        m1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]
        with pytest.raises(InvalidMatrixError, match="Matrix is singular and cannot be inverted"):
            self.mat.matrix_divide(m1, singular)
    
    def test_divide_matrix_by_itself_times_scalar(self):
        """Test A / (A * k) = I / k (approximately)"""
        m = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
        m_times_2 = self.mat.scalar_multiply(m, 2)
        result = self.mat.matrix_divide(m, m_times_2)
        
        # Result should be approximately I/2
        expected = self.mat.scalar_multiply([[1, 0, 0], [0, 1, 0], [0, 0, 1]], 0.5)
        for i in range(3):
            for j in range(3):
                assert abs(result[i][j] - expected[i][j]) < 1e-10


class TestAdjoint:
    """Test adjoint/adjugate calculation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_adjoint_identity_matrix(self):
        """Test adjoint of identity matrix"""
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        result = self.mat.adjoint(identity)
        assert result == identity


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mat = Matrices3x3()
    
    def test_very_large_numbers(self):
        """Test operations with very large numbers"""
        m1 = [[1e10, 2e10, 3e10], [4e10, 5e10, 6e10], [7e10, 8e10, 9e10]]
        m2 = [[1e10, 0, 0], [0, 1e10, 0], [0, 0, 1e10]]
        result = self.mat.add(m1, m2)
        assert result[0][0] == 2e10
    
    def test_very_small_numbers(self):
        """Test operations with very small numbers"""
        m1 = [[1e-10, 2e-10, 3e-10], [4e-10, 5e-10, 6e-10], [7e-10, 8e-10, 9e-10]]
        m2 = [[1e-10, 0, 0], [0, 1e-10, 0], [0, 0, 1e-10]]
        result = self.mat.add(m1, m2)
        assert abs(result[0][0] - 2e-10) < 1e-20
    
    def test_mixed_int_and_float(self):
        """Test operations with mixed int and float values"""
        m1 = [[1, 2.5, 3], [4.0, 5, 6.5], [7, 8.5, 9]]
        m2 = [[1.0, 2, 3.5], [4, 5.5, 6], [7.5, 8, 9.0]]
        result = self.mat.add(m1, m2)
        assert result[0][0] == 2.0
        assert result[0][1] == 4.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
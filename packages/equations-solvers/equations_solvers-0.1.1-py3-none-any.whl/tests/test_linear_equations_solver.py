# """
# Pytest test suite for LinearEquationsSolver3x3 class.

# This module contains comprehensive tests for the linear equations solver,
# including unit tests, integration tests, and edge case validation.

# Test Categories:
#     - Parsing Tests: Validate equation string parsing
#     - Matrix Construction Tests: Test coefficient and RHS matrix creation
#     - Solution Tests: Verify Cramer's Rule and Matrix Inversion methods
#     - Edge Cases: Test error handling and special conditions
#     - Integration Tests: Compare both solution methods

# Run tests with:
#     pytest test_linear_equations_solver.py -v
#     pytest test_linear_equations_solver.py -v --cov=linear_equations_solver
# """

# import pytest
# from fractions import Fraction
# from linear_equations_solver import LinearEquationsSolver3x3
# from matrices3x3 import InvalidMatrixError


# class TestEquationParsing:
#     """Test suite for equation parsing functionality."""
    
#     def test_parse_simple_equation(self):
#         """Test parsing of simple equations with positive coefficients."""
#         solver = LinearEquationsSolver3x3("x+y+z=6")
#         variables, coefficients, rhs = solver.equs_data[0]
        
#         assert variables == ['x', 'y', 'z']
#         assert coefficients == ['+1', '+1', '+1']
#         assert rhs == '6'
    
#     def test_parse_equation_with_negative_coefficients(self):
#         """Test parsing equations with negative coefficients."""
#         solver = LinearEquationsSolver3x3("-2x+3y-4z=5")
#         variables, coefficients, rhs = solver.equs_data[0]
        
#         assert variables == ['x', 'y', 'z']
#         assert coefficients == ['-2', '+3', '-4']
#         assert rhs == '5'
    
#     def test_parse_equation_with_spaces(self):
#         """Test parsing equations with spaces (should be removed)."""
#         solver = LinearEquationsSolver3x3("2x + 3y - z = 10")
#         variables, coefficients, rhs = solver.equs_data[0]
        
#         assert variables == ['x', 'y', 'z']
#         assert coefficients == ['+2', '+3', '-1']
#         assert rhs == '10'
    
#     def test_parse_equation_implicit_one(self):
#         """Test parsing equations with implicit coefficient of 1."""
#         solver = LinearEquationsSolver3x3("x-y+z=0")
#         variables, coefficients, rhs = solver.equs_data[0]
        
#         assert coefficients == ['+1', '-1', '+1']
    
#     def test_parse_equation_explicit_coefficients(self):
#         """Test parsing equations with explicit multi-digit coefficients."""
#         solver = LinearEquationsSolver3x3("10x+20y+30z=100")
#         variables, coefficients, rhs = solver.equs_data[0]
        
#         assert coefficients == ['+10', '+20', '+30']
#         assert rhs == '100'
    
#     def test_parse_multiple_equations(self):
#         """Test parsing multiple equations from comma-separated string."""
#         equations = "x+y+z=6, 2x-y+z=3, x+2y-z=2"
#         solver = LinearEquationsSolver3x3(equations)
        
#         assert len(solver.equs_data) == 3
#         assert solver.equs_data[0][2] == '6'
#         assert solver.equs_data[1][2] == '3'
#         assert solver.equs_data[2][2] == '2'
    
#     def test_parse_different_variable_names(self):
#         """Test parsing with different variable names (not x, y, z)."""
#         solver = LinearEquationsSolver3x3("2a+3b+c=10")
#         variables, _, _ = solver.equs_data[0]
        
#         assert variables == ['a', 'b', 'c']


# class TestMatrixConstruction:
#     """Test suite for coefficient matrix and RHS vector construction."""
    
#     def test_coefficient_matrix_construction(self):
#         """Test construction of coefficient matrix A."""
#         solver = LinearEquationsSolver3x3(
#             "2x+3y-z=5, x-y+2z=3, 3x+y+z=8"
#         )
#         A = solver.A()
        
#         assert A == [[2, 3, -1], [1, -1, 2], [3, 1, 1]]
#         assert all(isinstance(val, int) for row in A for val in row)
    
#     def test_rhs_vector_construction(self):
#         """Test construction of RHS vector B."""
#         solver = LinearEquationsSolver3x3(
#             "2x+3y-z=5, x-y+2z=3, 3x+y+z=8"
#         )
#         B = solver._get_RHS_matrix()
        
#         assert B == [5, 3, 8]
#         assert all(isinstance(val, int) for val in B)
    
#     def test_coefficient_matrix_negative_values(self):
#         """Test coefficient matrix with negative values."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
#         A = solver.A()
        
#         assert A == [[-2, 3, -4], [-1, -5, 4], [2, -4, 1]]
    
#     def test_replaced_matrix_x_column(self):
#         """Test replacing x column with RHS values."""
#         solver = LinearEquationsSolver3x3(
#             "2x+3y-z=5, x-y+2z=3, 3x+y+z=8"
#         )
#         A = solver.A()
#         Ax = solver.replaced_matrix(A, 'x')
        
#         assert Ax == [[5, 3, -1], [3, -1, 2], [8, 1, 1]]
    
#     def test_replaced_matrix_y_column(self):
#         """Test replacing y column with RHS values."""
#         solver = LinearEquationsSolver3x3(
#             "2x+3y-z=5, x-y+2z=3, 3x+y+z=8"
#         )
#         A = solver.A()
#         Ay = solver.replaced_matrix(A, 'y')
        
#         assert Ay == [[2, 5, -1], [1, 3, 2], [3, 8, 1]]
    
#     def test_replaced_matrix_z_column(self):
#         """Test replacing z column with RHS values."""
#         solver = LinearEquationsSolver3x3(
#             "2x+3y-z=5, x-y+2z=3, 3x+y+z=8"
#         )
#         A = solver.A()
#         Az = solver.replaced_matrix(A, 'z')
        
#         assert Az == [[2, 3, 5], [1, -1, 3], [3, 1, 8]]
    
#     def test_replaced_matrix_invalid_variable(self):
#         """Test that invalid variable name raises ValueError."""
#         solver = LinearEquationsSolver3x3("x+y+z=1, x+y+z=2, x+y+z=3")
#         A = solver.A()
        
#         with pytest.raises(ValueError, match="Invalid variable"):
#             solver.replaced_matrix(A, 'w')


# class TestCramersRule:
#     """Test suite for Cramer's Rule solution method."""
    
#     def test_cramers_rule_integer_solutions(self):
#         """Test Cramer's Rule with integer solutions."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+2z=8, -x-2y+3z=1, 3x-7y+4z=10"
#         )
#         solution = solver.crammers_rule()
        
#         assert solution == [('x', '3'), ('y', '1'), ('z', '2')]
    
#     def test_cramers_rule_fractional_solutions(self):
#         """Test Cramer's Rule with fractional solutions."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
#         solution = solver.crammers_rule()
        
#         assert solution[0][0] == 'x'
#         assert solution[1][0] == 'y'
#         assert solution[2][0] == 'z'
        
#         # Verify fractions
#         assert Fraction(solution[0][1]) == Fraction(2, 17)
#         assert Fraction(solution[1][1]) == Fraction(-3, 17)
#         assert Fraction(solution[2][1]) == Fraction(-16, 17)
    
#     def test_cramers_rule_zero_solution(self):
#         """Test Cramer's Rule when one variable equals zero."""
#         solver = LinearEquationsSolver3x3(
#             "2x+2y+z=0, -2x+5y+2z=1, 8x+y+4z=-1"
#         )
#         solution = solver.crammers_rule()
        
#         # Check that z = 0
#         assert Fraction(solution[2][1]) == 0
    
#     def test_cramers_rule_singular_matrix(self):
#         """Test Cramer's Rule with singular matrix (det = 0)."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+z=1, 2x+2y+2z=2, 3x+3y+3z=3"
#         )
        
#         with pytest.raises(InvalidMatrixError, match="no unique solution"):
#             solver.crammers_rule()
    
#     def test_cramers_rule_different_variables(self):
#         """Test Cramer's Rule with variables a, b, c."""
#         solver = LinearEquationsSolver3x3(
#             "2a+3b+c=10, a-b+2c=3, 3a+2b-c=5"
#         )
#         solution = solver.crammers_rule()
        
#         assert solution[0][0] == 'a'
#         assert solution[1][0] == 'b'
#         assert solution[2][0] == 'c'


# class TestMatrixInversionMethod:
#     """Test suite for Matrix Inversion solution method."""
    
#     def test_inversion_method_integer_solutions(self):
#         """Test Matrix Inversion with integer solutions."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+2z=8, -x-2y+3z=1, 3x-7y+4z=10"
#         )
#         solution = solver.matrix_inversion_rule()
        
#         assert solution == [('x', '3'), ('y', '1'), ('z', '2')]
    
#     def test_inversion_method_fractional_solutions(self):
#         """Test Matrix Inversion with fractional solutions."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
#         solution = solver.matrix_inversion_rule()
        
#         # Verify fractions
#         assert Fraction(solution[0][1]) == Fraction(2, 17)
#         assert Fraction(solution[1][1]) == Fraction(-3, 17)
#         assert Fraction(solution[2][1]) == Fraction(-16, 17)
    
#     def test_inversion_method_zero_solution(self):
#         """Test Matrix Inversion when one variable equals zero."""
#         solver = LinearEquationsSolver3x3(
#             "2x+2y+z=0, -2x+5y+2z=1, 8x+y+4z=-1"
#         )
#         solution = solver.matrix_inversion_rule()
        
#         # Check that z = 0
#         assert Fraction(solution[2][1]) == 0
    
#     def test_inversion_method_singular_matrix(self):
#         """Test Matrix Inversion with singular matrix (det = 0)."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+z=1, 2x+2y+2z=2, 3x+3y+3z=3"
#         )
        
#         with pytest.raises(InvalidMatrixError, match="not invertible"):
#             solver.matrix_inversion_rule()
    
#     def test_inversion_method_floating_point_precision(self):
#         """Test that floating-point results are properly rounded."""
#         solver = LinearEquationsSolver3x3(
#             "2x-3y+5z=1, x+y+2z=3, 3x-2y-4z=0"
#         )
#         solution = solver.matrix_inversion_rule()
        
#         # Should return clean fractions, not floating point numbers
#         for var, value in solution:
#             assert '.' not in value or value == '0'


# class TestMethodComparison:
#     """Test suite comparing both solution methods."""
    
#     def test_methods_match_case1(self):
#         """Test that both methods produce identical results - Case 1."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+2z=8, -x-2y+3z=1, 3x-7y+4z=10"
#         )
        
#         cramer_solution = solver.crammers_rule()
#         inversion_solution = solver.matrix_inversion_rule()
        
#         assert cramer_solution == inversion_solution
    
#     def test_methods_match_case2(self):
#         """Test that both methods produce identical results - Case 2."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
        
#         cramer_solution = solver.crammers_rule()
#         inversion_solution = solver.matrix_inversion_rule()
        
#         assert cramer_solution == inversion_solution
    
#     def test_methods_match_case3(self):
#         """Test that both methods produce identical results - Case 3."""
#         solver = LinearEquationsSolver3x3(
#             "2x-3y+5z=1, x+y+2z=3, 3x-2y-4z=0"
#         )
        
#         cramer_solution = solver.crammers_rule()
#         inversion_solution = solver.matrix_inversion_rule()
        
#         assert cramer_solution == inversion_solution
    
#     def test_methods_match_case4(self):
#         """Test that both methods produce identical results - Case 4."""
#         solver = LinearEquationsSolver3x3(
#             "2x+2y+z=0, -2x+5y+2z=1, 8x+y+4z=-1"
#         )
        
#         cramer_solution = solver.crammers_rule()
#         inversion_solution = solver.matrix_inversion_rule()
        
#         assert cramer_solution == inversion_solution
    
#     @pytest.mark.parametrize("equations", [
#         "x+y+z=6, 2x-y+z=3, x+2y-z=2",
#         "2x+3y+z=11, x+y+z=6, 3x+2y+z=11",
#         "x+2y+z=7, 2x+y+2z=10, x+y+3z=11",
#     ])
#     def test_methods_match_parametrized(self, equations):
#         """Parametrized test comparing both methods."""
#         solver = LinearEquationsSolver3x3(equations)
        
#         cramer_solution = solver.crammers_rule()
#         inversion_solution = solver.matrix_inversion_rule()
        
#         # Both methods should match
#         assert cramer_solution == inversion_solution
        
#         # Verify we got 3 solutions
#         assert len(cramer_solution) == 3
        
#         # Verify all solutions are fractions/integers (strings)
#         assert all(isinstance(sol[1], str) for sol in cramer_solution)


# class TestEdgeCases:
#     """Test suite for edge cases and special conditions."""
    
#     def test_all_positive_coefficients(self):
#         """Test system with all positive coefficients."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+z=6, 2x+y+z=5, x+2y+z=5"
#         )
#         solution = solver.crammers_rule()
        
#         assert len(solution) == 3
#         assert all(isinstance(sol[1], str) for sol in solution)
    
#     def test_all_negative_coefficients(self):
#         """Test system with all negative coefficients."""
#         solver = LinearEquationsSolver3x3(
#             "-x-y-z=-6, -2x-y-z=-5, -x-2y-z=-5"
#         )
#         solution = solver.crammers_rule()
        
#         # Should give valid solution
#         assert len(solution) == 3
#         assert all(isinstance(sol[1], str) for sol in solution)
    
#     def test_large_coefficients(self):
#         """Test system with large coefficient values."""
#         solver = LinearEquationsSolver3x3(
#             "100x+200y+300z=1400, 200x+300y+100z=1300, 300x+100y+200z=1200"
#         )
#         solution = solver.crammers_rule()
        
#         # Should still produce valid solution
#         assert len(solution) == 3
#         assert all(isinstance(sol[1], str) for sol in solution)
    
#     def test_zero_rhs_values(self):
#         """Test system with zero on RHS."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+z=0, x-y+z=0, x+y-z=2"
#         )
#         solution = solver.crammers_rule()
        
#         assert Fraction(solution[0][1]) == 1
#         assert Fraction(solution[1][1]) == 0
#         assert Fraction(solution[2][1]) == -1
    
#     def test_identity_like_system(self):
#         """Test system with diagonal-dominant matrix."""
#         solver = LinearEquationsSolver3x3(
#             "5x+y+z=10, x+5y+z=15, x+y+5z=20"
#         )
#         solution = solver.crammers_rule()
        
#         assert len(solution) == 3
#         assert all(isinstance(sol[1], str) for sol in solution)


# class TestInputValidation:
#     """Test suite for input validation and error handling."""
    
#     def test_invalid_equation_format_no_equals(self):
#         """Test that equation without equals sign is handled."""
#         with pytest.raises((ValueError, IndexError)):
#             solver = LinearEquationsSolver3x3("x+y+z")
    
#     def test_empty_equations_string(self):
#         """Test handling of empty equation string."""
#         with pytest.raises((ValueError, IndexError)):
#             solver = LinearEquationsSolver3x3("")
    
#     def test_inconsistent_variable_count(self):
#         """Test equations with inconsistent variable counts."""
#         # This should still parse, but may fail during solution
#         solver = LinearEquationsSolver3x3("x+y=5, x+y+z=10, x=1")
#         # The behavior depends on implementation


# class TestFractionOutput:
#     """Test suite for fraction output formatting."""
    
#     def test_integer_as_fraction(self):
#         """Test that integer results are formatted without denominator."""
#         solver = LinearEquationsSolver3x3(
#             "x+y+2z=8, -x-2y+3z=1, 3x-7y+4z=10"
#         )
#         solution = solver.crammers_rule()
        
#         # 3, 1, 2 should be displayed as '3', '1', '2' not '3/1', '1/1', '2/1'
#         assert solution[0][1] == '3'
#         assert solution[1][1] == '1'
#         assert solution[2][1] == '2'
    
#     def test_proper_fraction_format(self):
#         """Test that proper fractions are formatted correctly."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
#         solution = solver.crammers_rule()
        
#         # Should be in form 'numerator/denominator'
#         assert '/' in solution[0][1]
#         assert '/' in solution[1][1]
#         assert '/' in solution[2][1]
    
#     def test_negative_fraction_format(self):
#         """Test that negative fractions are formatted correctly."""
#         solver = LinearEquationsSolver3x3(
#             "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#         )
#         solution = solver.crammers_rule()
        
#         # y should be negative: -3/17
#         assert solution[1][1].startswith('-')


# # Pytest fixtures
# @pytest.fixture
# def simple_solver():
#     """Fixture providing a simple solver instance."""
#     return LinearEquationsSolver3x3("x+y+z=6, 2x-y+z=3, x+2y-z=2")


# @pytest.fixture
# def fractional_solver():
#     """Fixture providing a solver with fractional solutions."""
#     return LinearEquationsSolver3x3(
#         "-2x+3y-4z=3, -x-5y+4z=-3, 2x-4y+z=0"
#     )


# def test_with_simple_fixture(simple_solver):
#     """Test using the simple solver fixture."""
#     solution = simple_solver.crammers_rule()
#     assert solution[0][1] == '1'
#     assert solution[1][1] == '2'
#     assert solution[2][1] == '3'


# def test_with_fractional_fixture(fractional_solver):
#     """Test using the fractional solver fixture."""
#     solution = fractional_solver.matrix_inversion_rule()
#     assert len(solution) == 3
#     assert all(isinstance(sol[1], str) for sol in solution)


# if __name__ == "__main__":
#     pytest.main([__file__, "-v", "--tb=short"])



"""
Test Suite for Linear Equations Solver

Run with: pytest test_linear_equations_solver.py -v
For coverage: pytest test_linear_equations_solver.py --cov=linear_equations_solver
"""

"""
Test Suite for Linear Equations Solver

Run with: pytest test_linear_equations_solver.py -v
For coverage: pytest test_linear_equations_solver.py --cov=linear_equations_solver
"""

import pytest
from fractions import Fraction
from linear_equations_solver import (
    LinearEquationsSolver,
    ParseError,
    ValidationError,
    LinearEquationsSolverError
)
from matrices3x3 import InvalidMatrixError


class TestLinearEquationsSolverInit:
    """Test suite for initialization and basic setup."""
    
    def test_valid_2x2_system(self):
        """Test initialization with valid 2x2 system."""
        solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
        assert solver.m2x2 is True
        assert solver.m3x3 is False
        assert len(solver.equs_data) == 2
    
    def test_valid_3x3_system(self):
        """Test initialization with valid 3x3 system."""
        solver = LinearEquationsSolver(
            "3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0"
        )
        assert solver.m3x3 is True
        assert solver.m2x2 is False
        assert len(solver.equs_data) == 3
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises ParseError."""
        with pytest.raises(ParseError, match="cannot be empty"):
            LinearEquationsSolver("")
    
    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises ParseError."""
        with pytest.raises(ParseError, match="cannot be empty"):
            LinearEquationsSolver("   ")
    
    def test_single_equation_raises_error(self):
        """Test that single equation raises ValueError."""
        with pytest.raises(ValueError, match="Only 2x2 and 3x3 systems"):
            LinearEquationsSolver("x + y = 5")
    
    def test_four_equations_raises_error(self):
        """Test that 4 equations raises ValueError."""
        with pytest.raises(ValueError, match="Only 2x2 and 3x3 systems"):
            LinearEquationsSolver("x=1, y=2, z=3, w=4")


class TestEquationParsing:
    """Test suite for equation parsing."""
    
    def test_simple_2x2_parsing(self):
        """Test parsing of simple 2x2 system."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        assert solver.A() == [[1, 1], [1, -1]]
        assert solver._get_RHS_matrix() == [5, 1]
    
    def test_coefficients_with_numbers(self):
        """Test parsing with numeric coefficients."""
        solver = LinearEquationsSolver("2x + 3y = 10, 4x - 5y = 2")
        assert solver.A() == [[2, 3], [4, -5]]
        assert solver._get_RHS_matrix() == [10, 2]
    
    def test_negative_leading_term(self):
        """Test parsing with negative leading term."""
        solver = LinearEquationsSolver("-x + y = 3, x - y = 1")
        assert solver.A() == [[-1, 1], [1, -1]]
    
    def test_negative_rhs(self):
        """Test parsing with negative right-hand side."""
        solver = LinearEquationsSolver("x + y = -5, x - y = -1")
        assert solver._get_RHS_matrix() == [-5, -1]
    
    def test_spaces_are_ignored(self):
        """Test that spaces in equations are properly handled."""
        solver1 = LinearEquationsSolver("x+y=5,x-y=1")
        solver2 = LinearEquationsSolver("x + y = 5, x - y = 1")
        assert solver1.A() == solver2.A()
    
    def test_decimal_coefficients(self):
        """Test parsing with decimal coefficients."""
        solver = LinearEquationsSolver("1.5x + 2.5y = 10, 3.0x - 1.5y = 5")
        assert solver.A() == [[1.5, 2.5], [3.0, -1.5]]
    
    def test_3x3_with_all_variables(self):
        """Test parsing 3x3 system."""
        solver = LinearEquationsSolver("x + y + z = 6, 2x - y + z = 3, x + 2y - z = 2")
        assert solver.A() == [[1, 1, 1], [2, -1, 1], [1, 2, -1]]
        assert solver._get_RHS_matrix() == [6, 3, 2]
    
    def test_missing_equals_raises_error(self):
        """Test that equation without '=' raises ParseError."""
        with pytest.raises(ParseError, match="must contain '='"):
            LinearEquationsSolver("x + y, x - y = 1")
    
    def test_multiple_equals_raises_error(self):
        """Test that equation with multiple '=' raises ParseError."""
        with pytest.raises(ParseError, match="exactly one '='"):
            LinearEquationsSolver("x + y = 5 = 3, x - y = 1")
    
    def test_no_variables_raises_error(self):
        """Test that equation without variables raises ParseError."""
        with pytest.raises(ParseError, match="No variables found"):
            LinearEquationsSolver("2 + 3 = 5, 1 - 1 = 0")
    
    def test_invalid_rhs_raises_error(self):
        """Test that non-numeric RHS raises ParseError."""
        with pytest.raises(ParseError, match="must be a number"):
            LinearEquationsSolver("x + y = abc, x - y = 1")


class TestValidation:
    """Test suite for system validation."""
    
    def test_inconsistent_variables_raises_error(self):
        """Test that inconsistent variables raise ValidationError."""
        with pytest.raises(ValidationError, match="inconsistent variables"):
            LinearEquationsSolver("x + y = 5, x + z = 3")
    
    def test_different_variable_order_raises_error(self):
        """Test that different variable ordering raises ValidationError."""
        with pytest.raises(ValidationError, match="inconsistent variables"):
            LinearEquationsSolver("x + y = 5, y + x = 3")
    
    def test_validation_can_be_disabled(self):
        """Test that validation can be skipped."""
        # This should not raise an error with validate=False
        solver = LinearEquationsSolver("x + y = 5, x + z = 3", validate=False)
        assert solver is not None


class TestCoefficientMatrix:
    """Test suite for coefficient matrix operations."""
    
    def test_coefficient_matrix_2x2(self):
        """Test coefficient matrix extraction for 2x2."""
        solver = LinearEquationsSolver("2x + 3y = 5, 4x - y = 2")
        A = solver.A()
        assert A == [[2, 3], [4, -1]]
    
    def test_coefficient_matrix_3x3(self):
        """Test coefficient matrix extraction for 3x3."""
        solver = LinearEquationsSolver("x + 2y + 3z = 6, 4x + 5y + 6z = 15, 7x + 8y + 9z = 24")
        A = solver.A()
        assert A == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    
    def test_rhs_matrix_extraction(self):
        """Test RHS values extraction."""
        solver = LinearEquationsSolver("x + y = 10, x - y = 2")
        rhs = solver._get_RHS_matrix()
        assert rhs == [10, 2]


class TestReplacedMatrix:
    """Test suite for replaced matrix (Cramer's rule)."""
    
    def test_replace_first_column_2x2(self):
        """Test replacing first column for 2x2 system."""
        solver = LinearEquationsSolver("2x + 3y = 5, 4x - y = 2")
        A = solver.A()
        replaced = solver.replaced_matrix(A, 'x')
        assert replaced == [[5, 3], [2, -1]]
    
    def test_replace_second_column_2x2(self):
        """Test replacing second column for 2x2 system."""
        solver = LinearEquationsSolver("2x + 3y = 5, 4x - y = 2")
        A = solver.A()
        replaced = solver.replaced_matrix(A, 'y')
        assert replaced == [[2, 5], [4, 2]]
    
    def test_replace_column_3x3(self):
        """Test replacing columns for 3x3 system."""
        solver = LinearEquationsSolver("x + y + z = 6, 2x - y + z = 3, x + 2y - z = 2")
        A = solver.A()
        
        replaced_x = solver.replaced_matrix(A, 'x')
        assert replaced_x == [[6, 1, 1], [3, -1, 1], [2, 2, -1]]
        
        replaced_y = solver.replaced_matrix(A, 'y')
        assert replaced_y == [[1, 6, 1], [2, 3, 1], [1, 2, -1]]
        
        replaced_z = solver.replaced_matrix(A, 'z')
        assert replaced_z == [[1, 1, 6], [2, -1, 3], [1, 2, 2]]
    
    def test_invalid_variable_raises_error(self):
        """Test that invalid variable raises ValueError."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        A = solver.A()
        with pytest.raises(ValueError, match="Invalid variable"):
            solver.replaced_matrix(A, 'z')


class TestCramersRule:
    """Test suite for Cramer's rule solution method."""
    
    def test_simple_2x2_solution(self):
        """Test Cramer's rule for simple 2x2 system."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.crammers_rule()
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_2x2_with_fractions(self):
        """Test Cramer's rule returning fractions."""
        solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
        solution = solver.crammers_rule()
        # Expected: x = 11/18, y = 17/18
        assert len(solution) == 2
        assert solution[0][0] == 'x'
        assert solution[1][0] == 'y'
        # Verify the fractions
        x_val = Fraction(solution[0][1])
        y_val = Fraction(solution[1][1])
        assert x_val == Fraction(11, 18)
        assert y_val == Fraction(17, 18)
    
    def test_3x3_solution(self):
        """Test Cramer's rule for 3x3 system."""
        solver = LinearEquationsSolver("x + y + z = 6, 2x - y + z = 3, x + 2y - z = 2")
        solution = solver.crammers_rule()
        assert len(solution) == 3
        # Verify solution satisfies equations (approximately)
        x = float(Fraction(solution[0][1]))
        y = float(Fraction(solution[1][1]))
        z = float(Fraction(solution[2][1]))
        assert abs(x + y + z - 6) < 0.001
        assert abs(2*x - y + z - 3) < 0.001
        assert abs(x + 2*y - z - 2) < 0.001
    
    def test_singular_matrix_raises_error(self):
        """Test that singular matrix raises InvalidMatrixError."""
        # Dependent equations: second is 2x the first
        solver = LinearEquationsSolver("x + y = 2, 2x + 2y = 4")
        with pytest.raises(InvalidMatrixError, match="no unique solution"):
            solver.crammers_rule()


class TestMatrixInversion:
    """Test suite for matrix inversion solution method."""
    
    def test_simple_2x2_inversion(self):
        """Test matrix inversion for simple 2x2 system."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.matrix_inversion_rule()
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_2x2_inversion_with_fractions(self):
        """Test matrix inversion returning fractions."""
        solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
        solution = solver.matrix_inversion_rule()
        x_val = Fraction(solution[0][1])
        y_val = Fraction(solution[1][1])
        assert x_val == Fraction(11, 18)
        assert y_val == Fraction(17, 18)
    
    def test_3x3_inversion(self):
        """Test matrix inversion for 3x3 system."""
        solver = LinearEquationsSolver("x + y + z = 6, 2x - y + z = 3, x + 2y - z = 2")
        solution = solver.matrix_inversion_rule()
        assert len(solution) == 3
        # Verify solution
        x = float(Fraction(solution[0][1]))
        y = float(Fraction(solution[1][1]))
        z = float(Fraction(solution[2][1]))
        assert abs(x + y + z - 6) < 0.001
    
    def test_singular_matrix_inversion_raises_error(self):
        """Test that singular matrix raises InvalidMatrixError."""
        solver = LinearEquationsSolver("x + y = 2, 2x + 2y = 4")
        with pytest.raises(InvalidMatrixError, match="not invertible"):
            solver.matrix_inversion_rule()


class TestSolveMethod:
    """Test suite for the unified solve() method."""
    
    def test_solve_default_uses_cramer(self):
        """Test that solve() defaults to Cramer's rule."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.solve()
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_solve_with_cramer_method(self):
        """Test solve() with explicit 'cramer' method."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.solve('cramer')
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_solve_with_inverse_method(self):
        """Test solve() with 'inverse' method."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.solve('inverse')
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_solve_with_inversion_alias(self):
        """Test solve() with 'inversion' alias."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        solution = solver.solve('inversion')
        assert solution == [('x', '3'), ('y', '2')]
    
    def test_solve_case_insensitive(self):
        """Test that solve() method is case-insensitive."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        sol1 = solver.solve('CRAMER')
        sol2 = solver.solve('Inverse')
        assert sol1 == [('x', '3'), ('y', '2')]
        assert sol2 == [('x', '3'), ('y', '2')]
    
    def test_solve_invalid_method_raises_error(self):
        """Test that invalid method raises ValueError."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        with pytest.raises(ValueError, match="Unknown method"):
            solver.solve('gaussian')
    
    def test_both_methods_give_same_result(self):
        """Test that both solution methods give identical results."""
        solver = LinearEquationsSolver("2x + 3y = 13, 5x - 2y = 4")
        cramer_sol = solver.solve('cramer')
        inverse_sol = solver.solve('inverse')
        
        # Compare the fraction values
        for i in range(len(cramer_sol)):
            cramer_frac = Fraction(cramer_sol[i][1])
            inverse_frac = Fraction(inverse_sol[i][1])
            assert cramer_frac == inverse_frac


class TestHelperMethods:
    """Test suite for helper methods."""
    
    def test_get_variables_2x2(self):
        """Test get_variables() for 2x2 system."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        assert solver.get_variables() == ['x', 'y']
    
    def test_get_variables_3x3(self):
        """Test get_variables() for 3x3 system."""
        solver = LinearEquationsSolver("a + b + c = 6, a - b + c = 1, a + b - c = 2")
        assert solver.get_variables() == ['a', 'b', 'c']
    
    def test_str_representation(self):
        """Test __str__ method."""
        solver = LinearEquationsSolver("x + y = 5, x - y = 1")
        str_repr = str(solver)
        assert "2x2" in str_repr
        assert "['x', 'y']" in str_repr
    
    def test_repr_representation(self):
        """Test __repr__ method."""
        equations = "x + y = 5, x - y = 1"
        solver = LinearEquationsSolver(equations)
        repr_str = repr(solver)
        assert "LinearEquationsSolver" in repr_str
        assert equations in repr_str


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""
    
    def test_zero_coefficient(self):
        """Test system where a coefficient is zero (variable missing)."""
        # Note: This requires the parser to handle missing variables
        # Current implementation may need adjustment for this
        pass
    
    def test_negative_solution(self):
        """Test system with negative solutions."""
        solver = LinearEquationsSolver("x + y = 0, x - y = 4")
        solution = solver.solve()
        assert solution == [('x', '2'), ('y', '-2')]
    
    def test_large_coefficients(self):
        """Test system with large coefficients."""
        solver = LinearEquationsSolver("1000x + 2000y = 5000, 3000x - 4000y = 1000")
        solution = solver.solve()
        # Just verify it completes without error
        assert len(solution) == 2
    
    def test_decimal_solutions(self):
        """Test system yielding decimal/fractional solutions."""
        solver = LinearEquationsSolver("3x + 2y = 10, x + y = 4")
        solution = solver.solve()
        x_val = float(Fraction(solution[0][1]))
        y_val = float(Fraction(solution[1][1]))
        # Verify: 3x + 2y = 10
        assert abs(3*x_val + 2*y_val - 10) < 0.001
        # Verify: x + y = 4
        assert abs(x_val + y_val - 4) < 0.001


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_complete_workflow_2x2(self):
        """Test complete workflow for 2x2 system."""
        equations = "2x + 3y = 13, 5x - 2y = 4"
        solver = LinearEquationsSolver(equations)
        
        # Check initialization
        assert solver.m2x2
        assert len(solver.get_variables()) == 2
        
        # Check matrix extraction
        A = solver.A()
        assert len(A) == 2
        assert len(A[0]) == 2
        
        # Solve and verify
        solution = solver.solve()
        x = float(Fraction(solution[0][1]))
        y = float(Fraction(solution[1][1]))
        
        # Verify equations are satisfied
        assert abs(2*x + 3*y - 13) < 0.001
        assert abs(5*x - 2*y - 4) < 0.001
    
    def test_complete_workflow_3x3(self):
        """Test complete workflow for 3x3 system."""
        equations = "2x + y - z = 8, -3x - y + 2z = -11, -2x + y + 2z = -3"
        solver = LinearEquationsSolver(equations)
        
        # Check initialization
        assert solver.m3x3
        assert len(solver.get_variables()) == 3
        
        # Solve with both methods
        cramer_sol = solver.solve('cramer')
        inverse_sol = solver.solve('inverse')
        
        # Both should give same result
        for i in range(3):
            assert Fraction(cramer_sol[i][1]) == Fraction(inverse_sol[i][1])


# Pytest fixtures
@pytest.fixture
def simple_2x2_solver():
    """Fixture providing a simple 2x2 solver."""
    return LinearEquationsSolver("x + y = 5, x - y = 1")


@pytest.fixture
def simple_3x3_solver():
    """Fixture providing a simple 3x3 solver."""
    return LinearEquationsSolver("x + y + z = 6, 2x - y + z = 3, x + 2y - z = 2")


class TestWithFixtures:
    """Tests using pytest fixtures."""
    
    def test_fixture_2x2(self, simple_2x2_solver):
        """Test using 2x2 fixture."""
        solution = simple_2x2_solver.solve()
        assert len(solution) == 2
        assert solution[0][1] == '3'
        assert solution[1][1] == '2'
    
    def test_fixture_3x3(self, simple_3x3_solver):
        """Test using 3x3 fixture."""
        solution = simple_3x3_solver.solve()
        assert len(solution) == 3


# Parametrized tests
@pytest.mark.parametrize("equations,expected_x,expected_y", [
    ("x + y = 5, x - y = 1", "3", "2"),
    ("2x + 3y = 13, 5x - 2y = 4", "2", "3"),
    ("x + 2y = 8, 3x - y = 5", "18/7", "19/7"),  # Corrected: x=18/7, y=19/7
])
def test_various_2x2_systems(equations, expected_x, expected_y):
    """Parametrized test for various 2x2 systems."""
    solver = LinearEquationsSolver(equations)
    solution = solver.solve()
    assert solution[0][1] == expected_x
    assert solution[1][1] == expected_y


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
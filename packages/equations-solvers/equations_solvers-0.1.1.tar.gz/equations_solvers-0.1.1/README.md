# Equations Solvers

A comprehensive Python package for matrix operations and solving linear equations. This package provides easy-to-use classes for working with 2x2 and 3x3 matrices, along with a powerful linear equation solver.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE.txt)

## Features

✨ **Matrix Operations**
- Addition and Subtraction
- Matrix and Scalar Multiplication
- Matrix and Scalar Division
- Determinant Calculation
- Adjoint Matrix
- Multiplicative Inverse

🔢 **Linear Equation Solver**
- Solve 2x2 and 3x3 systems
- Multiple solving methods (Cramer's Rule, Matrix Inversion)
- Parse equations from string format
- Fraction results for exact solutions

🛡️ **Robust Error Handling**
- Invalid matrix detection
- Singular matrix handling
- Division by zero protection
- Equation parsing validation

## Installation

```bash
pip install equations_solvers
```

For development installation:
```bash
git clone https://github.com/yourusername/equations_solvers.git
cd equations_solvers
pip install -e .
```

## Quick Start

```python
from equations_solvers import Matrices2x2, LinearEquationsSolver

# Create a 2x2 matrix calculator
calc = Matrices2x2()

# Define matrices
A = [[2, 3], [1, 4]]
B = [[5, 2], [3, 1]]

# Perform operations
result = calc.add(A, B)
print(result)  # [[7.0, 5.0], [4.0, 5.0]]

# Solve linear equations
solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
solution = solver.solve('cramer')
for var, val in solution:
    print(f"{var} = {val}")
# Output: x = 11/18, y = 17/18
```

## Documentation

### Table of Contents
1. [2x2 Matrix Operations](#2x2-matrix-operations)
2. [3x3 Matrix Operations](#3x3-matrix-operations)
3. [Linear Equation Solver](#linear-equation-solver)
4. [Error Handling](#error-handling)

---

## 2x2 Matrix Operations

The `Matrices2x2` class provides comprehensive operations for 2x2 matrices.

### Basic Usage

```python
from equations_solvers import Matrices2x2

# Create an instance
calc = Matrices2x2()

# Define matrices
A = [[2, 3], [1, 4]]
B = [[5, 2], [3, 1]]
```

### Addition

```python
result = calc.add(A, B)
print(result)
```

**Output:**
```
[[7.0, 5.0], [4.0, 5.0]]
```

### Subtraction

```python
result = calc.subtract(A, B)
print(result)
```

**Output:**
```
[[-3.0, 1.0], [-2.0, 3.0]]
```

### Matrix Multiplication

```python
result = calc.multiply(A, B)
print(result)
```

**Output:**
```
[[19, 7], [17, 6]]
```

### Scalar Multiplication

```python
result = calc.multiply(A, num=2)
print(result)
```

**Output:**
```
[[4, 6], [2, 8]]
```

### Scalar Division

```python
result = calc.divide(A, num=2)
print(result)
```

**Output:**
```
[[1.0, 1.5], [0.5, 2.0]]
```

### Determinant

```python
det = calc.determinant(A)
print(det)
```

**Output:**
```
5.0
```

### Adjoint Matrix

```python
adj = calc.adjoint(A)
print(adj)
```

**Output:**
```
[[4.0, -3.0], [-1.0, 2.0]]
```

### Multiplicative Inverse

```python
inv = calc.multiplicative_inverse(A)
print(inv)
```

**Output:**
```
[[0.8, -0.6], [-0.2, 0.4]]
```

---

## 3x3 Matrix Operations

The `Matrices3x3` class provides comprehensive operations for 3x3 matrices.

### Basic Usage

```python
from equations_solvers import Matrices3x3

# Create an instance
calc = Matrices3x3()

# Define matrices
C = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
D = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # Identity matrix
```

### Addition

```python
result = calc.add(C, D)
print(result)
```

**Output:**
```
[[2.0, 2.0, 3.0], [0.0, 2.0, 4.0], [5.0, 6.0, 1.0]]
```

### Subtraction

```python
result = calc.subtract(C, D)
print(result)
```

**Output:**
```
[[0.0, 2.0, 3.0], [0.0, 0.0, 4.0], [5.0, 6.0, -1.0]]
```

### Matrix Multiplication

```python
result = calc.matrix_multiply(C, D)
print(result)
```

**Output:**
```
[[1, 2, 3], [0, 1, 4], [5, 6, 0]]
```

### Scalar Multiplication

```python
result = calc.scalar_multiply(C, 3)
print(result)
```

**Output:**
```
[[3, 6, 9], [0, 3, 12], [15, 18, 0]]
```

### Scalar Division

```python
result = calc.scalar_divide(C, 3)
print(result)
```

**Output:**
```
[[0.333, 0.667, 1.0], [0.0, 0.333, 1.333], [1.667, 2.0, 0.0]]
```

### Determinant

```python
det = calc.determinant(C)
print(det)
```

**Output:**
```
1.0
```

### Adjoint Matrix

```python
adj = calc.adjoint(C)
print(adj)
```

**Output:**
```
[[-24.0, 18.0, 5.0], [20.0, -15.0, -4.0], [-5.0, 4.0, 1.0]]
```

### Multiplicative Inverse

```python
inv = calc.multiplicative_inverse(C)
print(inv)
```

**Output:**
```
[[-24.0, 18.0, 5.0], [20.0, -15.0, -4.0], [-5.0, 4.0, 1.0]]
```

### Matrix Division

```python
result = calc.matrix_divide(C, D)
print(result)
```

**Output:**
```
[[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
```

---

## Linear Equation Solver

The `LinearEquationsSolver` class solves systems of 2x2 and 3x3 linear equations.

### Solving 2x2 Systems

```python
from equations_solvers import LinearEquationsSolver

# Define the system of equations
solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")

# Get coefficient matrix
print("Coefficient Matrix:")
for row in solver.A():
    print(row)
```

**Output:**
```
Coefficient Matrix:
[2.0, 4.0]
[3.0, -3.0]
```

#### Using Cramer's Rule

```python
solution = solver.solve('cramer')
for var, val in solution:
    print(f"{var} = {val}")
```

**Output:**
```
x = 11/18
y = 17/18
```

#### Using Matrix Inversion

```python
solution = solver.solve('inverse')
for var, val in solution:
    print(f"{var} = {val}")
```

**Output:**
```
x = 11/18
y = 17/18
```

### Solving 3x3 Systems

```python
# Define a 3x3 system
solver = LinearEquationsSolver("3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0")

# Solve using Cramer's rule
solution = solver.solve('cramer')
for var, val in solution:
    print(f"{var} = {val}")
```

**Output:**
```
x = 8/5
y = 16/5
z = -2
```

### Complete Example with Verification

```python
# System: 2x + 3y = 8, x + 4y = 10
solver = LinearEquationsSolver("2x + 3y = 8, x + 4y = 10")

# Solve
solution = solver.solve('cramer')
x_val = float(solution[0][1])
y_val = float(solution[1][1])

print(f"Solution: x = {solution[0][1]}, y = {solution[1][1]}")

# Verify
eq1 = 2 * x_val + 3 * y_val
eq2 = x_val + 4 * y_val

print(f"\nVerification:")
print(f"2x + 3y = {eq1} (should be 8)")
print(f"x + 4y = {eq2} (should be 10)")
```

**Output:**
```
Solution: x = 2/5, y = 12/5

Verification:
2x + 3y = 8.0 (should be 8)
x + 4y = 10.0 (should be 10)
```

---

## Error Handling

The package includes robust error handling for common issues.

### Singular Matrix (Non-Invertible)

```python
from equations_solvers import Matrices3x3, InvalidMatrixError

calc = Matrices3x3()
singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

try:
    inv = calc.multiplicative_inverse(singular)
except InvalidMatrixError as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Matrix is singular and cannot be inverted.
```

### Division by Zero

```python
from equations_solvers import Matrices2x2, InvalidMatrixError

calc = Matrices2x2()
A = [[2, 3], [1, 4]]

try:
    result = calc.divide(A, num=0)
except InvalidMatrixError as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Division by zero is not allowed.
```

### Invalid Equation Format

```python
from equations_solvers import LinearEquationsSolver

try:
    # Missing equals sign
    solver = LinearEquationsSolver("2x + 3y")
except Exception as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Equation must contain '=': 2x+3y
```

### Inconsistent Variables

```python
try:
    # Variables don't match across equations
    solver = LinearEquationsSolver("x + y = 1, x + z = 2")
except Exception as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Equation 2 has inconsistent variables. Expected ['x', 'y'], got ['x', 'z']
```

---

## API Reference

### Matrices2x2

**Methods:**
- `add(matrix1, matrix2)` - Add two matrices
- `subtract(matrix1, matrix2)` - Subtract matrix2 from matrix1
- `multiply(matrix1, matrix2=None, num=None)` - Multiply matrices or by scalar
- `divide(matrix, matrix2=None, num=None)` - Divide matrix by scalar or another matrix
- `determinant(matrix)` - Calculate determinant
- `adjoint(matrix)` - Calculate adjoint matrix
- `multiplicative_inverse(matrix)` - Calculate inverse matrix

### Matrices3x3

**Methods:**
- `add(matrix1, matrix2)` - Add two matrices
- `subtract(matrix1, matrix2)` - Subtract matrix2 from matrix1
- `matrix_multiply(matrix1, matrix2)` - Multiply two matrices
- `scalar_multiply(matrix, scalar)` - Multiply matrix by scalar
- `matrix_divide(matrix1, matrix2)` - Divide matrix1 by matrix2
- `scalar_divide(matrix, scalar)` - Divide matrix by scalar
- `determinant(matrix)` - Calculate determinant
- `adjoint(matrix)` - Calculate adjoint matrix
- `multiplicative_inverse(matrix)` - Calculate inverse matrix

### LinearEquationsSolver

**Constructor:**
- `LinearEquationsSolver(equations_str)` - Parse equations from string

**Methods:**
- `A()` - Get coefficient matrix
- `solve(method='cramer')` - Solve system using 'cramer' or 'inverse' method

**Returns:** List of tuples `[(variable, value), ...]`

### InvalidMatrixError

Custom exception raised for matrix-related errors.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

---

## Author

**Your Name**
- GitHub: [@Hammail-Riaz](https://github.com/Hammail-Riaz)
- Email: hammailriaz.dev@gmail.com

---

## Changelog

### Version 0.1.0 (Initial Release)
- 2x2 and 3x3 matrix operations
- Linear equation solver with multiple methods
- Comprehensive error handling
- Full documentation and examples

---

## Acknowledgments

- Built with Python 3.8+
- Inspired by linear algebra education needs
- Thanks to all contributors

---

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub Issues](https://github.com/yourusername/equations_solvers/issues)
- Check the [documentation](#documentation)
- Contact: hammailriaz.dev@gmail.com

---

**Made with ❤️ for mathematics and Python enthusiasts**
# 🧮 pyeqsolver 

### A comprehensive Python package for matrix operations and solving linear equations

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/pyeqsolver.svg)](https://pypi.org/project/pyeqsolver/)

**[Features](#-features) • [Installation](#️-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)**

---

## ✨ Features

### 🧮 Matrix Operations
- ➕ Addition and subtraction  
- ✖️ Matrix and scalar multiplication  
- ➗ Scalar division  
- 🔢 Determinant calculation  
- 🔄 Adjoint and inverse matrix computation  
- ➗ Matrix division (via inverse multiplication)

### 🔢 Linear Equation Solver
- 📐 Solve 2×2 and 3×3 systems  
- 🎯 **Cramer's Rule** and **Matrix Inversion** methods  
- 📝 Parse equations from strings  
- 🎲 Returns exact fractions for solutions  

### 🛡️ Robust Error Handling
- ❌ Singular matrices detection  
- 🚫 Division by zero protection  
- ⚠️ Equation parsing validation  
- 📏 Variable consistency checking

---

## ⚙️ Installation

### Quick Install

```bash
pip install pyeqsolver
```

### Development Installation

```bash
git clone https://github.com/Hammail-Riaz/pyeqsolver.git
cd pyeqsolver
pip install -e .
```

---

## 🚀 Quick Start

```python
from pyeqsolver import Matrices2x2, LinearEquationsSolver

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
# Output:
# x = 11/18
# y = 17/18
```

---

## 📘 Documentation

### Table of Contents

1. [2×2 Matrix Operations](#-2x2-matrix-operations)
2. [3×3 Matrix Operations](#-3x3-matrix-operations)
3. [Linear Equation Solver](#-linear-equation-solver)
4. [Error Handling](#️-error-handling)
5. [API Reference](#-api-reference)

---

### 🧩 2×2 Matrix Operations

```python
from pyeqsolver import Matrices2x2

calc = Matrices2x2()
A = [[2, 3], [1, 4]]
B = [[5, 2], [3, 1]]
```

| Operation | Method | Example | Output |
|-----------|--------|---------|--------|
| **Addition** | `add(matrix1, matrix2)` | `calc.add(A, B)` | `[[7.0, 5.0], [4.0, 5.0]]` |
| **Subtraction** | `subtract(matrix1, matrix2)` | `calc.subtract(A, B)` | `[[-3.0, 1.0], [-2.0, 3.0]]` |
| **Matrix Multiplication** | `multiply(matrix1, matrix2)` | `calc.multiply(A, B)` | `[[19, 7], [17, 6]]` |
| **Scalar Multiplication** | `multiply(matrix, num=n)` | `calc.multiply(A, num=2)` | `[[4, 6], [2, 8]]` |
| **Scalar Division** | `divide(matrix, num=n)` | `calc.divide(A, num=2)` | `[[1.0, 1.5], [0.5, 2.0]]` |
| **Determinant** | `determinant(matrix)` | `calc.determinant(A)` | `5.0` |
| **Adjoint** | `adjoint(matrix)` | `calc.adjoint(A)` | `[[4.0, -3.0], [-1.0, 2.0]]` |
| **Inverse** | `multiplicative_inverse(matrix)` | `calc.multiplicative_inverse(A)` | `[[0.8, -0.6], [-0.2, 0.4]]` |

**Notes:**
- Matrix multiplication: returns integer values when possible
- Scalar multiplication: returns integer values when possible
- Scalar division: returns float values
- Addition/Subtraction: returns float values
- Inverse: returns float values

---

### 🧮 3×3 Matrix Operations

```python
from pyeqsolver import Matrices3x3

calc = Matrices3x3()
C = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
D = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # Identity matrix
```

| Operation | Method | Example | Output |
|-----------|--------|---------|--------|
| **Addition** | `add(matrix1, matrix2)` | `calc.add(C, D)` | `[[2.0, 2.0, 3.0], [0.0, 2.0, 4.0], [5.0, 6.0, 1.0]]` |
| **Subtraction** | `subtract(matrix1, matrix2)` | `calc.subtract(C, D)` | `[[0.0, 2.0, 3.0], [0.0, 0.0, 4.0], [5.0, 6.0, -1.0]]` |
| **Matrix Multiplication** | `matrix_multiply(matrix1, matrix2)` | `calc.matrix_multiply(C, D)` | `[[1, 2, 3], [0, 1, 4], [5, 6, 0]]` |
| **Scalar Multiplication** | `scalar_multiply(matrix, scalar)` | `calc.scalar_multiply(C, 3)` | `[[3, 6, 9], [0, 3, 12], [15, 18, 0]]` |
| **Scalar Division** | `scalar_divide(matrix, scalar)` | `calc.scalar_divide(C, 3)` | `[[1.0, 2.0, 3.0], ...]` |
| **Matrix Division** | `matrix_divide(matrix1, matrix2)` | `calc.matrix_divide(C, D)` | C × D⁻¹ |
| **Determinant** | `determinant(matrix)` | `calc.determinant(C)` | `1.0` |
| **Adjoint** | `adjoint(matrix)` | `calc.adjoint(C)` | `[[-24.0, 18.0, 5.0], ...]` |
| **Inverse** | `multiplicative_inverse(matrix)` | `calc.multiplicative_inverse(C)` | `[[-24.0, 18.0, 5.0], ...]` |

**Important Notes for 3×3 Matrices:**
- The `Matrices3x3` class uses **different method names** than `Matrices2x2`:
  - Use `matrix_multiply()` instead of `multiply()` for matrix multiplication
  - Use `scalar_multiply()` instead of `multiply()` for scalar multiplication
  - Use `scalar_divide()` instead of `divide()` for scalar division
- Addition and subtraction return float values
- Matrix and scalar multiplication return integer values when possible
- Matrix division: computes `matrix1 × matrix2⁻¹`

---

### 🔍 Linear Equation Solver

Solve systems of linear equations with ease!

#### Example: 2-Variable System

```python
from pyeqsolver import LinearEquationsSolver

# Define your equations as a string (comma-separated)
solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")

# Get the coefficient matrix (returns only the matrix, not a tuple)
coeff_matrix = solver.A()
print(coeff_matrix)
# [[2.0, 4.0], [3.0, -3.0]]

# Solve using Cramer's Rule
solution = solver.solve('cramer')
for var, val in solution:
    print(f"{var} = {val}")
```

**Output:**
```
x = 11/18
y = 17/18
```

#### Example: 3-Variable System

```python
equations = "3x + y - z = 10, -3x + 4y - z = 10, 3x + y + 4z = 0"
solver = LinearEquationsSolver(equations)

# Solve using matrix inversion
solution = solver.solve('inverse')
for var, val in solution:
    print(f"{var} = {val}")
```

**Output:**
```
x = 8/5
y = 16/5
z = -2
```

#### Solver Features

- **Input Format**: Comma-separated string of equations
  - Supports standard variable names (x, y, z)
  - Coefficients can be integers or decimals
  - Equations must contain `=` sign
  
- **Solution Methods**:
  - `'cramer'`: Uses Cramer's Rule
  - `'inverse'`: Uses Matrix Inversion Method
  
- **Return Format**: List of tuples `[(variable, value), ...]`
  - Values are returned as strings in fraction form (e.g., "11/18")
  - Integer results shown without denominator (e.g., "-2")

---

### ⚠️ Error Handling

pyeqsolver provides comprehensive error handling with custom exceptions:

#### 1. Singular Matrix (InvalidMatrixError)

```python
from pyeqsolver import Matrices3x3, InvalidMatrixError

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

#### 2. Division by Zero (InvalidMatrixError)

```python
try:
    result = calc.scalar_divide(C, 0)
except InvalidMatrixError as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Division by zero is not allowed.
```

#### 3. Equation Parsing Errors (ParseError)

```python
# Empty string
solver = LinearEquationsSolver("")
# ParseError: Equations string cannot be empty.

# Missing equals sign
solver = LinearEquationsSolver("2x + 3y")
# ParseError: Error parsing equation 1 ('2x + 3y'): Equation must contain '=': 2x+3y
```

#### 4. System Size Validation (ValueError)

```python
# Only one equation
solver = LinearEquationsSolver("x = 5")
# ValueError: Only 2x2 and 3x3 systems are supported. Got 1 equation(s).
```

#### 5. Variable Consistency (ValidationError)

```python
# Inconsistent variables
solver = LinearEquationsSolver("x + y = 1, x + z = 2")
# ValidationError: Equation 2 has inconsistent variables. Expected ['x', 'y'], got ['x', 'z']
```

---

## 🧠 API Reference

### `Matrices2x2`

Class for 2×2 matrix operations.

#### Constructor
```python
Matrices2x2()
```
No parameters required.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add(matrix1, matrix2)` | Two 2×2 lists | `list[list[float]]` | Element-wise addition |
| `subtract(matrix1, matrix2)` | Two 2×2 lists | `list[list[float]]` | Element-wise subtraction |
| `multiply(matrix1, matrix2=None, num=None)` | Two matrices OR matrix + scalar | `list[list[int/float]]` | Matrix or scalar multiplication |
| `divide(matrix, num)` | Matrix and non-zero scalar | `list[list[float]]` | Scalar division |
| `determinant(matrix)` | 2×2 list | `float` | Calculate determinant |
| `adjoint(matrix)` | 2×2 list | `list[list[float]]` | Calculate adjoint matrix |
| `multiplicative_inverse(matrix)` | 2×2 list | `list[list[float]]` | Calculate inverse (raises InvalidMatrixError if singular) |

**Usage Notes:**
- `multiply()` can be called with either two matrices OR with one matrix and `num` parameter
- All input matrices must be 2×2
- Determinant must be non-zero for inverse calculation

---

### `Matrices3x3`

Class for 3×3 matrix operations.

#### Constructor
```python
Matrices3x3()
```
No parameters required.

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add(matrix1, matrix2)` | Two 3×3 lists | `list[list[float]]` | Element-wise addition |
| `subtract(matrix1, matrix2)` | Two 3×3 lists | `list[list[float]]` | Element-wise subtraction |
| `matrix_multiply(matrix1, matrix2)` | Two 3×3 lists | `list[list[int/float]]` | Matrix multiplication |
| `scalar_multiply(matrix, scalar)` | Matrix and scalar | `list[list[int/float]]` | Multiply all elements by scalar |
| `scalar_divide(matrix, scalar)` | Matrix and non-zero scalar | `list[list[float]]` | Divide all elements by scalar |
| `matrix_divide(matrix1, matrix2)` | Two 3×3 lists | `list[list[float]]` | Matrix division (A × B⁻¹) |
| `determinant(matrix)` | 3×3 list | `float` | Calculate determinant |
| `adjoint(matrix)` | 3×3 list | `list[list[float]]` | Calculate adjoint matrix |
| `multiplicative_inverse(matrix)` | 3×3 list | `list[list[float]]` | Calculate inverse (raises InvalidMatrixError if singular) |

**Important:**
- Method names differ from `Matrices2x2` class
- All input matrices must be 3×3
- `matrix_divide(A, B)` computes A × B⁻¹, not A / B element-wise

---

### `LinearEquationsSolver`

Class for solving systems of linear equations.

#### Constructor

```python
LinearEquationsSolver(equations_str: str)
```

**Parameters:**
- `equations_str` (str): Comma-separated equations
  - Format: `"equation1, equation2"` or `"eq1, eq2, eq3"`
  - Example: `"2x + 4y = 5, 3x - 3y = -1"`
  - Each equation must contain exactly one `=` sign
  - Variables must be consistent across all equations

**Raises:**
- `ParseError`: Empty string, malformed equations, or missing `=`
- `ValueError`: Number of equations not 2 or 3
- `ValidationError`: Inconsistent variables between equations

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `A()` | None | `list[list[float]]` | Returns coefficient matrix only |
| `solve(method)` | `'cramer'` or `'inverse'` | `list[tuple[str, str]]` | Solves system and returns variable-value pairs |

**Return Format:**
- `A()`: Returns the coefficient matrix (NOT a tuple)
- `solve()`: Returns list of tuples: `[('x', '11/18'), ('y', '17/18')]`
  - Variable names as first element
  - Solutions as fraction strings (or integers when applicable)

---

### Custom Exceptions

#### `InvalidMatrixError`

Raised when:
- Matrix is singular (determinant = 0)
- Division by zero attempted
- Invalid matrix operations

#### `ParseError`

Raised when:
- Equations string is empty
- Equation doesn't contain `=`
- Malformed equation syntax

#### `ValidationError`

Raised when:
- Variables are inconsistent between equations
- Invalid system configuration

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push** to the branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

### Areas for Contribution
- Support for larger matrix sizes (4×4, 5×5, etc.)
- Additional solution methods
- Performance optimizations
- More comprehensive test coverage
- Documentation improvements

---

## 📜 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Hammail Riaz**

- 🐙 GitHub: [@Hammail-Riaz](https://github.com/Hammail-Riaz)
- 📧 Email: hammailriaz.dev@gmail.com

---

## 🕓 Changelog

### Version 1.0.1
- ✅ Initial stable release as `pyeqsolver`
- ✅ 2×2 matrix operations with unified `multiply()` and `divide()` methods
- ✅ 3×3 matrix operations with distinct method names
- ✅ Linear equation solver supporting Cramer's Rule and Matrix Inversion
- ✅ Comprehensive error handling with custom exceptions
- ✅ Fraction-based exact solutions for equation systems

---

## 🆘 Support

Need help? Have suggestions?

- 📝 [Open an issue](https://github.com/Hammail-Riaz/pyeqsolver/issues)
- 📧 Email: hammailriaz.dev@gmail.com
- 💬 Check the [documentation](https://github.com/Hammail-Riaz/pyeqsolver)

---

## 📚 Additional Examples

### Working with Identity Matrix

```python
from pyeqsolver import Matrices3x3

calc = Matrices3x3()
I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
C = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]

# Any matrix multiplied by identity equals itself
result = calc.matrix_multiply(C, I)
# Result: [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
```

### Verifying Inverse

```python
from pyeqsolver import Matrices2x2

calc = Matrices2x2()
A = [[2, 3], [1, 4]]
A_inv = calc.multiplicative_inverse(A)

# A × A⁻¹ should equal identity matrix
result = calc.multiply(A, A_inv)
# Result approximately: [[1.0, 0.0], [0.0, 1.0]]
```

---

**Made with ❤️ for mathematics and Python enthusiasts**

⭐ Star this repo if you find it helpful!
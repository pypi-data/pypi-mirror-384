# 🧮 EqSolver

### A comprehensive Python package for matrix operations and solving linear equations

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/eqsolver.svg)](https://pypi.org/project/eqsolver/)

**[Features](#-features) • [Installation](#️-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)**

---

## ✨ Features

### 🧮 Matrix Operations
- ➕ Addition and subtraction  
- ✖️ Matrix and scalar multiplication  
- ➗ Matrix and scalar division  
- 🔢 Determinant calculation  
- 🔄 Adjoint and inverse matrix computation  

### 🔢 Linear Equation Solver
- 📐 Solve 2×2 and 3×3 systems  
- 🎯 **Cramer's Rule** and **Matrix Inversion**  
- 📝 Parse equations from strings  
- 🎲 Supports fractions for exact results  

### 🛡️ Robust Error Handling
- ❌ Invalid or singular matrices  
- 🚫 Division by zero  
- ⚠️ Inconsistent or malformed equations  

---

## ⚙️ Installation

### Quick Install

```bash
pip install eqsolver
```

### Development Installation

```bash
git clone https://github.com/Hammail-Riaz/eqsolver.git
cd eqsolver
pip install -e .
```

---

## 🚀 Quick Start

```python
from eqsolver import Matrices2x2, LinearEquationsSolver

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
from eqsolver import Matrices2x2

calc = Matrices2x2()
A = [[2, 3], [1, 4]]
B = [[5, 2], [3, 1]]
```

| Operation | Example | Output |
|-----------|---------|--------|
| **Addition** | `calc.add(A, B)` | `[[7.0, 5.0], [4.0, 5.0]]` |
| **Subtraction** | `calc.subtract(A, B)` | `[[-3.0, 1.0], [-2.0, 3.0]]` |
| **Multiplication** | `calc.multiply(A, B)` | Matrix product |
| **Scalar Multiply** | `calc.multiply(A, num=2)` | All elements × 2 |
| **Determinant** | `calc.determinant(A)` | `5.0` |
| **Adjoint** | `calc.adjoint(A)` | `[[4.0, -3.0], [-1.0, 2.0]]` |
| **Inverse** | `calc.multiplicative_inverse(A)` | `[[0.8, -0.6], [-0.2, 0.4]]` |

---

### 🧮 3×3 Matrix Operations

```python
from eqsolver import Matrices3x3

calc = Matrices3x3()
C = [[1, 2, 3], [0, 1, 4], [5, 6, 0]]
D = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # Identity matrix
```

| Operation | Example | Output |
|-----------|---------|--------|
| **Addition** | `calc.add(C, D)` | `[[2, 2, 3], [0, 2, 4], [5, 6, 1]]` |
| **Subtraction** | `calc.subtract(C, D)` | Matrix difference |
| **Determinant** | `calc.determinant(C)` | `1.0` |
| **Adjoint** | `calc.adjoint(C)` | `[[-24, 18, 5], [20, -15, -4], [-5, 4, 1]]` |
| **Inverse** | `calc.multiplicative_inverse(C)` | `[[-24, 18, 5], [20, -15, -4], [-5, 4, 1]]` |

---

### 🔍 Linear Equation Solver

Solve systems of linear equations with ease!

#### Example: 2-Variable System

```python
from eqsolver import LinearEquationsSolver

# Define your equations as a string
solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")

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
equations = "x + 2y + 3z = 6, 2x - y + z = 3, 3x + y - z = 4"
solver = LinearEquationsSolver(equations)

# Solve using matrix inversion
solution = solver.solve('inverse')

for var, val in solution:
    print(f"{var} = {val}")
```

#### Get Coefficient Matrix

```python
solver = LinearEquationsSolver("2x + 4y = 5, 3x - 3y = -1")
A, b = solver.A()  # Returns coefficient matrix and constants vector
```

---

### ⚠️ Error Handling

EqSolver provides comprehensive error handling for common issues:

#### Singular Matrix

```python
from eqsolver import Matrices3x3, InvalidMatrixError

calc = Matrices3x3()
singular = [[1, 2, 3], [2, 4, 6], [3, 6, 9]]  # Linearly dependent rows

try:
    inv = calc.multiplicative_inverse(singular)
except InvalidMatrixError as e:
    print(f"Error: {e}")
```

**Output:**
```
Error: Matrix is singular and cannot be inverted.
```

#### Division by Zero

```python
try:
    result = calc.divide(A, num=0)
except ZeroDivisionError as e:
    print(f"Error: {e}")
```

---

## 🧠 API Reference

### `Matrices2x2` and `Matrices3x3`

Both classes share the same interface:

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add(matrix1, matrix2)` | Two matrices | Matrix | Element-wise addition |
| `subtract(matrix1, matrix2)` | Two matrices | Matrix | Element-wise subtraction |
| `multiply(matrix1, matrix2, num)` | Two matrices or matrix + scalar | Matrix | Matrix multiplication or scalar multiplication |
| `divide(matrix, num)` | Matrix and scalar | Matrix | Scalar division |
| `determinant(matrix)` | Matrix | Float | Calculate determinant |
| `adjoint(matrix)` | Matrix | Matrix | Calculate adjoint (adjugate) |
| `multiplicative_inverse(matrix)` | Matrix | Matrix | Calculate inverse matrix |

---

### `LinearEquationsSolver`

#### Constructor

```python
LinearEquationsSolver(equations_str: str)
```

**Parameters:**
- `equations_str`: Comma-separated string of equations (e.g., `"2x + 3y = 5, x - y = 1"`)

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `A()` | None | Tuple[Matrix, Vector] | Returns coefficient matrix and constants vector |
| `solve(method)` | `'cramer'` or `'inverse'` | List[Tuple[str, str]] | Solves equations and returns variable-value pairs |

---

### `InvalidMatrixError`

Custom exception raised for:
- Singular matrices (determinant = 0)
- Invalid matrix dimensions
- Malformed input

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

### Version 1.0.0
- ✅ Initial stable release as `eqsolver`
- ✅ Added 2×2 and 3×3 matrix operations
- ✅ Added linear equation solver with Cramer's Rule and Matrix Inversion
- ✅ Comprehensive error handling
- ✅ Complete documentation and examples

---

## ❤️ Acknowledgments

- Built with **Python 3.8+**
- Inspired by linear algebra education needs
- Thanks to all contributors and the open-source community

---

## 🆘 Support

Need help? Have suggestions?

- 📝 [Open an issue](https://github.com/Hammail-Riaz/eqsolver/issues)
- 📧 Email: hammailriaz.dev@gmail.com

---

**Made with ❤️ for mathematics and Python enthusiasts**

⭐ Star this repo if you find it helpful!
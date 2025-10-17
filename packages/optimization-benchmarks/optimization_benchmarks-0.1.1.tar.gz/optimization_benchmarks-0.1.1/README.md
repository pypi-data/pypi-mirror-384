
## **optimization-benchmarks**

[![PyPI version](https://badge.fury.io/py/optimization-benchmarks.svg)](https://pypi.org/project/optimization-benchmarks/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python package providing 50+ classical mathematical benchmark functions for testing and evaluating optimization algorithms.

## 🎯 Features

- **50+ Standard Benchmark Functions**: Including Ackley, Rastrigin, Rosenbrock, Griewank, and many more
- **Vectorized NumPy Implementation**: Fast and efficient computation
- **Well-Documented**: Each function includes domain constraints and global minima
- **Type Hints**: Full type annotation support
- **Command-Line Interface**: Evaluate functions directly from the terminal
- **Zero Dependencies**: Only requires NumPy
- **Academic Citations**: Properly cited mathematical formulations

## 📦 Installation

### From PyPI
```
pip install optimization-benchmarks
```
### From Source
```
git clone https://github.com/ak-rahul/optimization-benchmarks.git
cd optimization-benchmarks
pip install -e .
```
----

## 🚀 Quick Start
```
import numpy as np
from optimization_benchmarks import ackley, rastrigin, rosenbrock

x = np.zeros(5)
result = ackley(x)
print(f"Ackley(0) = {result}") # Should be close to 0

x = np.ones(10)
result = rosenbrock(x)
print(f"Rosenbrock(1) = {result}") # Should be 0

x = np.random.randn(5)
result = rastrigin(x)
print(f"Rastrigin(x) = {result}")
```

---

## 📊 Usage Examples

### Benchmarking an Optimization Algorithm

```
import numpy as np
from optimization_benchmarks import ackley, rastrigin, sphere

def my_optimizer(func, bounds, max_iter=1000):
"""Your optimization algorithm here."""
# ... implementation ...
pass

test_functions = {
'Sphere': (sphere, [(-5.12, 5.12)] * 10),
'Ackley': (ackley, [(-32, 32)] * 10),
'Rastrigin': (rastrigin, [(-5.12, 5.12)] * 10),
}

for name, (func, bounds) in test_functions.items():
best_x, best_f = my_optimizer(func, bounds)
print(f"{name}: f(x*) = {best_f}")
```

---

## 🎯 Using Benchmark Metadata (New in v0.1.1)

Version 0.1.1 introduces comprehensive metadata for all 55 functions, eliminating the need to manually specify bounds and known minima:

```
from optimization_benchmarks import BENCHMARK_SUITE, get_function_info
import numpy as np
```

### Get all available functions
```
from optimization_benchmarks import get_all_functions
print(f"Total functions: {len(get_all_functions())}")  # 55
```

### Get metadata for a specific function
```
info = get_function_info('ackley')
func = info['function']
bounds = info['bounds'] * info['default_dim']  # 10D by default
known_min = info['known_minimum']
```

### Test at known minimum
```
x = np.zeros(info['default_dim'])
result = func(x)
print(f"Ackley(0) = {result:.6f}, Expected: {known_min}")
```

### Simple Benchmarking with Metadata

```
from optimization_benchmarks import BENCHMARK_SUITE
import numpy as np

def simple_random_search(func, bounds, n_iter=1000):
    """Simple random search optimizer."""
    best_x = None
    best_cost = float('inf')
    
    for _ in range(n_iter):
        x = np.array([np.random.uniform(b, b) for b in bounds])
        cost = func(x)
        if cost < best_cost:
            best_cost = cost
            best_x = x
    
    return best_x, best_cost
```

### Benchmark on all functions - no manual bounds needed!
```
for name, meta in BENCHMARK_SUITE.items():
    func = meta['function']
    bounds = meta['bounds'] * meta['default_dim']
    known_min = meta['known_minimum']
    
    best_x, best_cost = simple_random_search(func, bounds)
    error = abs(best_cost - known_min)
    
    print(f"{name:20s} | Found: {best_cost:12.6f} | "
          f"Expected: {known_min:12.6f} | Error: {error:10.6f}")
```

### Metadata Helper Functions

| Function | Description |
|----------|-------------|
| `BENCHMARK_SUITE` | Dictionary with all 55 functions and metadata |
| `get_all_functions()` | Returns list of all function names |
| `get_function_info(name)` | Returns metadata for specific function |
| `get_bounds(name, dim=None)` | Returns bounds for given dimension |
| `get_function_list()` | Returns formatted string with all functions |

### Metadata Fields

Each entry in `BENCHMARK_SUITE` contains:
- **`function`**: The callable function
- **`bounds`**: List of (min, max) tuples for each dimension
- **`default_dim`**: Recommended test dimension
- **`known_minimum`**: Known global minimum value
- **`optimal_point`**: Location(s) of the global minimum

---


## 🎮 Command-Line Interface

The package includes a CLI for quick function evaluation:

### List all available functions
```
optbench --list
```

### Get function information
```
optbench --info ackley
```

### Evaluate a function
```
optbench --function rastrigin --values 0 0 0 0 0
```

### Batch evaluation from CSV

```
optbench --function sphere --input points.csv --output results.json
```

---


## 📚 Available Functions

### Multimodal Functions
- `ackley` - Multiple local minima with deep global minimum
- `rastrigin` - Highly multimodal with regular structure
- `griewank` - Multimodal with product term
- `schwefel2_26` - Deceptive with distant global minimum
- `levy` - Multimodal with sharp global minimum
- `michalewicz` - Steep ridges and valleys

### Unimodal Functions
- `sphere` - Simple convex quadratic
- `rosenbrock` - Narrow curved valley
- `sum_squares` - Weighted sphere function
- `hyperellipsoid` - Axis-parallel ellipsoid

### 2D Test Functions
- `beale` - Narrow valley
- `booth` - Simple quadratic
- `matyas` - Plate-like surface
- `himmelblau` - Four identical local minima
- `goldstein_price` - Multiple local minima
- `easom` - Flat surface with narrow peak

### Special Functions
- `branin` - Three global minima
- `camel3` - Three-hump camel function
- `camel6` - Six-hump camel function
- `kowalik` - Parameter estimation problem
- `langerman` - Multimodal test function

**And 30+ more functions!** 

## 🔬 Function Properties

Each function includes:
- **Domain**: Valid input ranges
- **Dimension**: Number of variables (n for arbitrary dimensions)
- **Global Minimum**: Known optimal value and location
- **Mathematical Formula**: Documented in docstrings


## 🎓 Academic Use

This package is perfect for:
- **Algorithm Development**: Test new optimization algorithms
- **Comparative Studies**: Benchmark against existing methods
- **Academic Research**: Reproduce published results
- **Teaching**: Demonstrate optimization concepts
- **Thesis Projects**: Comprehensive evaluation suite

### Citing This Package

If you use this package in academic work, please cite:
```
@software{optimization_benchmarks,
author = {AK Rahul},
title = {optimization-benchmarks: Benchmark Functions for Optimization Algorithms},
year = {2025},
publisher = {PyPI},
url = {https://github.com/ak-rahul/optimization-benchmarks}
}
```

### Mathematical Formulations Based On

[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C.  
[2] Surjanovic, S. & Bingham, D. (2013). Virtual Library of Simulation Experiments.  
[3] Jamil, M., & Yang, X. S. (2013). A literature survey of benchmark functions for global optimization problems.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

    1. Fork the repository
    2. Create your feature branch (`git checkout -b feature/new-function`)
    3. Add your function to `functions.py`
    4. Add tests to `tests/test_functions.py`
    5. Run tests: `pytest`
    6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Mathematical formulations based on the MVF C library by E.P. Adorio
- Function definitions from Virtual Library of Simulation Experiments
- Inspired by the optimization research community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ak-rahul/optimization-benchmarks/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ak-rahul/optimization-benchmarks/discussions)


## 🔗 Related Projects

- [SciPy Optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html) - Optimization algorithms
- [PyGMO](https://esa.github.io/pygmo2/) - Massively parallel optimization
- [DEAP](https://github.com/DEAP/deap) - Evolutionary algorithms

---

**Made with ❤️ for the optimization community**

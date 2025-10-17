"""
Optimization Benchmark Functions Package

A comprehensive collection of standard benchmark functions for evaluating 
optimization algorithms. This package provides Python implementations of 
classical test functions widely used in the optimization research community.

Mathematical formulations are based on well-established definitions from:
- MVF C library[1]
- Virtual Library of Simulation Experiments[2]
- Academic optimization literature[3]

References:
-----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C.
    University of the Philippines Diliman.
[2] Surjanovic, S. & Bingham, D. (2013). Virtual Library of Simulation Experiments.
    Simon Fraser University.
[3] Jamil, M., & Yang, X. S. (2013). A literature survey of benchmark functions 
    for global optimization problems. International Journal of Mathematical 
    Modelling and Numerical Optimisation, 4(2), 150-194.

License: MIT
"""

from .functions import (
    ackley, beale, bohachevsky1, bohachevsky2, booth, box_betts,
    branin, branin2, camel3, camel6, chichinadze, colville,
    corana, easom, eggholder, exp2, fraudenstein_roth, gear,
    goldstein_price, griewank, himmelblau, holzman1, holzman2,
    hosaki, hyperellipsoid, katsuura, kowalik, langerman,
    lennard_jones, leon, levy, maxmod, matyas, mccormick,
    michalewicz, multimod, rastrigin, rastrigin2, rosenbrock,
    rosenbrock_ext1, rosenbrock_ext2, schaffer1, schaffer2,
    schwefel1_2, schwefel2_21, schwefel2_22, schwefel2_26,
    schwefel3_2, sphere, sphere2, step, step2, stretched_v,
    sum_squares, trecanni, trefethen4, watson, xor, zettl,
    zimmerman,
)

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

class BenchmarkFunction:
    """
    Wrapper class for optimization benchmark functions.
    
    Each instance wraps a Python function that takes a NumPy array 
    and returns a float.
    """
    def __init__(self, func):
        self._func = func
        self.name = func.__name__
        self.__doc__ = func.__doc__
    
    def __call__(self, x):
        return self._func(x)
    
    def __repr__(self):
        return f"<BenchmarkFunction '{self.name}'>"

# Populate the global registry
FUNCTIONS = {
    fn.__name__.lower(): BenchmarkFunction(fn) for fn in (
        ackley, beale, bohachevsky1, bohachevsky2, booth, box_betts,
        branin, branin2, camel3, camel6, chichinadze, colville,
        corana, easom, eggholder, exp2, fraudenstein_roth, gear,
        goldstein_price, griewank, himmelblau, holzman1, holzman2,
        hosaki, hyperellipsoid, katsuura, kowalik, langerman,
        lennard_jones, leon, levy, maxmod, matyas, mccormick,
        michalewicz, multimod, rastrigin, rastrigin2, rosenbrock,
        rosenbrock_ext1, rosenbrock_ext2, schaffer1, schaffer2,
        schwefel1_2, schwefel2_21, schwefel2_22, schwefel2_26,
        schwefel3_2, sphere, sphere2, step, step2, stretched_v,
        sum_squares, trecanni, trefethen4, watson, xor, zettl,
        zimmerman
    )
}

def get_function(name: str) -> BenchmarkFunction:
    """
    Retrieve a benchmark function by name (case-insensitive).
    
    Args:
        name: Function name (e.g., 'ackley', 'rosenbrock')
    
    Returns:
        BenchmarkFunction wrapper instance
    
    Raises:
        KeyError: If function name not found
    """
    key = name.lower()
    if key not in FUNCTIONS:
        raise KeyError(f"No benchmark function named '{name}'.")
    return FUNCTIONS[key]

__all__ = [
    "ackley", "beale", "bohachevsky1", "bohachevsky2", "booth",
    "box_betts", "branin", "branin2", "camel3", "camel6",
    "chichinadze", "colville", "corana", "easom", "eggholder",
    "exp2", "fraudenstein_roth", "gear", "goldstein_price", "griewank",
    "himmelblau", "holzman1", "holzman2", "hosaki", "hyperellipsoid",
    "katsuura", "kowalik", "langerman", "lennard_jones", "leon",
    "levy", "maxmod", "matyas", "mccormick", "michalewicz",
    "multimod", "rastrigin", "rastrigin2", "rosenbrock",
    "rosenbrock_ext1", "rosenbrock_ext2", "schaffer1", "schaffer2",
    "schwefel1_2", "schwefel2_21", "schwefel2_22", "schwefel2_26",
    "schwefel3_2", "sphere", "sphere2", "step", "step2",
    "stretched_v", "sum_squares", "trecanni", "trefethen4", "watson",
    "xor", "zettl", "zimmerman", "get_function", "BenchmarkFunction"
]

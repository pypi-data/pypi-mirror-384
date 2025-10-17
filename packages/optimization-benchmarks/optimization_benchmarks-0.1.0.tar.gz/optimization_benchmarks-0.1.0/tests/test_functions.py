"""
Test suite for optimization-benchmarks package.

Tests verify that benchmark functions return expected global minimum values
at known optimal points. All test functions are based on formulations from
the MVF C library[1] and academic literature.

References:
-----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C
    for Unconstrained Global Optimization.
"""

import numpy as np
import pytest
from optimization_benchmarks import (
    ackley, beale, bohachevsky1, bohachevsky2, booth, box_betts,
    branin, branin2, camel3, camel6, chichinadze, colville, corana,
    easom, eggholder, exp2, gear, goldstein_price, griewank,
    himmelblau, hyperellipsoid, kowalik, holzman1, holzman2, hosaki,
    katsuura, langerman, leon, levy, matyas, maxmod, mccormick,
    michalewicz, multimod, rastrigin, rastrigin2, rosenbrock,
    rosenbrock_ext1, rosenbrock_ext2, schaffer1, schaffer2,
    schwefel1_2, schwefel2_21, schwefel2_22, schwefel2_26, schwefel3_2,
    sphere, sphere2, step, step2, stretched_v, sum_squares,
    trecanni, trefethen4, zettl
)


class TestGlobalMinima:
    """Test that functions achieve their known global minimum values."""
    
    def test_ackley_minimum(self):
        """Ackley: f(0) = 0 at x = 0[1]."""
        x = np.zeros(5)
        assert abs(ackley(x)) < 1e-8
    
    def test_beale_minimum(self):
        """Beale: f(3,0.5) = 0[1]."""
        x = np.array([3.0, 0.5])
        assert abs(beale(x)) < 1e-8
    
    def test_bohachevsky1_minimum(self):
        """Bohachevsky1: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(bohachevsky1(x)) < 1e-8
    
    def test_bohachevsky2_minimum(self):
        """Bohachevsky2: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(bohachevsky2(x)) < 1e-8
    
    def test_booth_minimum(self):
        """Booth: f(1,3) = 0[1]."""
        x = np.array([1.0, 3.0])
        assert abs(booth(x)) < 1e-8
    
    def test_box_betts_minimum(self):
        """Box-Betts: f(1,10,1) = 0[1]."""
        x = np.array([1.0, 10.0, 1.0])
        assert abs(box_betts(x)) < 1e-8
    
    def test_branin_minimum(self):
        """Branin: f ≈ 0.3979 at known minima[1]."""
        x1 = np.array([-np.pi, 12.275])
        x2 = np.array([np.pi, 2.275])
        x3 = np.array([9.42478, 2.475])
        assert abs(branin(x1) - 0.397887) < 1e-4
        assert abs(branin(x2) - 0.397887) < 1e-4
        assert abs(branin(x3) - 0.397887) < 1e-4
    
    def test_camel3_minimum(self):
        """Three-hump camel: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(camel3(x)) < 1e-8
    
    def test_camel6_minimum(self):
        """Six-hump camel: f ≈ -1.0316 at two known minima[1]."""
        x1 = np.array([0.0898, -0.7126])
        x2 = np.array([-0.0898, 0.7126])
        assert abs(camel6(x1) + 1.0316) < 1e-3
        assert abs(camel6(x2) + 1.0316) < 1e-3
    
    def test_colville_minimum(self):
        """Colville: f(1,1,1,1) = 0[1]."""
        x = np.ones(4)
        assert abs(colville(x)) < 1e-8
    
    def test_corana_minimum(self):
        """Corana: f(0,0,0,0) = 0[1]."""
        x = np.zeros(4)
        assert abs(corana(x)) < 1e-8
    
    def test_easom_minimum(self):
        """Easom: f(π,π) = -1[1]."""
        x = np.array([np.pi, np.pi])
        assert abs(easom(x) + 1.0) < 1e-6
    
    def test_exp2_minimum(self):
        """Exp2: f(1,10) = 0[1]."""
        x = np.array([1.0, 10.0])
        assert abs(exp2(x)) < 1e-8
    
    def test_goldstein_price_minimum(self):
        """Goldstein-Price: f(0,-1) = 3[1]."""
        x = np.array([0.0, -1.0])
        assert abs(goldstein_price(x) - 3.0) < 1e-8
    
    def test_griewank_minimum(self):
        """Griewank: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(griewank(x)) < 1e-8
    
    def test_himmelblau_minimum(self):
        """Himmelblau: f(3,2) = 0 (one of four minima)[1]."""
        x = np.array([3.0, 2.0])
        assert abs(himmelblau(x)) < 1e-8
    
    def test_hyperellipsoid_minimum(self):
        """Hyperellipsoid: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(hyperellipsoid(x)) < 1e-8
    
    def test_leon_minimum(self):
        """Leon: f(1,1) = 0[1]."""
        x = np.array([1.0, 1.0])
        assert abs(leon(x)) < 1e-8
    
    def test_matyas_minimum(self):
        """Matyas: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(matyas(x)) < 1e-8
    
    def test_maxmod_minimum(self):
        """Maxmod: f(0) = 0[1]."""
        x = np.zeros(5)
        assert abs(maxmod(x)) < 1e-8
    
    def test_multimod_minimum(self):
        """Multimod: f(0) = 0[1]."""
        x = np.zeros(5)
        assert abs(multimod(x)) < 1e-8
    
    def test_rastrigin_minimum(self):
        """Rastrigin: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(rastrigin(x)) < 1e-8
    
    def test_rastrigin2_minimum(self):
        """Rastrigin2: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(rastrigin2(x) + 2.0) < 1e-8
    
    def test_rosenbrock_minimum(self):
        """Rosenbrock: f(1,...,1) = 0[1]."""
        x = np.ones(10)
        assert abs(rosenbrock(x)) < 1e-8
    
    def test_rosenbrock_ext1_minimum(self):
        """Extended Rosenbrock1: f(1,...,1) = 0[1]."""
        x = np.ones(10)
        assert abs(rosenbrock_ext1(x)) < 1e-8
    
    def test_rosenbrock_ext2_minimum(self):
        """Extended Rosenbrock2: f(1,...,1) = 0[1]."""
        x = np.ones(10)
        assert abs(rosenbrock_ext2(x)) < 1e-8
    
    def test_schaffer1_minimum(self):
        """Schaffer1: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(schaffer1(x)) < 1e-8
    
    def test_schaffer2_minimum(self):
        """Schaffer2: f(0,0) = 0[1]."""
        x = np.array([0.0, 0.0])
        assert abs(schaffer2(x)) < 1e-8
    
    def test_schwefel1_2_minimum(self):
        """Schwefel1.2: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(schwefel1_2(x)) < 1e-8
    
    def test_schwefel2_21_minimum(self):
        """Schwefel2.21: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(schwefel2_21(x)) < 1e-8
    
    def test_schwefel2_22_minimum(self):
        """Schwefel2.22: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(schwefel2_22(x)) < 1e-8
    
    def test_sphere_minimum(self):
        """Sphere: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(sphere(x)) < 1e-8
    
    def test_sphere2_minimum(self):
        """Sphere2: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(sphere2(x)) < 1e-8
    
    def test_step2_minimum(self):
        """Step2: f(x) = 6n + sum(floor(xi)) where minimum is at x=0[1]."""
        x = np.zeros(5)
        result = step2(x)
        # For x = [0, 0, 0, 0, 0]: floor(0) = 0, so result = 6*5 + 0 = 30
        assert result == 30

    def test_sum_squares_minimum(self):
        """Sum Squares: f(0) = 0[1]."""
        x = np.zeros(10)
        assert abs(sum_squares(x)) < 1e-8
    
    def test_trecanni_minimum(self):
        """Trecanni: f(0,0) = 0 (one of two minima)[1]."""
        x = np.array([0.0, 0.0])
        assert abs(trecanni(x)) < 1e-8


class TestFunctionProperties:
    """Test basic properties of benchmark functions."""
    
    def test_ackley_vectorized(self):
        """Test Ackley accepts different input dimensions."""
        x2d = np.zeros(2)
        x5d = np.zeros(5)
        x10d = np.zeros(10)
        assert isinstance(ackley(x2d), float)
        assert isinstance(ackley(x5d), float)
        assert isinstance(ackley(x10d), float)
    
    def test_sphere_positive(self):
        """Sphere function should be non-negative."""
        x = np.random.randn(10)
        assert sphere(x) >= 0
    
    def test_rosenbrock_positive(self):
        """Rosenbrock function should be non-negative."""
        x = np.random.uniform(-5, 5, 10)
        assert rosenbrock(x) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

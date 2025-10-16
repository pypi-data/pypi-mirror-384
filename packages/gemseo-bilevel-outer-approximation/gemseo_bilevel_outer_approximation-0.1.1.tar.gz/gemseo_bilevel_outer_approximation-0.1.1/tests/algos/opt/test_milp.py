# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import annotations

import pytest
from gemseo.algos.design_space import DesignSpace
from gemseo.algos.opt.factory import OptimizationLibraryFactory
from gemseo.algos.optimization_problem import OptimizationProblem
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.core.mdo_functions.mdo_linear_function import MDOLinearFunction
from numpy import array

from gemseo_bilevel_outer_approximation.algos.opt.ortools_milp.ortools_milp import (
    OrtoolsMILPAlgorithmDescription,
)


@pytest.fixture
def milp_problem():
    """Milp problem fixture."""
    design_space = DesignSpace()
    design_space.add_variable("x", lower_bound=0.0, upper_bound=1.0, value=0.5)
    design_space.add_variable(
        "y",
        lower_bound=0.0,
        upper_bound=1.0,
        value=0,
        type_=design_space.DesignVariableType.INTEGER,
    )

    # Optimization functions
    args = ["x", "y"]
    problem = OptimizationProblem(design_space, is_linear=True)
    problem.objective = MDOLinearFunction(
        array([1.0, 1.0]), "f", MDOFunction.FunctionType.OBJ, args, -1.0
    )
    ineq_constraint = MDOLinearFunction(array([1.0, 1.0]), "g", input_names=args)
    problem.add_constraint(ineq_constraint, 1.0, MDOFunction.ConstraintType.INEQ)
    eq_constraint = MDOLinearFunction(array([-2.0, 1.0]), "h", input_names=args)
    problem.add_constraint(eq_constraint, 0.0, MDOFunction.ConstraintType.EQ)
    return problem


@pytest.mark.parametrize("description", [OrtoolsMILPAlgorithmDescription])
def test_init(description):
    """Test solver are correctly initialized."""
    factory = OptimizationLibraryFactory()
    if factory.is_available(description.library_name):
        factory.create(description.library_name)


@pytest.mark.parametrize("algo_name", ["Scipy_MILP", "ORTOOLS_MILP"])
def test_solve_milp(milp_problem, algo_name):
    """Test MILP solvers."""
    optim_result = OptimizationLibraryFactory().execute(
        milp_problem, algo_name=algo_name
    )
    assert all(optim_result.x_opt == array([0, 0]))
    assert optim_result.f_opt == -1.0

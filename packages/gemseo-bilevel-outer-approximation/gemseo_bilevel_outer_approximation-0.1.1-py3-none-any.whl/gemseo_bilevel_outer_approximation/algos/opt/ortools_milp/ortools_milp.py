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
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or initial
#                           documentation
#        :author: Simone Coniglio
"""SciPy linear programming library wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Final

from gemseo.algos.design_space_utils import get_value_and_bounds
from gemseo.algos.opt.base_optimization_library import BaseOptimizationLibrary
from gemseo.algos.opt.base_optimization_library import OptimizationAlgorithmDescription
from gemseo.algos.opt.core.linear_constraints import build_constraints_matrices
from gemseo.algos.optimization_problem import OptimizationProblem
from gemseo.core.mdo_functions.mdo_linear_function import MDOLinearFunction
from numpy import array
from numpy import inf
from numpy import isinf
from numpy import mod
from numpy import ones_like
from ortools.linear_solver import pywraplp

from gemseo_bilevel_outer_approximation.algos.opt.ortools_milp.ortools_milp_settings import (  # noqa: E501
    OrtoolsMilp_Settings,
)

if TYPE_CHECKING:
    from gemseo.algos.optimization_problem import OptimizationProblem


@dataclass
class OrtoolsMILPAlgorithmDescription(OptimizationAlgorithmDescription):
    """The description of a MILP optimization algorithm from the Ortools library."""

    for_linear_problems: bool = True
    handle_equality_constraints: bool = True
    handle_inequality_constraints: bool = True
    library_name: str = "Ortools"
    handle_integer_variables: bool = True


class OrtoolsMILP(BaseOptimizationLibrary[OrtoolsMilp_Settings]):
    """SciPy Mixed Integer Linear Programming library interface.

    See OptimizationLibrary.
    """

    VAR_PREFIX: Final[str] = "x_"

    LIB_COMPUTE_GRAD: ClassVar[bool] = True

    LIBRARY_NAME: Final[str] = "Ortools"

    ALGORITHM_INFOS: ClassVar[dict[str, OrtoolsMILPAlgorithmDescription]] = {
        "ORTOOLS_MILP": OrtoolsMILPAlgorithmDescription(
            algorithm_name="Branch & Cut algorithm",
            description=("Mixed-integer linear programming"),
            internal_algorithm_name="milp",
            Settings=OrtoolsMilp_Settings,
        ),
    }

    def __init__(self, algo_name: str = "ORTOOLS_MILP") -> None:  # noqa:D107
        super().__init__(algo_name)

    def _run(self, problem: OptimizationProblem) -> tuple[Any, Any]:
        # Get the starting point and bounds
        _x_0, l_b, u_b = get_value_and_bounds(
            problem.design_space,
            normalize_ds=self._settings.normalize_design_space,
            as_dict=False,
        )
        # Replace infinite bounds with None

        # Build the functions matrices
        # N.B. use the non-processed functions to access the coefficients
        obj_coeff = problem.objective.original.coefficients[0, :].real
        constraints = list(problem.constraints.get_originals())
        ineq_lhs, ineq_rhs = build_constraints_matrices(
            constraints, MDOLinearFunction.ConstraintType.INEQ
        )
        eq_lhs, eq_rhs = build_constraints_matrices(
            constraints, MDOLinearFunction.ConstraintType.EQ
        )
        solver = pywraplp.Solver(
            "Outer Approximation Master Problem",
            pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING,
        )
        tl = self._settings.milp_time_limit
        if tl:
            solver.set_time_limit(tl)
        # create the design variables
        variables = []
        count = 0
        values = problem.design_space.get_current_value()
        integrality = array([isinf(x) or x is None or not mod(x, 1) for x in values])
        for count, (xl, xu, integer) in enumerate(
            zip(l_b, u_b, integrality, strict=False)
        ):
            if integer == 1:
                variables.append(
                    solver.IntVar(xl, xu, self.VAR_PREFIX + str(count + 1))
                )
            else:
                variables.append(
                    solver.NumVar(xl, xu, self.VAR_PREFIX + str(count + 1))
                )
        # define the objective function
        objective = sum(c * x for c, x in zip(obj_coeff, variables, strict=False))
        solver.Minimize(objective)
        # add inequality constraints
        for cc, lb, ub in zip(
            ineq_lhs, -inf * ones_like(ineq_rhs), ineq_rhs, strict=False
        ):
            constraint = sum(c * x for c, x in zip(cc, variables, strict=False))
            if not isinf(lb):
                solver.Add(constraint >= lb)
            if not isinf(ub):
                solver.Add(constraint <= ub)
        # add equality constraints with eq. tolerance
        for cc, lb, ub in zip(
            eq_lhs,
            eq_rhs - self._settings.eq_tolerance,
            eq_rhs + self._settings.eq_tolerance,
            strict=False,
        ):
            constraint = sum(c * x for c, x in zip(cc, variables, strict=False))
            if not isinf(lb):
                solver.Add(constraint >= lb)
            if not isinf(ub):
                solver.Add(constraint <= ub)
        # |g| is in charge of ensuring max iterations, since it may
        # have a different definition of iterations, such as for SLSQP
        # for instance which counts duplicate calls to x as a new iteration

        # For the "revised simplex" algorithm (available since SciPy 1.3.0 which
        # requires Python 3.5+) the initial guess must be a basic feasible solution,
        # or BFS (geometrically speaking, a vertex of the feasible polyhedron).
        # Here the passed initial guess is always ignored.
        # (A BFS will be automatically looked for during the first phase of the simplex
        # algorithm.)
        solver_status = solver.Solve()
        # Gather the optimization results
        x_opt = array([a.solution_value() for a in variables])
        # N.B. SciPy tolerance on bounds is higher than the DesignSpace one
        x_opt = problem.design_space.project_into_bounds(x_opt)
        _val_opt, _jac_opt = problem.evaluate_functions(
            design_vector=x_opt,
            design_vector_is_normalized=False,
            preprocess_design_vector=False,
            jacobian_functions=(),
        )
        # f_opt = val_opt[problem.objective.name]
        # constraint_names = problem.constraints.get_names()
        # constraint_values = {key: val_opt[key] for key in constraint_names}
        # constraints_grad = {key: jac_opt[key] for key in constraint_names}
        # is_feasible = problem.constraints.is_point_feasible(val_opt)

        return "", solver_status

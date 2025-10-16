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

# Copyright (c) 2022 IRT-AESE.
# All rights reserved.
#
# Contributors:
#    AUTHORS:
#        :author: Pierre-Jean Barjhoux
#        :author: Simone Coniglio
"""Bi-level Outer Approximation Optimizer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.algos.design_space import DesignSpace
from gemseo.algos.optimization_problem import OptimizationProblem
from gemseo.core.chains.chain import MDOChain
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.core.mdo_functions.mdo_linear_function import MDOLinearFunction
from gemseo.core.parallel_execution.callable_parallel_execution import (
    CallableParallelExecution,
)
from numpy import all as np_all
from numpy import any as np_any
from numpy import append
from numpy import argmin
from numpy import argsort
from numpy import array
from numpy import atleast_1d
from numpy import atleast_2d
from numpy import concatenate
from numpy import diag
from numpy import dot
from numpy import geomspace
from numpy import inf
from numpy import isclose
from numpy import ones
from numpy import sum as np_sum
from numpy import tile
from numpy import unique
from numpy import where
from numpy import zeros
from numpy.linalg import lstsq
from numpy.linalg import matrix_rank

from gemseo_bilevel_outer_approximation.algos.opt.core.filter_dict_for_settings import (
    filter_dict_for_settings,
)
from gemseo_bilevel_outer_approximation.algos.opt.ortools_milp.ortools_milp import (
    OrtoolsMILP,
)
from gemseo_bilevel_outer_approximation.algos.opt.ortools_milp.ortools_milp_settings import (  # noqa: E501
    OrtoolsMilp_Settings,
)
from gemseo_bilevel_outer_approximation.algos.opt.scipy_milp.extended_scipy_milp import (  # noqa: E501
    ExtendedScipyMILP,
)
from gemseo_bilevel_outer_approximation.algos.opt.scipy_milp.extended_scipy_milp_settings import (  # noqa: E501
    ExtendedScipyMILP_Settings,
)
from gemseo_bilevel_outer_approximation.disciplines.enumerative_to_one_hot import (
    EnumerativeToOneHot,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.algos.database import Database
    from gemseo.core.discipline import Discipline
    from gemseo.typing import RealArray
    from numpy import ndarray

    from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
        CatalogueDesignSpace,
    )

LOGGER = logging.getLogger(__name__)


# TODO: to refactor (split class)
class OuterApproximationOptimizer:
    """Outer Approximation Optimizer class.

    Solve an integer optimization problem with an outer approximation approach. The
    outer approximation solve problem including the set of integer or categorical design
    variables.
    """

    distance_filter_ratio: float | None
    """The ratio between current step and the history filter distance."""

    n_processes: int
    """The number of parallel process for DOE execution."""

    min_step: int
    """The minimum iteration step in terms of catalog choice variations."""

    _milp_settings: ExtendedScipyMILP_Settings | OrtoolsMilp_Settings
    """MILP solver settings."""

    _use_scipy: bool
    """Whether to use Scipy MILP solver."""

    delta_bound: float
    """The upper bound of constraint violation."""

    use_bilateral_adaptation: bool
    """Whether to use bilateral adaptation."""

    _max_infeasible_history_size: int
    """The max infeasible point history size."""

    _max_feasible_history_size: int
    """The max feasible point history size."""

    current_step: int
    """The current iteration step in terms of catalog choice variations."""

    infeasible_history_size: int
    """The infeasible point history size."""

    feasible_history_size: int
    """The feasible point history size."""

    gradient_free: bool
    """Whether to use gradient-free optimization."""

    max_step: int
    """The maximum iteration step in terms of catalog choice variations."""

    function_names: list[str]
    "The names of the function to be extracted from database at each iteration."

    eq_tolerance: float
    """The linear equality constraints tolerance."""

    upper_bound_stall: int
    """The maximum number of main problem iterations not changing the upper bound."""

    time_limit_milliseconds: int | None
    """The time limit to solve the MILP in milliseconds."""

    initial_doe: ndarray | None
    """The initial design of experiments for parallel execution.

    If None, it's generated automatically generated.
    """

    n_parallel_points: int
    """The number of parallel evaluations of the sub-problem optimizations."""

    use_adaptative_convexification: bool
    """Whether the adaptive convexification needs to be activated."""

    min_dfk: float
    """The convexity margin of the adaptive convexification."""

    posa: float
    """The Post Optimal Sensitivity Amplification constant."""

    epsilon: float
    """The upper bound tolerance."""

    max_iter: int
    """The maximum number of iterations."""

    normalize_design_space: bool
    """If True, normalize design space."""

    n_members: dict[str, int] | None
    """The dimension of each categorical design variable."""

    n_catalogues: dict[str, int] | None
    """The number of catalog choice per categorical design variable."""

    message: str
    """Solver message."""

    design_space: CatalogueDesignSpace
    """The OptimizationProblem design_space."""

    database: Database
    """The OptimizationProblem database."""

    problem_copy: OptimizationProblem
    """The copy of OptimizationProblem to be solved."""

    problem: OptimizationProblem
    """The OptimizationProblem to be solved."""

    LOWER_BOUND_NAME: ClassVar[str] = "lower bound"
    PRIMAL_SOL_NAME: ClassVar[str] = "primal solution"
    UPPER_BOUND_NAME: ClassVar[str] = "upper bound"
    UPPER_BOUND_ALPHA_NAME: ClassVar[str] = "upper bound alpha"
    BI_LEVEL_ITER_NAME: ClassVar[str] = "Bi-level iteration"
    IS_FEASIBLE_NAME: ClassVar[str] = "is_feasible"

    ABSOLUTE_OBJ_TOL: ClassVar[float] = 1.0e-3
    CONSTRAINT_LOWER_TOL: ClassVar[float] = 1e-3
    UPPER_BOUND_STALL: ClassVar[int] = 10

    def __init__(self, problem: OptimizationProblem) -> None:
        """
        Args:
            problem: The GEMSEO optimization problem.
        """  # noqa: D212, D205
        self.distance_filter_ratio = None
        self.constraint_history_size = None
        self.parallel_exploration_factor = None
        self.min_step = 1
        self._milp_settings = ExtendedScipyMILP_Settings()
        self._use_scipy = False
        self.lmbd = 1e4
        self.delta_bound = inf
        self.step_decreasing_activation = 3
        self.problem = problem
        self.function_names = list(
            set(
                [
                    self.problem.objective.name,
                ]
                + [cstr.name for cstr in self.problem.constraints]
            )
        )
        self.database = self.problem.database
        self.design_space = problem.design_space
        self.message = ""
        self.n_catalogues = None
        self.n_members = None
        self.normalize_design_space = False
        self.max_iter = 1000
        self.epsilon = 1e-3
        self.posa = 1.0
        self.min_dfk = 0.0
        self.use_adaptative_convexification = False
        self.n_parallel_points = 1
        self.initial_doe = None
        self.upper_bound_stall = 10
        self.convexification_constant = 0.0
        self.max_step = 10
        self.use_bilateral_adaptation = False
        self.feasible_history_size = 1000
        self.gradient_free = False
        self._max_feasible_history_size = self.feasible_history_size
        # self.feasible_history_size = 1000
        self.infeasible_history_size = 1000
        self._max_infeasible_history_size = self.infeasible_history_size
        # self.infeasible_history_size = 1000
        self.current_step = self.max_step
        self.time_limit_milliseconds = None
        # self.current_step = self.max_step

    @staticmethod
    def _check_independent_constraint(
        constraint_slopes_hist: list[ndarray],
        alpha_hist: list[ndarray],
        constraint_hist: list[float],
        df: ndarray,
        a: ndarray,
        f: float | ndarray,
    ) -> bool:
        """Check if the constraint to be added is linearly independent of history.

        Args:
            constraint_slopes_hist: The constraint sensitivity history.
            alpha_hist: The one-hot encoding design variable history.
            constraint_hist: The constraint function history.
            df: The new constraint slope.
            a: The new alpha.
            f: The new constraint value.

        Returns:
            True when the new constraint is independent.
        """
        if len(constraint_slopes_hist):
            if len(constraint_slopes_hist[0].shape) == 1:
                jac = array(constraint_slopes_hist)
                jac_new = array([*constraint_slopes_hist, df])
            else:
                jac = concatenate(constraint_slopes_hist)
                jac_new = concatenate([*constraint_slopes_hist, atleast_2d(df)])
            if matrix_rank(jac_new) == matrix_rank(jac):
                for df_old, a_old, f_old in zip(
                    constraint_slopes_hist, alpha_hist, constraint_hist, strict=False
                ):
                    if abs(f - (f_old + df_old.dot(a - a_old))) < 1e-3:
                        return False
        return True

    def _filter_distance_history(
        self,
        slopes_hist: Iterable[ndarray],
        alpha_hist: Iterable[ndarray],
        fopt_hist: Iterable[float],
        alpha_best: ndarray | None,
        eliminated_alpha_hist: Iterable[ndarray],
        size: int,
    ) -> tuple[
        Iterable[ndarray], Iterable[ndarray], Iterable[float], Iterable[ndarray]
    ]:
        """Filter the objective function history according to distance from bestpoint.

        Take the N best points out of the history.

        Args:
            slopes_hist: The objective function slope history.
            alpha_hist: The corresponding binary variable history.
            fopt_hist:  The objective function history.
            eliminated_alpha_hist: The binary variable to be removed from milp solution.
            alpha_best: The binary variable from which distance are computed.
                If None this is deduced by alpha_hist.
            size: The total number of history points.


        Returns:
            The filtered objective function, slope and binary variable histories.
        """
        d = min(len(fopt_hist), size)
        if d > 0 and self.distance_filter_ratio is not None:
            sorted_index = argsort(array(fopt_hist))
            if alpha_best is None:
                alpha_best = array(alpha_hist)[sorted_index[0], :]
            distances = (alpha_best) @ array(alpha_best).reshape((
                len(alpha_best),
                1,
            )) - array(alpha_hist) @ array(alpha_best).reshape((
                len(alpha_best),
                1,
            )).flatten()
            sorted_index = argsort(array(distances))
            distances_sorted = distances[sorted_index][:d]
            fopt_hist = list(
                array(fopt_hist)[sorted_index][:d][
                    distances_sorted <= self.current_step * self.distance_filter_ratio
                ]
            )
            slopes_hist = list(
                array(slopes_hist)[sorted_index, :][:d][
                    distances_sorted <= self.current_step * self.distance_filter_ratio
                ]
            )
            alpha_hist = list(
                array(alpha_hist)[sorted_index, :][:d][
                    distances_sorted <= self.current_step * self.distance_filter_ratio
                ]
            )

        return slopes_hist, alpha_hist, fopt_hist, eliminated_alpha_hist

    @staticmethod
    def _filter_history(
        slopes_hist: Iterable[ndarray],
        alpha_hist: Iterable[ndarray],
        fopt_hist: Iterable[float],
        eliminated_alpha_hist: Iterable[ndarray],
        history_size: int,
    ) -> tuple[
        Iterable[ndarray], Iterable[ndarray], Iterable[float], Iterable[ndarray]
    ]:
        """Filter the objective function history to be consistent with history size.

        Take the last N points out of the history.

        Args:
            slopes_hist: The objective function slope history.
            alpha_hist: The corresponding binary variable history.
            fopt_hist:  The objective function history.
            eliminated_alpha_hist: The binary variable to be removed from milp solution.
            history_size: The number of plane to keep.

        Returns:
            The filtered objective function, slope and binary variable histories.
        """
        if len(fopt_hist) > history_size:
            if not history_size:
                fopt_hist = []
                slopes_hist = []
                alpha_hist = []
            else:
                fopt_hist = fopt_hist[-history_size:]
                slopes_hist = slopes_hist[-history_size:]
                alpha_hist = alpha_hist[-history_size:]
        return slopes_hist, alpha_hist, fopt_hist, eliminated_alpha_hist

    def _solve_milp(
        self,
        slopes_hist: Iterable[ndarray],
        alpha_hist: Iterable[ndarray],
        fopt_hist: Iterable[float],
        ineq_constr_alpha: Iterable[ndarray],
        ineq_constraint_violation_hist: Iterable[ndarray],
        ineq_constraint_violation_jac_hist: Iterable[ndarray],
        eq_constr_alpha: Iterable[ndarray],
        eq_constraint_violation_hist: Iterable[ndarray],
        eq_constraint_violation_jac_hist: Iterable[ndarray],
        eliminated_alpha: Iterable[ndarray],
        infeasible_slopes_hist: Iterable[ndarray],
        infeasible_alpha_hist: Iterable[ndarray],
        infeasible_fopt_hist: Iterable[float],
        retained_alpha: ndarray | None,
        current_step: float,
    ) -> tuple[ndarray, ndarray, bool]:
        """Solve the mixed integer linear program.

        Linearization of the objective of the NLP problem, and add the linear equality
        constraints that ensures a unique choice per element. Returns a lower bound of
        the original problem.

        Args:
            infeasible_fopt_hist: The objective value history for infeasible points.
            infeasible_alpha_hist: The binary variables history for infeasible points.
            infeasible_slopes_hist: The objective slope history for infeasible points.
            retained_alpha: The upper bound binary variable value.
            ineq_constraint_violation_hist: The history of inequality constraint
                violation.
            ineq_constraint_violation_jac_hist: The history of inequality constraint
                violation jacobian .
            eq_constraint_violation_hist: The history of equality constraint
                violation.
            eq_constraint_violation_jac_hist: The history of equality constraint
                violation jacobian .
            slopes_hist: The post-optimal sensitivity history.
            alpha_hist: The one-hot encoding design variable history.
            fopt_hist: The objective function history.
            ineq_constr_alpha: The vector of inequality alpha.
            eq_constr_alpha: The vector of equality alpha.
            current_step: The maximum step

        Returns:
            The new optimization candidate and if the candidate, the estimated
            objective function at the new candidate using the outer approximation and
            the feasibility of the new optimization candidate.
        """
        if self.use_adaptative_convexification:
            # add adaptive convexification (secant method)
            if len(alpha_hist) > 0 and len(infeasible_alpha_hist) > 0:
                total_slope_hist = self._update_sensitivities_wt_secant_method(
                    alpha_hist + infeasible_alpha_hist,
                    slopes_hist + infeasible_slopes_hist,
                    fopt_hist + infeasible_fopt_hist,
                    min_dfk=self.min_dfk,
                )
                slopes_hist = total_slope_hist[: len(alpha_hist)]
                infeasible_slopes_hist = total_slope_hist[len(alpha_hist) :]
            elif len(alpha_hist) > 1 and len(infeasible_alpha_hist) == 0:
                slopes_hist = self._update_sensitivities_wt_secant_method(
                    alpha_hist, slopes_hist, fopt_hist, min_dfk=self.min_dfk
                )
            elif len(alpha_hist) == 0 and len(infeasible_alpha_hist) > 1:
                infeasible_slopes_hist = self._update_sensitivities_wt_secant_method(
                    infeasible_alpha_hist,
                    infeasible_slopes_hist,
                    infeasible_fopt_hist,
                    min_dfk=self.min_dfk,
                )
            # if len(ineq_constr_alpha) >= 1:
            #     if isinstance(ineq_constraint_violation_hist[0], ndarray):
            #         ial = []
            #         for c, alpha in zip(ineq_constraint_violation_hist,
            #         ineq_constr_alpha):
            #             ial += [alpha] * len(c)
            #         ineq_constr_alpha = ial
            #         ineq_constraint_violation_jac_hist = list(
            #             concatenate(ineq_constraint_violation_jac_hist)
            #         )
            #         ineq_constraint_violation_hist = list(
            #             concatenate(ineq_constraint_violation_hist)
            #         )
            # if len(eq_constr_alpha) >= 1:
            #     if isinstance(eq_constraint_violation_hist[0], ndarray):
            #         eal = []
            #         for c, alpha in zip(eq_constraint_violation_hist,
            #         eq_constr_alpha):
            #             eal += [alpha] * len(c)
            #         eq_constr_alpha = eal
            #         eq_constraint_violation_jac_hist = list(
            #             concatenate(eq_constraint_violation_jac_hist)
            #         )
            #         eq_constraint_violation_hist = list(
            #             concatenate(eq_constraint_violation_hist)
            #         )
            if len(ineq_constr_alpha) > 1:
                ineq_constraint_violation_jac_hist = (
                    self._update_sensitivities_wt_secant_method(
                        ineq_constr_alpha,
                        ineq_constraint_violation_jac_hist,
                        ineq_constraint_violation_hist,
                        min_dfk=self.min_dfk,
                    )
                )
            if len(eq_constr_alpha) > 1:
                # TODO: equality constraints not taken into account in bilevel oa.
                # We should first transform any equality constraint
                # into inequality constraints with a margin.
                # Equality constraints could be removed from all the code.
                eq_constraint_violation_jac_hist = (
                    self._update_sensitivities_wt_secant_method(
                        eq_constr_alpha,
                        eq_constraint_violation_jac_hist,
                        eq_constraint_violation_hist,
                        min_dfk=0.0,
                    )
                )
        if self.posa > 1 or self.convexification_constant > 0.0:
            slopes_hist = self._update_sensitivities_posa_convexification(
                alpha_hist, slopes_hist
            )
            infeasible_slopes_hist = self._update_sensitivities_posa_convexification(
                infeasible_alpha_hist, infeasible_slopes_hist
            )
            # ineq_constraint_violation_jac_hist =
            # self._update_sensitivities_posa_convexification(
            #     ineq_constr_alpha, ineq_constraint_violation_jac_hist
            # )
            # eq_constraint_violation_jac_hist = \
            #     self._update_sensitivities_posa_convexification(
            #     eq_constr_alpha, eq_constraint_violation_jac_hist
            # )
        milp_problem = self._build_milp_problem(
            slopes_hist,
            alpha_hist,
            fopt_hist,
            ineq_constr_alpha,
            ineq_constraint_violation_hist,
            ineq_constraint_violation_jac_hist,
            eq_constr_alpha,
            eq_constraint_violation_hist,
            eq_constraint_violation_jac_hist,
            eliminated_alpha,
            infeasible_slopes_hist,
            infeasible_alpha_hist,
            infeasible_fopt_hist,
            retained_alpha,
            current_step,
        )
        optim_result = self._milp_solver.execute(
            milp_problem, **self._milp_settings.model_dump()
        )

        if optim_result.status in [0, 1]:
            alpha_opt = milp_problem.design_space.convert_array_to_dict(
                milp_problem.solution.x_opt
            )["alpha"]
            alpha_opt[alpha_opt < 0.5] = 0.0
            alpha_opt[alpha_opt >= 0.5] = 1.0
            eta_opt = milp_problem.design_space.convert_array_to_dict(
                milp_problem.solution.x_opt
            )["eta"]
            self.feasible_history_size = min(
                len(alpha_hist) + self.n_parallel_points,
                self._max_feasible_history_size,
            )
            self.infeasible_history_size = min(
                len(infeasible_alpha_hist) + self.n_parallel_points,
                self._max_infeasible_history_size,
            )
            return alpha_opt, eta_opt, True
        if optim_result.status == 2:
            milp_problem = self._build_relaxed_milp_problem(
                slopes_hist,
                alpha_hist,
                fopt_hist,
                ineq_constr_alpha,
                ineq_constraint_violation_hist,
                ineq_constraint_violation_jac_hist,
                eq_constr_alpha,
                eq_constraint_violation_hist,
                eq_constraint_violation_jac_hist,
                eliminated_alpha,
                infeasible_slopes_hist,
                infeasible_alpha_hist,
                infeasible_fopt_hist,
                retained_alpha,
            )

            optim_result = self._milp_solver.execute(
                milp_problem, **self._milp_settings.model_dump()
            )

            if optim_result.status in [0, 1]:
                solution = milp_problem.design_space.convert_array_to_dict(
                    milp_problem.solution.x_opt
                )
                alpha_opt = solution["alpha"]
                alpha_opt[alpha_opt < 0.5] = 0.0
                alpha_opt[alpha_opt >= 0.5] = 1.0
                eta_opt = solution["eta"]
                delta_opt = solution["delta"]
                if not self.gradient_free:
                    self.delta_bound = max(delta_opt, 0.0)
                return alpha_opt, eta_opt, True
            return retained_alpha, inf, False
        return None

    def _build_milp_problem(
        self,
        slopes_hist: Iterable[ndarray],
        alpha_hist: Iterable[ndarray],
        fopt_hist: Iterable[float],
        ineq_constr_alpha: Iterable[ndarray],
        ineq_constraint_violation_hist: Iterable[ndarray],
        ineq_constraint_violation_jac_hist: Iterable[ndarray],
        eq_constr_alpha: Iterable[ndarray],
        eq_constraint_violation_hist: Iterable[ndarray],
        eq_constraint_violation_jac_hist: Iterable[ndarray],
        eliminated_alpha: Iterable[ndarray],
        infeasible_slopes_hist: Iterable[ndarray],
        infeasible_alpha_hist: Iterable[ndarray],
        infeasible_fopt_hist: Iterable[float],
        retained_alpha: ndarray | None,
        current_step: float,
    ) -> OptimizationProblem:
        """Build the MILP problem without relaxation.

        Args:
            infeasible_fopt_hist: The objective value history for infeasible points.
            infeasible_alpha_hist: The binary variables history for infeasible points.
            infeasible_slopes_hist: The objective slope history for infeasible points.
            retained_alpha: The upper bound binary variable value.
            ineq_constraint_violation_hist: The history of inequality constraint
                violation.
            ineq_constraint_violation_jac_hist: The history of inequality constraint
                violation jacobian.
            eq_constraint_violation_hist: The history of equality constraint
                violation.
            eq_constraint_violation_jac_hist: The history of equality constraint
                violation jacobian.
            slopes_hist: The post-optimal sensitivity history.
            alpha_hist: The one-hot encoding design variable history.
            fopt_hist: The objective function history.
            ineq_constr_alpha: The vector of inequality alpha.
            eq_constr_alpha: The vector of equality alpha.
            current_step: The maximum iteration step.

        Returns:
            The optimization problem.
        """
        design_space = DesignSpace()
        design_space.add_variable(
            "alpha",
            lower_bound=self.problem.design_space.get_lower_bounds(),
            upper_bound=self.problem.design_space.get_upper_bounds(),
            value=retained_alpha,
            type_=design_space.DesignVariableType.INTEGER,
            size=len(retained_alpha),
        )
        if len(fopt_hist) > 0:
            design_space.add_variable(
                "eta", lower_bound=-inf, upper_bound=inf, value=min(fopt_hist)
            )
        else:
            design_space.add_variable("eta", lower_bound=-inf, upper_bound=inf, value=0)
        eta_id = design_space.get_variables_indexes(["eta"])
        coeffs = zeros(len(retained_alpha) + 1)
        coeffs[eta_id] = 1.0
        # Optimization functions
        args = ["alpha", "eta"]
        problem = OptimizationProblem(design_space, is_linear=True)
        problem.objective = MDOLinearFunction(
            coeffs, "eta", MDOFunction.FunctionType.OBJ, input_names=args, expr=""
        )

        # Constraint: The sum of the alpha[i] is equal to 1.
        one_hot_encoded_vars = sum(
            self.n_members[variable_name]
            * (0 if self.design_space.hypercube[variable_name] else 1)
            for variable_name in self.design_space.variable_names
        )
        if one_hot_encoded_vars:
            alpha_sum_a = zeros((
                one_hot_encoded_vars,
                len(retained_alpha) + 1,
            ))
            row_id = 0
            begin_col = 0
            for variable_name in self.design_space.variable_names:
                if not self.design_space.hypercube[variable_name]:
                    for _i in range(self.n_members[variable_name]):
                        end_col = begin_col + self.n_catalogues[variable_name]
                        alpha_sum_a[row_id, begin_col:end_col] = ones(
                            self.n_catalogues[variable_name]
                        )
                        begin_col = end_col
                        row_id += 1
            problem.add_constraint(
                MDOLinearFunction(
                    alpha_sum_a,
                    "unit_sum_constraints",
                    input_names=args,
                    expr="",
                ),
                value=1.0,
                constraint_type=MDOFunction.ConstraintType.EQ,
            )

        # Constraint A: Hyperplans tangeants en dessous de l'objectif
        slopes = slopes_hist + infeasible_slopes_hist
        if len(slopes):
            oa_a = concatenate(
                (
                    concatenate(slopes),
                    -ones((len(slopes), 1)),
                ),
                axis=1,
            )  # -1 * eta
            oa_b_u = diag(
                (concatenate(slopes) @ array(alpha_hist + infeasible_alpha_hist).T)
                - array(fopt_hist + infeasible_fopt_hist)
            ).flatten()  # f_i + nabla_f_i (alpha - alpha_i)

            for i, (coef, value) in enumerate(zip(oa_a, oa_b_u, strict=False)):
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"objective outer approximation {i}",
                        input_names=args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )

        # Constraint B
        if len(ineq_constraint_violation_hist):
            if len(ineq_constraint_violation_jac_hist[0].shape) == 1:
                ineq_a = concatenate(
                    (
                        concatenate(ineq_constraint_violation_jac_hist),
                        zeros((len(ineq_constraint_violation_jac_hist), 1)),
                    ),
                    axis=1,
                )
                ineq_b_u = (
                    diag(
                        concatenate(ineq_constraint_violation_jac_hist)
                        @ array(ineq_constr_alpha).T
                    )
                    - array(ineq_constraint_violation_hist)
                ).flatten()
            else:
                ineq_jac = concatenate(ineq_constraint_violation_jac_hist)
                ineq_a = concatenate(
                    (
                        ineq_jac,
                        zeros((ineq_jac.shape[0], 1)),
                    ),
                    axis=1,
                )
                ineq_b_u = concatenate([
                    jac @ a.T - f
                    for jac, a, f in zip(
                        ineq_constraint_violation_jac_hist,
                        ineq_constr_alpha,
                        ineq_constraint_violation_hist,
                        strict=False,
                    )
                ])

            for i, (coef, value) in enumerate(zip(ineq_a, ineq_b_u, strict=False)):
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"inequality constraint  {i}",
                        input_names=args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )

        # Constraint B: equality with ineq and tol
        if len(eq_constraint_violation_jac_hist):
            if len(eq_constraint_violation_jac_hist[0].shape) == 1:
                eq_a = concatenate(
                    (
                        concatenate(eq_constraint_violation_jac_hist),
                        zeros((len(eq_constraint_violation_jac_hist), 1)),
                    ),
                    axis=1,
                )
                eq_b_u = (
                    diag(
                        concatenate(eq_constraint_violation_jac_hist)
                        @ array(eq_constr_alpha).T
                    )
                    - array(eq_constraint_violation_hist)
                ).flatten()
            else:
                eq_jac = concatenate(eq_constraint_violation_jac_hist)
                eq_a = concatenate(
                    (
                        eq_jac,
                        zeros((eq_jac.shape[0], 1)),
                    ),
                    axis=1,
                )
                eq_b_u = concatenate([
                    jac @ a.T - f
                    for jac, a, f in zip(
                        eq_constraint_violation_jac_hist,
                        eq_constr_alpha,
                        eq_constraint_violation_hist,
                        strict=False,
                    )
                ])
            i = 0
            for coef, value in zip(eq_a, eq_b_u, strict=False):
                i += 1
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"equality constraint  {i}",
                        input_names=args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.EQ,
                )

        # Constraint D: Elimination of all unfeasible apha_s
        if len(eliminated_alpha):
            infeasible_a = concatenate(
                (
                    atleast_2d(array(eliminated_alpha)),
                    zeros((len(eliminated_alpha), 1)),
                ),
                axis=1,
            )
            infeasible_b_u = (
                np_sum(atleast_2d(array(eliminated_alpha) ** 2), axis=1) - 1
            )
            f0 = problem.objective.evaluate(problem.design_space.get_current_value())
            for i, (coef, value) in enumerate(
                zip(infeasible_a, infeasible_b_u, strict=False)
            ):
                if self.parallel_exploration_factor > 0.0:
                    c = np_sum(coef**2) - current_step
                    scaling = (
                        self.parallel_exploration_factor * f0 / float(current_step)
                    )
                    penalty = MDOLinearFunction(
                        scaling * coef,
                        f"penalty {i}",
                        MDOFunction.ConstraintType.INEQ,
                        input_names=args,
                        expr="",
                        value_at_zero=-scaling * (c),
                    )
                    problem.objective += penalty
                    problem.objective = problem.objective.linear_approximation(
                        x_vect=problem.design_space.get_current_value(),
                        name=problem.objective.name,
                    )
                    problem.objective.expr = ""
                    problem.objective.args = args
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"eliminated solution  {i}",
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )

        # Constraint E
        if retained_alpha is not None:
            weighted_retained_alpha = self.__apply_weights(retained_alpha)
            trust_region_a = concatenate([weighted_retained_alpha, [0]])
            trust_region_b_l = weighted_retained_alpha.sum() - current_step

            problem.add_constraint(
                MDOLinearFunction(
                    trust_region_a,
                    "trust region",
                    input_names=args,
                    expr="",
                ),
                value=trust_region_b_l,
                constraint_type=MDOFunction.ConstraintType.INEQ,
                positive=True,
            )

        return problem

    def __apply_weights(self, alpha: ndarray[float]) -> ndarray[float]:
        r"""Apply catalogue weights to a one-hot encoding for distance computation.

        The return value is the concatenation of the vectors
        $\begin{bmatrix}
        w_{i, 1} \, \alpha_{ij_i, 1} & \cdots &
        w_{i, n^{(i)}_{\mathrm{catalogue}}} \,
        \alpha_{ij_i, n^{(i)}_{\mathrm{catalogue}}}
        \end{bmatrix}$
        where:

        * $i$ indexes the categorical variables,
        * $j_i$ indexes the components of the $i$-th categorical variable,
        * $\begin{bmatrix}
          w_{i, 1} & \cdots & w_{i, n^{(i)}_{\mathrm{catalogue}}}
          \end{bmatrix}$
          are the weights of the catalogue values of the $i$-th categorical variable,
        * $\begin{bmatrix}
          \alpha_{ij_i, 1} & \cdots & \alpha_{ij_i, n^{(i)}_{\mathrm{catalogue}}}
          \end{bmatrix}$
          is the one-hot encoding of the $j_i$-th component
          of the $i$-th categorical variable.

        Args:
            alpha: The one-hot encoding.

        Returns:
            The weighted one-hot encoding.
        """
        return alpha * concatenate([
            tile(self.design_space.get_catalogue_weights(name), self.n_members[name])
            for name in self.design_space.categorical_variables
        ])

    def _build_relaxed_milp_problem(
        self,
        slopes_hist: Iterable[ndarray],
        alpha_hist: Iterable[ndarray],
        fopt_hist: Iterable[float],
        ineq_constr_alpha: Iterable[ndarray],
        ineq_constraint_violation_hist: Iterable[ndarray],
        ineq_constraint_violation_jac_hist: Iterable[ndarray],
        eq_constr_alpha: Iterable[ndarray],
        eq_constraint_violation_hist: Iterable[ndarray],
        eq_constraint_violation_jac_hist: Iterable[ndarray],
        eliminated_alpha: Iterable[ndarray],
        infeasible_slopes_hist: Iterable[ndarray],
        infeasible_alpha_hist: Iterable[ndarray],
        infeasible_fopt_hist: Iterable[float],
        retained_alpha: ndarray | None,
    ) -> OptimizationProblem:
        """Build the relaxed MILP problem.

        Args:
            infeasible_fopt_hist: The objective value history for infeasible points.
            infeasible_alpha_hist: The binary variables history for infeasible points.
            infeasible_slopes_hist: The objective slope history for infeasible points.
            retained_alpha: The upper bound binary variable value.
            ineq_constraint_violation_hist: The history of inequality constraint
                violation.
            ineq_constraint_violation_jac_hist: The history of inequality constraint
                violation jacobian .
            eq_constraint_violation_hist: The history of equality constraint
                violation.
            eq_constraint_violation_jac_hist: The history of equality constraint
                violation jacobian .
            slopes_hist: The post-optimal sensitivity history.
            alpha_hist: The one-hot encoding design variable history.
            fopt_hist: The objective function history.
            ineq_constr_alpha: The vector of inequality alpha.
            eq_constr_alpha: The vector of equality alpha.

        Returns:
            The optimization problem
        """
        design_space = DesignSpace()
        design_space.add_variable(
            "alpha",
            lower_bound=self.problem.design_space.get_lower_bounds(),
            upper_bound=self.problem.design_space.get_upper_bounds(),
            value=retained_alpha,
            type_=design_space.DesignVariableType.INTEGER,
            size=len(retained_alpha),
        )
        if len(fopt_hist) > 0:
            design_space.add_variable(
                "eta", lower_bound=-inf, upper_bound=inf, value=min(fopt_hist)
            )
        else:
            design_space.add_variable("eta", lower_bound=-inf, upper_bound=inf, value=0)
        design_space.add_variable(
            "delta", lower_bound=0.0, upper_bound=self.delta_bound, value=0
        )
        eta_id = design_space.get_variables_indexes(["eta"])
        delta_id = design_space.get_variables_indexes(["delta"])
        coeffs = zeros(len(retained_alpha) + 2)
        coeffs[eta_id] = 1.0
        coeffs[delta_id] = self.lmbd
        # Optimization functions
        args = ["alpha", "eta", "delta"]
        problem = OptimizationProblem(design_space, is_linear=True)
        problem.objective = MDOLinearFunction(
            coeffs,
            f"eta + {self.lmbd}*delta",
            MDOFunction.FunctionType.OBJ,
            args,
            expr="",
        )
        one_hot_encoded_vars = sum(
            self.n_members[key] * (0 if self.design_space.hypercube[key] else 1)
            for key in self.design_space.variable_names
        )
        if one_hot_encoded_vars >= 1:
            alpha_sum_a = zeros((
                one_hot_encoded_vars,
                len(retained_alpha) + 2,
            ))
            row_id = 0
            begin_col = 0
            for key in self.design_space.variable_names:
                if not self.design_space.hypercube[key]:
                    for _i in range(self.n_members[key]):
                        end_col = begin_col + self.n_catalogues[key]
                        alpha_sum_a[row_id, begin_col:end_col] = ones(
                            self.n_catalogues[key]
                        )
                        begin_col = end_col
                        row_id += 1
            problem.add_constraint(
                MDOLinearFunction(
                    alpha_sum_a,
                    "unit_sum_constraints",
                    MDOFunction.ConstraintType.EQ,
                    args,
                    expr="",
                ),
                value=1.0,
                constraint_type=MDOFunction.ConstraintType.EQ,
            )
        if len(slopes_hist + infeasible_slopes_hist) > 0:
            oa_a = concatenate(
                (
                    concatenate(slopes_hist + infeasible_slopes_hist),
                    -ones((len(slopes_hist + infeasible_slopes_hist), 1)),
                    zeros((len(slopes_hist + infeasible_slopes_hist), 1)),
                ),
                axis=1,
            )
            oa_b_u = (
                diag(
                    concatenate(slopes_hist + infeasible_slopes_hist)
                    @ array(alpha_hist + infeasible_alpha_hist).T
                )
                - array(fopt_hist + infeasible_fopt_hist)
            ).flatten()
            for i, (coef, value) in enumerate(zip(oa_a, oa_b_u, strict=False)):
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"objective outer approximation {i + 1}",
                        MDOFunction.ConstraintType.INEQ,
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )
        if len(ineq_constraint_violation_hist) > 0:
            if len(ineq_constraint_violation_jac_hist[0].shape) == 1:
                ineq_a = concatenate(
                    (
                        concatenate(ineq_constraint_violation_jac_hist),
                        zeros((len(ineq_constraint_violation_jac_hist), 1)),
                        -ones((len(ineq_constraint_violation_jac_hist), 1)),
                    ),
                    axis=1,
                )
                ineq_b_u = (
                    concatenate(ineq_constraint_violation_jac_hist)
                    @ array(ineq_constr_alpha).T
                    - array(ineq_constraint_violation_hist)
                ).flatten()
            else:
                ineq_jac = concatenate(ineq_constraint_violation_jac_hist)
                ineq_a = concatenate(
                    (
                        ineq_jac,
                        zeros((ineq_jac.shape[0], 1)),
                        -ones((ineq_jac.shape[0], 1)),
                    ),
                    axis=1,
                )
                ineq_b_u = concatenate([
                    jac @ a.T - f
                    for jac, a, f in zip(
                        ineq_constraint_violation_jac_hist,
                        ineq_constr_alpha,
                        ineq_constraint_violation_hist,
                        strict=False,
                    )
                ])
            i = 0
            for coef, value in zip(ineq_a, ineq_b_u, strict=False):
                i += 1
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"inequality constraint  {i}",
                        MDOFunction.ConstraintType.INEQ,
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )
        if len(eq_constraint_violation_jac_hist) > 0:
            if len(eq_constraint_violation_jac_hist[0].shape) == 1:
                eq_a = concatenate(
                    (
                        concatenate(eq_constraint_violation_jac_hist),
                        zeros((len(eq_constraint_violation_jac_hist), 1)),
                        -ones((len(eq_constraint_violation_jac_hist), 1)),
                    ),
                    axis=1,
                )
                eq_a2 = concatenate(
                    (
                        concatenate(eq_constraint_violation_jac_hist),
                        zeros((len(eq_constraint_violation_jac_hist), 1)),
                        ones((len(eq_constraint_violation_jac_hist), 1)),
                    ),
                    axis=1,
                )
                eq_b_u = (
                    concatenate(eq_constraint_violation_jac_hist)
                    @ array(eq_constr_alpha).T
                    - array(eq_constraint_violation_hist)
                ).flatten()
            else:
                eq_jac = concatenate(eq_constraint_violation_jac_hist)
                eq_a2 = concatenate(
                    (
                        eq_jac,
                        zeros((eq_jac.shape[0], 1)),
                        ones((eq_jac.shape[0], 1)),
                    ),
                    axis=1,
                )
                eq_a = concatenate(
                    (
                        eq_jac,
                        zeros((eq_jac.shape[0], 1)),
                        -ones((eq_jac.shape[0], 1)),
                    ),
                    axis=1,
                )
                eq_b_u = concatenate([
                    jac @ a.T - f
                    for jac, a, f in zip(
                        eq_constraint_violation_jac_hist,
                        eq_constr_alpha,
                        eq_constraint_violation_hist,
                        strict=False,
                    )
                ])
            i = 0
            for coef, value in zip(eq_a, eq_b_u, strict=False):
                i += 1
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"equality constraint  relaxed neg   {i}",
                        MDOFunction.ConstraintType.INEQ,
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )
            i = 0
            for coef, value in zip(eq_a2, eq_b_u, strict=False):
                i += 1
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"equality constraint  relaxed pos   {i}",
                        MDOFunction.ConstraintType.INEQ,
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                    positive=True,
                )
        if len(eliminated_alpha) > 0:
            infeasible_a = concatenate(
                (array(eliminated_alpha), zeros((len(eliminated_alpha), 2))), axis=1
            )
            infeasible_b_u = np_sum(array(eliminated_alpha) ** 2, axis=1) - 1
            i = 0
            for coef, value in zip(infeasible_a, infeasible_b_u, strict=False):
                i += 1
                problem.add_constraint(
                    MDOLinearFunction(
                        coef,
                        f"eliminated solution  {i}",
                        MDOFunction.ConstraintType.INEQ,
                        args,
                        expr="",
                    ),
                    value=value,
                    constraint_type=MDOFunction.ConstraintType.INEQ,
                )
        if retained_alpha is not None:
            weighted_retained_alpha = self.__apply_weights(retained_alpha)
            trust_region_a = concatenate((weighted_retained_alpha, [0] * 2))
            trust_region_b_l = atleast_1d(
                np_sum(weighted_retained_alpha) - self.current_step
            )
            problem.add_constraint(
                MDOLinearFunction(
                    trust_region_a,
                    "trust region",
                    MDOFunction.ConstraintType.INEQ,
                    args,
                    expr="",
                ),
                value=trust_region_b_l[0],
                constraint_type=MDOFunction.ConstraintType.INEQ,
                positive=True,
            )
        return problem

    def __decrease_step_size(self) -> None:
        """Decrease the current step."""
        self.current_step = max(self.current_step * 0.7, self.min_step)

    def _update_sensitivities_posa_convexification(
        self,
        alpha_hist: Iterable[ndarray],
        slopes_hist: Iterable[ndarray],
    ) -> Iterable[ndarray]:
        """POSA and alpha underestimator approach.

        Args:
            alpha_hist: The history of feasible design candidate.
            slopes_hist: The history of objective function jacobians.
        """
        modified_slopes = []
        for alpha_k, slopes_k in zip(
            alpha_hist,
            slopes_hist,
            strict=False,
        ):
            slopes_k = slopes_k.flatten()
            posa_vect = []
            pb_size = len(self.design_space.get_current_value())
            for i in range(pb_size):
                if ((slopes_k[i] > 0) & (alpha_k[i].real == 0)) or (
                    (slopes_k[i] < 0) & (alpha_k[i].real == 1)
                ):
                    posa_vect.append(1)
                else:
                    posa_vect.append(self.posa)
            scaling = []
            for key in self.design_space.variable_names:
                scaling += (
                    [1.0 / float(self.n_members[key])]
                    * self.n_catalogues[key]
                    * self.n_members[key]
                )
            modified_slopes.append(
                atleast_2d(
                    array([
                        posa_vect[i]
                        * (
                            slopes_k[i]
                            + self.convexification_constant
                            * scaling[i]
                            * (2 * alpha_k[i].real - 1)
                        )
                        for i in range(pb_size)
                    ])
                )
            )
        return modified_slopes

    def _update_sensitivities_wt_secant_method(
        self,
        alpha_hist: Iterable[ndarray],
        slopes_hist: Iterable[ndarray],
        fopt_hist: Iterable[ndarray],
        min_dfk: float,
    ) -> Iterable[ndarray]:
        """Adaptive convexivication.

        Args:
            alpha_hist: The history of feasible design candidate.
            slopes_hist: The history of objective function jacobians.
            fopt_hist: The history of objective function.
            min_dfk: The convexity margin.
        """
        min_delta = 0.0
        delta_alphas = []
        deltas = []
        for alpha_k, f_k, slope_k in zip(
            alpha_hist, fopt_hist, slopes_hist, strict=False
        ):
            df_k = array(fopt_hist) - f_k
            delta_alpha = array(alpha_hist).T - tile(alpha_k, (len(alpha_hist), 1)).T
            delta_alphas.append(delta_alpha)
            l_df_k = slope_k.dot(delta_alpha)
            rhs = l_df_k - df_k + min_dfk
            if not self.use_bilateral_adaptation:
                rhs[rhs < min_delta] = min_delta
            delta, _, _, _ = lstsq(
                delta_alpha.T.dot(delta_alpha), rhs.flatten(), rcond=None
            )
            deltas.append(delta)
        corrected_slopes_hist = []
        for slope_k, delta_alpha, delta in zip(
            slopes_hist, delta_alphas, deltas, strict=False
        ):
            corrected_slopes_hist.append(slope_k - delta_alpha.dot(delta).flatten())
        return corrected_slopes_hist

    def __evaluate_termination_criteria(
        self, alpha_hist: list[ndarray], iteration: int, i_k: ndarray
    ) -> bool:
        """Termination criteria.

        Args:
            alpha_hist: The categorical variable history.
            iteration: The number of iterations.
            i_k: Current iteration design points.

        Returns:
            True if in all next iteration points are already evaluated.
        """
        previously_computed = not self._is_previously_computed(i_k)
        return (
            len(alpha_hist) <= 2 or (previously_computed)
        ) and iteration < self.max_iter

    def _is_previously_computed(self, i_k: ndarray) -> bool:
        """Test if one of the new proposed solution was previously computed.

        Args:
            i_k: The new candidate solutions.

        Returns:
            Whether one of the new proposed solution were previously computed.
        """
        return any(alpha in self.problem.database for alpha in i_k)

    @staticmethod
    def __get_active_milp_constraints(
        slopes_hist: ndarray,
        alpha_hist: ndarray,
        fopt_hist: ndarray,
        eta_opt: ndarray,
        alpha_opt: ndarray,
    ) -> ndarray:
        """Return the active constraints in the MILP problem.

        Args:
            slopes_hist: The history of post optimal sensitivities.
            alpha_hist: The history of categorical one hot encoding.
            fopt_hist: The master problem objective value history.
            eta_opt: The eta variable history.
            alpha_opt: The current optimal alpha.

        Returns:
            The active constraints.
        """
        all_cst = array([])
        for slopes_k, alpha_k, fopt_k in zip(
            slopes_hist, alpha_hist, fopt_hist, strict=False
        ):
            all_cst = append(
                all_cst, fopt_k + dot(slopes_k, alpha_opt - alpha_k) - eta_opt
            )
        k_bool = isclose(all_cst, zeros(len(all_cst)))
        active_constraints = where(k_bool)[0]
        message = "MILP : active constraints are " + str(active_constraints)
        LOGGER.info(message)

        return active_constraints

    def __iterate(self, alpha0: ndarray) -> tuple[ndarray, float]:
        """Run the optimization algorithm.

        Args:
            alpha0: The initial one-hot encoding point.

        Returns:
            The optimum one-hot encoding point and its objective value.
        """
        slopes_nosum_hist = []
        alpha_hist = []
        fopt_hist = []
        eliminated_alpha = []
        inequality_constraints_alpha = []
        inequality_constraint_violation_hist = []
        inequality_constraint_violation_jac_hist = []
        equality_constraints_alpha = []
        equality_constraint_violation_hist = []
        equality_constraint_violation_jac_hist = []
        infeasible_slopes_nosum_hist = []
        infeasible_alpha_hist = []
        infeasible_fopt_hist = []
        upper_bound_alpha = alpha0
        iteration = 1
        stall_counter = 0
        upper_bound = inf
        i_k = self.initial_doe
        self.current_step = self.max_step
        while self.__evaluate_termination_criteria(alpha_hist, iteration, i_k):
            self.problem.evaluation_counter.current = iteration
            i_iteration = f"iteration {iteration}"
            LOGGER.info(i_iteration)
            upper_bound_old = upper_bound
            self._execute_doe(i_k)
            upper_bound_alpha_old = upper_bound_alpha
            database = self.problem.database
            for alpha in i_k:
                out = {
                    func_name: database.get_function_value(func_name, alpha)
                    for func_name in self.function_names
                }
                if not self.gradient_free:
                    out_jac = {
                        func_name: atleast_2d(
                            database.get_function_value("@" + func_name, alpha)
                        )
                        for func_name in self.function_names
                    }
                else:
                    out_jac = {
                        func_name: zeros((len(atleast_1d(out[func_name])), len(alpha)))
                        for func_name in self.function_names
                    }
                fopt = out[self.problem.objective.name]
                if fopt is None:
                    LOGGER.error("CustomDOE execution did not run correctly.")
                    LOGGER.error("The database was not correctly updated.")
                    break
                feasible = self._is_point_feasible(out)
                (
                    inequality_constraints_alpha,
                    inequality_constraint_violation_hist,
                    inequality_constraint_violation_jac_hist,
                    equality_constraints_alpha,
                    equality_constraint_violation_hist,
                    equality_constraint_violation_jac_hist,
                ) = self._deal_with_constraints(
                    alpha,
                    equality_constraint_violation_hist,
                    equality_constraint_violation_jac_hist,
                    equality_constraints_alpha,
                    inequality_constraint_violation_hist,
                    inequality_constraint_violation_jac_hist,
                    inequality_constraints_alpha,
                    out,
                    out_jac,
                )
                slopes_nosum = out_jac[self.problem.objective.name]
                if feasible:
                    (
                        alpha_hist,
                        fopt_hist,
                        infeasible_alpha_hist,
                        infeasible_fopt_hist,
                        infeasible_slopes_nosum_hist,
                        slopes_nosum_hist,
                        upper_bound,
                        upper_bound_alpha,
                        eliminated_alpha,
                    ) = self._deal_with_feasible_points(
                        alpha,
                        alpha_hist,
                        fopt,
                        fopt_hist,
                        infeasible_alpha_hist,
                        infeasible_fopt_hist,
                        infeasible_slopes_nosum_hist,
                        slopes_nosum,
                        slopes_nosum_hist,
                        eliminated_alpha,
                    )
                else:
                    if all(upper_bound_alpha == alpha0):
                        alpha_best = alpha
                    else:
                        alpha_best = upper_bound_alpha
                    (
                        infeasible_alpha_hist,
                        infeasible_fopt_hist,
                        infeasible_slopes_nosum_hist,
                        eliminated_alpha,
                    ) = self._deal_with_infeasible_points(
                        alpha,
                        fopt,
                        infeasible_alpha_hist,
                        infeasible_fopt_hist,
                        infeasible_slopes_nosum_hist,
                        slopes_nosum,
                        eliminated_alpha,
                        alpha_best,
                    )
                    self.__save_state(
                        alpha, out, inf, fopt, -inf, iteration, alpha_best
                    )
                    if iteration == 1:
                        n_infeasible_solutions_counter = 0
                        while not feasible:
                            if n_infeasible_solutions_counter > self.max_iter:
                                LOGGER.warning(
                                    "There can't be any feasible solution..."
                                )
                                break
                            n_infeasible_solutions_counter += 1
                            alphaold = alpha
                            if all(upper_bound_alpha == alpha0):
                                alpha_best = alpha
                            else:
                                alpha_best = upper_bound_alpha
                            alpha, _, _ = self._solve_milp(
                                slopes_nosum_hist,
                                alpha_hist,
                                fopt_hist,
                                inequality_constraints_alpha,
                                inequality_constraint_violation_hist,
                                inequality_constraint_violation_jac_hist,
                                equality_constraints_alpha,
                                equality_constraint_violation_hist,
                                equality_constraint_violation_jac_hist,
                                eliminated_alpha,
                                infeasible_slopes_nosum_hist,
                                infeasible_alpha_hist,
                                infeasible_fopt_hist,
                                alpha_best,
                                current_step=self.current_step,
                            )
                            if self._is_previously_computed(atleast_2d(alpha)):
                                eliminated_alpha.append(alpha)
                                alpha, _, _ = self._solve_milp(
                                    slopes_nosum_hist,
                                    alpha_hist,
                                    fopt_hist,
                                    inequality_constraints_alpha,
                                    inequality_constraint_violation_hist,
                                    inequality_constraint_violation_jac_hist,
                                    equality_constraints_alpha,
                                    equality_constraint_violation_hist,
                                    equality_constraint_violation_jac_hist,
                                    eliminated_alpha,
                                    infeasible_slopes_nosum_hist,
                                    infeasible_alpha_hist,
                                    infeasible_fopt_hist,
                                    alpha,
                                    current_step=self.current_step,
                                )

                            if self.__check_trust_region_border(alpha, alphaold):
                                self.__increase_step_size()

                            self._execute_doe(atleast_2d(alpha))
                            out = {
                                func_name: database.get_function_value(func_name, alpha)
                                for func_name in self.function_names
                            }
                            if not self.gradient_free:
                                out_jac = {
                                    func_name: atleast_2d(
                                        database.get_function_value(
                                            "@" + func_name, alpha
                                        )
                                    )
                                    for func_name in self.function_names
                                }
                            else:
                                out_jac = {
                                    func_name: zeros((
                                        len(atleast_1d(out[func_name])),
                                        len(alpha),
                                    ))
                                    for func_name in self.function_names
                                }
                            fopt = out[self.problem.objective.name]
                            if fopt is None:
                                LOGGER.error(
                                    "CustomDOE execution did not run correctly."
                                )
                                LOGGER.error("The database was not correctly updated.")
                                break
                            feasible = self._is_point_feasible(out)

                            (
                                inequality_constraints_alpha,
                                inequality_constraint_violation_hist,
                                inequality_constraint_violation_jac_hist,
                                equality_constraints_alpha,
                                equality_constraint_violation_hist,
                                equality_constraint_violation_jac_hist,
                            ) = self._deal_with_constraints(
                                alpha,
                                equality_constraint_violation_hist,
                                equality_constraint_violation_jac_hist,
                                equality_constraints_alpha,
                                inequality_constraint_violation_hist,
                                inequality_constraint_violation_jac_hist,
                                inequality_constraints_alpha,
                                out,
                                out_jac,
                            )
                            slopes_nosum = out_jac[self.problem.objective.name]
                            if feasible:
                                (
                                    alpha_hist,
                                    fopt_hist,
                                    infeasible_alpha_hist,
                                    infeasible_fopt_hist,
                                    infeasible_slopes_nosum_hist,
                                    slopes_nosum_hist,
                                    upper_bound,
                                    upper_bound_alpha,
                                    eliminated_alpha,
                                ) = self._deal_with_feasible_points(
                                    alpha,
                                    alpha_hist,
                                    fopt,
                                    fopt_hist,
                                    infeasible_alpha_hist,
                                    infeasible_fopt_hist,
                                    infeasible_slopes_nosum_hist,
                                    slopes_nosum,
                                    slopes_nosum_hist,
                                    eliminated_alpha,
                                )
                                i_k = concatenate((i_k, atleast_2d(alpha)))
                            else:
                                if all(upper_bound_alpha == alpha0):
                                    alpha_best = alpha
                                else:
                                    alpha_best = upper_bound_alpha
                                (
                                    infeasible_alpha_hist,
                                    infeasible_fopt_hist,
                                    infeasible_slopes_nosum_hist,
                                    eliminated_alpha,
                                ) = self._deal_with_infeasible_points(
                                    alpha,
                                    fopt,
                                    infeasible_alpha_hist,
                                    infeasible_fopt_hist,
                                    infeasible_slopes_nosum_hist,
                                    slopes_nosum,
                                    eliminated_alpha,
                                    alpha_best,
                                )
                                self._deal_with_infeasible_point_constraints(
                                    alpha,
                                    inequality_constraint_violation_hist,
                                    inequality_constraint_violation_jac_hist,
                                    inequality_constraints_alpha,
                                    out,
                                    out_jac,
                                )
                                self.__save_state(
                                    alpha,
                                    out,
                                    inf,
                                    fopt,
                                    -inf,
                                    iteration,
                                    alpha_best,
                                )

            old_iteration = i_k
            if upper_bound_old - upper_bound == 0.0:
                stall_counter += 1
                LOGGER.info("MILP : Upper Bound stalling.")
                msg = (
                    f"MILP : Stalling iterations: "
                    f"{stall_counter}/{self.upper_bound_stall}."
                )
                LOGGER.info(msg)
                if (
                    stall_counter >= self.step_decreasing_activation
                    and stall_counter % self.step_decreasing_activation == 0
                ):
                    self.__decrease_step_size()
            elif iteration > 1 and upper_bound_old - upper_bound > 0.0:
                stall_counter = 0
                LOGGER.info("MILP : Upper Bound improving.")
                if self.__check_trust_region_border(
                    upper_bound_alpha_old, upper_bound_alpha
                ):
                    self.__increase_step_size()
                msg = (
                    f"MILP : Upper Bound improvement: {upper_bound_old - upper_bound}."
                )
                LOGGER.info(msg)
            i_k = []
            eta_opt = inf
            if fopt is None:
                if len(fopt_hist) + len(infeasible_fopt_hist) >= self.max_iter:
                    LOGGER.info("Maximum function call reached.")
                else:
                    LOGGER.info("Error evaluating functions.")
                break
            for _k_trade in range(self.n_parallel_points):
                if self.n_parallel_points > 1:
                    current_steps = geomspace(
                        max(self.current_step / 2, self.min_step),
                        self.current_step,
                        num=self.n_parallel_points,
                    )
                    current_step = current_steps[_k_trade]
                else:
                    current_step = self.current_step
                alpha_opt, eta_opt_, is_feasible = self._solve_milp(
                    slopes_nosum_hist,
                    alpha_hist,
                    fopt_hist,
                    inequality_constraints_alpha,
                    inequality_constraint_violation_hist,
                    inequality_constraint_violation_jac_hist,
                    equality_constraints_alpha,
                    equality_constraint_violation_hist,
                    equality_constraint_violation_jac_hist,
                    i_k + eliminated_alpha,
                    infeasible_slopes_nosum_hist,
                    infeasible_alpha_hist,
                    infeasible_fopt_hist,
                    upper_bound_alpha,
                    current_step=current_step,
                )
                if not is_feasible:
                    break
                while self._is_previously_computed(atleast_2d(alpha_opt)):
                    if len(eliminated_alpha) > 1:
                        list_np_arrays = array(eliminated_alpha)
                        if np_any(np_any(alpha_opt == list_np_arrays, axis=1)):
                            eliminated_alpha.append(alpha_opt)
                        else:
                            break
                    elif len(eliminated_alpha) == 1:
                        if not np_all(eliminated_alpha == alpha_opt):
                            eliminated_alpha.append(alpha_opt)
                        else:
                            break
                    else:
                        eliminated_alpha.append(alpha_opt)
                    alpha_opt, eta_opt_, is_feasible = self._solve_milp(
                        slopes_nosum_hist,
                        alpha_hist,
                        fopt_hist,
                        inequality_constraints_alpha,
                        inequality_constraint_violation_hist,
                        inequality_constraint_violation_jac_hist,
                        equality_constraints_alpha,
                        equality_constraint_violation_hist,
                        equality_constraint_violation_jac_hist,
                        i_k + eliminated_alpha,
                        infeasible_slopes_nosum_hist,
                        infeasible_alpha_hist,
                        infeasible_fopt_hist,
                        upper_bound_alpha,
                        current_step=current_step,
                    )
                    if not is_feasible:
                        break
                if is_feasible:
                    eta_opt = min(eta_opt_, eta_opt)
                    k_activ = self.__get_active_milp_constraints(
                        slopes_nosum_hist, alpha_hist, fopt_hist, eta_opt, alpha_opt
                    )
                    activ_ = "MILP : constraints active = " + str(k_activ)
                    LOGGER.info(activ_)
                    cat_ = "alpha_opt :  " + str(alpha_opt)
                    LOGGER.info(cat_)
                    i_k.append(alpha_opt)
            i_k = array(i_k)

            # The objective value of the solution.
            opt_ = "MILP : Optimal eta = " + str(eta_opt)
            LOGGER.info(opt_)
            bound_ = "MILP : Upper Bound = " + str(upper_bound)
            LOGGER.info(bound_)
            cat_ = "MILP : Upper Bound alpha = " + str(upper_bound_alpha)
            LOGGER.info(cat_)
            for alpha in old_iteration:
                out = {
                    func_name: database.get_function_value(func_name, alpha)
                    for func_name in self.function_names
                }
                fopt = out[self.problem.objective.name]
                if fopt is None:
                    LOGGER.error("CustomDOE execution did not run correctly.")
                    LOGGER.error("The database was not correctly updated.")
                    break
                self._is_point_feasible(out)
                self.__save_state(
                    alpha,
                    out,
                    upper_bound,
                    fopt.real,
                    eta_opt,
                    iteration,
                    upper_bound_alpha,
                )
            if eta_opt > upper_bound + self.epsilon:
                upper_bound_ = f"MILP : eta* ({eta_opt!s}) > UBD ({upper_bound!s})"
                LOGGER.info(upper_bound_)
                LOGGER.info("End of Outer Approximation algorithm.")
                break
            if iteration >= self.max_iter:
                upper_bound_ = f"MILP : eta* ({eta_opt!s}) > UBD ({upper_bound!s})"
                LOGGER.info(upper_bound_)
                LOGGER.info("Maximum iteration reached.")
                LOGGER.info("End of Outer Approximation algorithm.")
                break
            if (
                upper_bound_old - upper_bound == 0.0
                and stall_counter >= self.upper_bound_stall
            ):
                msg = (
                    f"The Upper bound stopped changing for "
                    f"{self.upper_bound_stall} iterations."
                )
                LOGGER.info(msg)
                LOGGER.info("End of Outer Approximation algorithm.")
                break
            if not is_feasible and len(i_k) == 0:
                msg = "Infeasible MILP problem."
                LOGGER.info(msg)
                LOGGER.info("End of Outer Approximation algorithm.")
                break

            iteration += 1
            alpha = alpha_opt
            fopt_ = "Outer Approximation current solution = " + str(fopt)
            LOGGER.info(fopt_)
        if iteration < self.max_iter:
            msg = "The Algorithm stopped proposing different new candidates."
            LOGGER.info(msg)
            LOGGER.info("End of Outer Approximation algorithm.")
        else:
            msg = "Maximum number of iteration reached."
            LOGGER.info(msg)
            LOGGER.info("End of Outer Approximation algorithm.")
        return upper_bound_alpha.real, upper_bound.real

    def _deal_with_constraints(
        self,
        alpha: ndarray,
        equality_constraint_violation_hist: Iterable[float],
        equality_constraint_violation_jac_hist: Iterable[ndarray],
        equality_constraints_alpha: Iterable[ndarray],
        inequality_constraint_violation_hist: Iterable[float],
        inequality_constraint_violation_jac_hist: Iterable[ndarray],
        inequality_constraints_alpha: Iterable[ndarray],
        out: dict[str, ndarray],
        out_jac: dict[str, dict[str, ndarray]],
    ) -> tuple[
        Iterable[ndarray],
        Iterable[float],
        Iterable[ndarray],
        Iterable[ndarray],
        Iterable[float],
        Iterable[ndarray],
    ]:
        """Deal with constraints.

        Args:
            alpha: The binary variable vector of the design point.
            equality_constraint_violation_hist: The equality constraint violation
                history.
            equality_constraint_violation_jac_hist:The equality constraint violation
                jacobian history.
            equality_constraints_alpha: The binary variable where equality constraints
                violation where computed.
            inequality_constraint_violation_hist: The inequality constraint violation
                history.
            inequality_constraint_violation_jac_hist:The inequality constraint violation
                jacobian history.
            inequality_constraints_alpha:The binary variable where inequality
                constraints violation where computed.
            out: The discipline outputs.
            out_jac: The jacobian outputs.
        """
        for constr in self.problem.constraints:
            if constr.f_type == MDOFunction.ConstraintType.INEQ:
                constraint_violation = out[constr.name]
                constraint_violation_jac = out_jac[constr.name]
                if self._check_independent_constraint(
                    inequality_constraint_violation_jac_hist,
                    inequality_constraints_alpha,
                    inequality_constraint_violation_hist,
                    constraint_violation_jac,
                    alpha.real,
                    constraint_violation,
                ):
                    inequality_constraints_alpha.append(alpha.real)
                    inequality_constraint_violation_hist.append(constraint_violation)
                    inequality_constraint_violation_jac_hist.append(
                        constraint_violation_jac
                    )
                    if self.constraint_history_size is not None and constr.name in list(
                        self.constraint_history_size.keys()
                    ):
                        (
                            inequality_constraint_violation_jac_hist,
                            inequality_constraints_alpha,
                            inequality_constraint_violation_hist,
                            _,
                        ) = self._filter_history(
                            slopes_hist=inequality_constraint_violation_jac_hist,
                            alpha_hist=inequality_constraints_alpha,
                            fopt_hist=inequality_constraint_violation_hist,
                            eliminated_alpha_hist=[],
                            history_size=self.constraint_history_size[constr.name],
                        )

            elif constr.f_type == MDOFunction.ConstraintType.EQ:
                constraint_violation = out[constr.name]
                constraint_violation_jac = out_jac[constr.name]
                if self._check_independent_constraint(
                    equality_constraint_violation_jac_hist,
                    equality_constraints_alpha,
                    equality_constraint_violation_hist,
                    constraint_violation_jac,
                    alpha.real,
                    constraint_violation,
                ):
                    equality_constraints_alpha.append(alpha.real)
                    equality_constraint_violation_hist.append(constraint_violation)
                    equality_constraint_violation_jac_hist.append(
                        constraint_violation_jac
                    )
                    if self.constraint_history_size is not None and constr.name in list(
                        self.constraint_history_size.keys()
                    ):
                        (
                            equality_constraint_violation_jac_hist,
                            equality_constraints_alpha,
                            equality_constraint_violation_hist,
                            _,
                        ) = self._filter_history(
                            slopes_hist=equality_constraint_violation_jac_hist,
                            alpha_hist=equality_constraints_alpha,
                            fopt_hist=equality_constraint_violation_hist,
                            eliminated_alpha_hist=[],
                            history_size=self.constraint_history_size[constr.name],
                        )
        return (
            inequality_constraints_alpha,
            inequality_constraint_violation_hist,
            inequality_constraint_violation_jac_hist,
            equality_constraints_alpha,
            equality_constraint_violation_hist,
            equality_constraint_violation_jac_hist,
        )

    def _deal_with_infeasible_point_constraints(
        self,
        alpha: ndarray,
        inequality_constraint_violation_hist: list[float | ndarray],
        inequality_constraint_violation_jac_hist: list[ndarray],
        inequality_constraints_alpha: list[ndarray],
        out: dict[str, ndarray],
        out_jac: dict[str, ndarray],
    ) -> None:
        """Deal with infeasible point constraints.

        Args:
            alpha: The binary variable vector of the design point.
            inequality_constraint_violation_hist: The inequality constraint
                violation history.
            inequality_constraint_violation_jac_hist:The inequality
            constraint violation
                jacobian history.
            inequality_constraints_alpha:The binary variable where inequality
                constraints violation where computed.
            out: The discipline outputs.
            out_jac: The jacobian outputs.
        """
        return

    def _deal_with_infeasible_points(
        self,
        alpha: ndarray,
        fopt: ndarray | float,
        infeasible_alpha_hist: list[ndarray],
        infeasible_fopt_hist: list[ndarray | float],
        infeasible_slopes_nosum_hist: list[ndarray],
        slopes_nosum: ndarray,
        eliminated_alpha: list[ndarray],
        alpha_best: ndarray | None,
    ) -> tuple[list[ndarray], list[ndarray | float], list[ndarray], list[ndarray]]:
        """Deal with infeasible points.

        Args:
            alpha: The binary vector where the infeasible point was computed.
            fopt: The objective value at alpha.
            infeasible_alpha_hist: The history of infeasible point binary variables.
            infeasible_fopt_hist:  The history of infeasible point objective function.
            infeasible_slopes_nosum_hist: The history of infeasible point objective
                function gradient.
            slopes_nosum: The objective function gradient at alpha.
            eliminated_alpha: The design points to be eliminated from design space.
            alpha_best: The reference alpha.

        Returns:
            The infeasible and eliminated alphas consistent with the infeasible history
            size.
        """
        infeasible_alpha_hist.append(alpha.real)
        infeasible_fopt_hist.append(fopt.real)
        infeasible_slopes_nosum_hist.append(slopes_nosum.real)
        if alpha_best is not None or self.infeasible_history_size >= 1:
            (
                infeasible_slopes_nosum_hist,
                infeasible_alpha_hist,
                infeasible_fopt_hist,
                eliminated_alpha,
            ) = self._filter_distance_history(
                infeasible_slopes_nosum_hist,
                infeasible_alpha_hist,
                infeasible_fopt_hist,
                alpha_best,
                eliminated_alpha,
                size=self.feasible_history_size,
            )
        return (
            infeasible_alpha_hist,
            infeasible_fopt_hist,
            infeasible_slopes_nosum_hist,
            eliminated_alpha,
        )

    def _deal_with_feasible_points(
        self,
        alpha: ndarray,
        alpha_hist: list[ndarray],
        fopt: ndarray | float,
        fopt_hist: list[ndarray | float],
        infeasible_alpha_hist: list[ndarray],
        infeasible_fopt_hist: list[ndarray | float],
        infeasible_slopes_nosum_hist: list[ndarray],
        slopes_nosum: ndarray,
        slopes_nosum_hist: list[ndarray],
        eliminated_alpha: list[ndarray],
    ) -> tuple[
        Iterable[ndarray],
        Iterable[float],
        Iterable[ndarray],
        Iterable[float],
        Iterable[ndarray],
        Iterable[ndarray],
        ndarray,
        ndarray,
        Iterable[ndarray],
    ]:
        """Deal with feasible points.

        Args:
            alpha: The binary variable vector of the design point.
            alpha_hist: The feasible design point binary variables.
            fopt: The objective function at alpha.
            fopt_hist: The objective function history for fesible design points.
            infeasible_alpha_hist: The history of infeasible point binary variables.
            infeasible_fopt_hist:  The history of infeasible point objective function.
            infeasible_slopes_nosum_hist: The history of infeasible point objective
                function gradient.
            slopes_nosum: The objective function gradient at alpha.
            slopes_nosum_hist: The objective function gradient history at feasible
                points.
            eliminated_alpha: The design points to be eliminated from design space.

        Returns:
            The feasible, infeasible and eliminated alphas consistent with the feasible
                and infeasible history size.
        """
        alpha_hist.append(alpha.real)
        fopt_hist.append(fopt.real)
        slopes_nosum_hist.append(slopes_nosum.real)
        min_index = argmin(fopt_hist)
        upper_bound = fopt_hist[min_index]
        upper_bound_alpha = alpha_hist[min_index]
        # (
        #     slopes_nosum_hist,
        #     alpha_hist,
        #     fopt_hist,
        #     eliminated_alpha,
        # ) = self._filter_sort_history(
        #     slopes_nosum_hist, alpha_hist, fopt_hist, eliminated_alpha
        # )
        (
            slopes_nosum_hist,
            alpha_hist,
            fopt_hist,
            eliminated_alpha,
        ) = self._filter_distance_history(
            slopes_hist=slopes_nosum_hist,
            alpha_hist=alpha_hist,
            fopt_hist=fopt_hist,
            alpha_best=upper_bound_alpha,
            eliminated_alpha_hist=eliminated_alpha,
            size=self.feasible_history_size,
        )
        (
            infeasible_slopes_nosum_hist,
            infeasible_alpha_hist,
            infeasible_fopt_hist,
            eliminated_alpha,
        ) = self._filter_distance_history(
            slopes_hist=infeasible_slopes_nosum_hist,
            alpha_hist=infeasible_alpha_hist,
            fopt_hist=infeasible_fopt_hist,
            alpha_best=upper_bound_alpha,
            eliminated_alpha_hist=eliminated_alpha,
            size=self.infeasible_history_size,
        )
        return (
            alpha_hist,
            fopt_hist,
            infeasible_alpha_hist,
            infeasible_fopt_hist,
            infeasible_slopes_nosum_hist,
            slopes_nosum_hist,
            upper_bound,
            upper_bound_alpha,
            eliminated_alpha,
        )

    def _is_point_feasible(self, out: dict[str, ndarray]) -> int:
        """Check if a point is feasible.

        Note:
            If the value of a constraint is absent from this point,
            then this constraint will be considered satisfied.

        Args:
            out: The values of the objective function, and eventually
            constraints.


        Returns:
            The feasibility of the point.
        """
        feasible = self.problem.constraints.is_point_feasible(out)
        out[self.IS_FEASIBLE_NAME] = int(feasible)
        return feasible

    def __check_trust_region_border(self, alpha: ndarray, alphaold: ndarray) -> bool:
        """Check if the border of the trust region are reached.

        Args:
            alpha: The new binary variable.
            alphaold: The old binary variable.

        Returns:
            Whether the new alpha is at the border of the trust region.
        """
        return (
            self.current_step - self.__apply_weights(alphaold).dot(alphaold - alpha) < 1
        )

    def __increase_step_size(self) -> None:
        """Increase the step size."""
        self.current_step = min(self.current_step * 1.2, self.max_step)

    def _execute_doe(self, i_k: ndarray) -> None:
        """Evaluate the functions of the problem at several one-hot-encoded designs.

        Args:
            i_k: The one-hot-encoded designs (as rows).
        """
        if i_k.shape[0] == 1 or self.n_processes == 1:
            for alpha in i_k:
                self.__evaluate_functions(alpha)
        else:
            CallableParallelExecution(
                [self.__evaluate_functions], self.n_processes
            ).execute(i_k)

    def __evaluate_functions(self, alpha: RealArray) -> None:
        """Evaluate the functions of the problem at a one-hot-encoded design.

        Args:
            alpha: The one-hot-encoded design.
        """
        self.problem.evaluate_functions(
            alpha,
            jacobian_functions=None if self.gradient_free else (),
        )

    # TODO: API replace the settings with the Pydantic model and remove all the getters.
    def optimize(self, **settings: Any) -> str:
        """Execute the whole optimization process.

        Args:
            **settings: The optimization solver settings.

        Returns:
            The optimization solver message at convergence.
        """
        self.n_catalogues = self.design_space.n_catalogues
        self.n_members = {}
        for key, value in self.n_catalogues.items():
            self.n_members[key] = int(self.design_space.variable_sizes[key] / value)
        self.normalize_design_space = settings["normalize_design_space"]
        self.time_limit_milliseconds = settings["time_limit_milliseconds"]
        self.max_iter = settings["max_iter"]
        self.epsilon = settings["ub_tol"]
        self.eq_tolerance = settings["eq_tolerance"]
        self.posa = settings["posa"]
        self.min_dfk = settings["min_dfk"]
        self.use_adaptative_convexification = settings["adapt"]
        self.use_bilateral_adaptation = settings["bilateral_adapt"]
        # TODO: remove self.UPPER_BOUND_STALL when the settings dictionary is replaced
        #       by a Pydantic model.
        self.upper_bound_stall = settings.get(
            "upper_bound_stall", self.UPPER_BOUND_STALL
        )

        self._use_scipy = settings["scipy"]
        if self._use_scipy:
            self._milp_solver = ExtendedScipyMILP()
            milp_settings = ExtendedScipyMILP_Settings
        else:
            self._milp_solver = OrtoolsMILP()
            milp_settings = OrtoolsMilp_Settings

        self._milp_settings = milp_settings(
            **filter_dict_for_settings(milp_settings, settings)
        )
        self._milp_settings.log_problem = settings["log_milp"]

        if self._use_scipy:
            if self.time_limit_milliseconds is not None:
                self._milp_settings.milp_time_limit = (
                    self.time_limit_milliseconds / 1000
                )
        else:
            self._milp_settings.milp_time_limit = self.time_limit_milliseconds

        self.convexification_constant = settings.get("convexification_constant", 0.0)
        self.max_step = settings.get("max_step", 10)
        self.min_step = settings.get("min_step", 1)
        self.step_decreasing_activation = settings.get("step_decreasing_activation", 3)
        self.lmbd = settings.get("constraint_scaling", 1000.0)
        self.feasible_history_size = settings.get("feasible_history_size", 1000)
        self.infeasible_history_size = settings.get("infeasible_history_size", 1000)
        self._max_feasible_history_size = settings.get("feasible_history_size", 1000)
        self._max_infeasible_history_size = settings.get(
            "infeasible_history_size", 1000
        )
        self.n_parallel_points = settings.get("number_of_parallel_points", 1)
        self.distance_filter_ratio = settings.get("distance_filter_ratio")
        self.gradient_free = settings.get("gradient_free", False)
        self.n_processes = settings.get("number_of_processes", self.n_parallel_points)
        # TODO: The parallel_exploration_factor setting is not defined
        #       in BiLevelMasterOuterApproximation_Settings,
        #       it only exists in OuterApproximation_Settings.
        #       The getter below ensures it is always 0 even if the setting is not
        #       defined.
        self.parallel_exploration_factor = settings.get(
            "parallel_exploration_factor", 0
        )
        self.constraint_history_size = settings.get("constraint_history_size")
        # initialize database
        x0 = self.design_space.get_current_value()
        self.initial_doe = self.build_doe(
            n=self.n_parallel_points, algorithm="OT_OPT_LHS", x0=x0
        )
        xopt, _ = self.__iterate(x0)
        self.design_space.set_current_value(xopt)

        return self.message

    def __save_state(
        self,
        xvect: ndarray,
        out: dict[str, ndarray],
        upper_bound: float,
        primal_sol: ndarray,
        lower_bound: float,
        iteration: int,
        upper_bound_alpha: ndarray,
    ) -> None:
        """Store in database information for plot.

        Args:
            xvect: The design variables vector.
            out: All outputs from the current  iteration.
            upper_bound: The upper bound value.
            primal_sol: The current sub-problem solution.
            lower_bound: The current lower bound value.
            iteration: The bilevel OuterApproximation iteration.
            upper_bound_alpha: The upper bound binary variable.
        """
        vals = {
            self.LOWER_BOUND_NAME: lower_bound,
            self.UPPER_BOUND_NAME: upper_bound,
            self.PRIMAL_SOL_NAME: primal_sol,
            self.BI_LEVEL_ITER_NAME: iteration,
            self.UPPER_BOUND_ALPHA_NAME: upper_bound_alpha,
        }
        out.update(vals)
        if (
            xvect not in self.database
            or self.LOWER_BOUND_NAME not in self.database[xvect]
        ):
            self.database.store(xvect, out)

    def build_doe(
        self, n: int, algorithm: str = "lhs", x0: ndarray | None = None
    ) -> ndarray:
        """Build a categorical DOE of n points based on enumerative representation.

        Args:
            n: The number of design point in the DOE.
            algorithm: The name of the algorithm used for building the DOE.
            x0: The starting guess if provided is used as starting point in the DOE.

        Returns:
            The DOE in the categorical design space.
        """
        converter = MDOChain(self.__build_enum_to_onehot_disciplines())
        design_space = DesignSpace()
        for key, value in self.n_catalogues.items():
            design_space.add_variable(
                key.replace("_onehot", "_enum"),
                value=zeros((self.n_members[key],)),
                lower_bound=0,
                upper_bound=(value - 1),
                size=self.n_members[key],
                type_="integer",
            )
        if n > 1:
            from gemseo import compute_doe

            doe_mat = unique(
                compute_doe(
                    variables_space=design_space, algo_name=algorithm, n_samples=n
                ),
                axis=0,
            )
        else:
            doe_mat = atleast_2d(design_space.get_current_value())
        alpha_doe = []
        for row in doe_mat:
            out = converter.execute(design_space.convert_array_to_dict(row))
            out_row = self.problem.design_space.convert_dict_to_array(out)
            alpha_doe.append(out_row)
        if x0.tolist() not in array(alpha_doe).tolist():
            alpha_doe[0] = x0
        if len(alpha_doe) < n:
            for _ in range(n - len(alpha_doe)):
                alpha_opt, _eta_opt, _is_feasible = self._solve_milp(
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    [],
                    alpha_doe,
                    [],
                    [],
                    [],
                    x0,
                    self.current_step,
                )
                alpha_doe.append(alpha_opt)
        return array(alpha_doe)

    def __build_enum_to_onehot_disciplines(self) -> list[Discipline]:
        """Build the discipline that compute one-hot from enumerative representation."""
        enum_disciplines = []
        for key, value in self.n_catalogues.items():
            enum_disciplines.append(
                EnumerativeToOneHot(
                    n_components=self.n_members[key],
                    catalogue=list(range(value)),
                    variable_name=key.replace("_onehot", "_enum"),
                    output_name=key,
                )
            )
        return enum_disciplines

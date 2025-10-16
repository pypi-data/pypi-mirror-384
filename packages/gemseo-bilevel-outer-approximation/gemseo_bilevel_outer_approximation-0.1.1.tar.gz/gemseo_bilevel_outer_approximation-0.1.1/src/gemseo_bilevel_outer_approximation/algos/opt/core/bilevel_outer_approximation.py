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
"""BiLevel Outer Approximation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.mdo_functions.mdo_function import MDOFunction
from numpy import atleast_1d

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.disciplines.scenario_adapters.mdo_scenario_adapter_benders import (  # noqa: E501
    MDOScenarioAdapterBenders,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.algos.optimization_problem import OptimizationProblem
    from gemseo.core.mdo_functions.discipline_adapter import DisciplineAdapter
    from gemseo.disciplines.scenario_adapters.mdo_scenario_adapter import (
        MDOScenarioAdapter,
    )
    from numpy import ndarray


class BiLevelOuterApproximation(OuterApproximationOptimizer):
    """Bi-level Outer Approximation Optimization solver."""

    def __init__(self, problem: OptimizationProblem) -> None:
        """
        Args:
            problem: The optimization problem.
        """  # noqa: D205, D212
        super().__init__(problem)
        self.function_names = list(
            set(
                [
                    self.problem.objective.name,
                    MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME,
                    self.IS_FEASIBLE_NAME,
                ]
                + [cstr.name for cstr in self.problem.constraints]
                + [obs.name for obs in self.problem.observables]
            )
        )

    def _is_point_feasible(self, out: dict[str, ndarray | float]) -> int:
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

    def _deal_with_constraints(
        self,
        alpha: ndarray,
        equality_constraint_violation_hist: list[float | ndarray],
        equality_constraint_violation_jac_hist: list[ndarray],
        equality_constraints_alpha: list[ndarray],
        inequality_constraint_violation_hist: list[float | ndarray],
        inequality_constraint_violation_jac_hist: list[ndarray],
        inequality_constraints_alpha: list[ndarray],
        out: dict[str, ndarray],
        out_jac: dict[str, ndarray],
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
            if constr.output_names[0] != self.IS_FEASIBLE_NAME:
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
                        inequality_constraint_violation_hist.append(
                            constraint_violation
                        )
                        inequality_constraint_violation_jac_hist.append(
                            constraint_violation_jac
                        )
                        if (
                            self.constraint_history_size is not None
                            and constr.name in list(self.constraint_history_size.keys())
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
                        if (
                            self.constraint_history_size is not None
                            and constr.name in list(self.constraint_history_size.keys())
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
        constraint_violation = out[MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME]
        constraint_violation_jac = out_jac[
            MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME
        ]
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
            inequality_constraint_violation_jac_hist.append(constraint_violation_jac)

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
        ) = super()._deal_with_feasible_points(
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

        # TODO:This part of the code requires gemseo-bilevel_oa Architecture discussion
        # for refactoring.
        # if isinstance(self.problem.objective, NormDBFunction):
        #     norm_db_func = self.problem.objective._NormDBFunction__orig_func
        #     norm_func = norm_db_func._NormFunction__orig_func
        #     o_fun = norm_func._DenseJacobianFunction__original_function
        # else:
        #     o_fun = self.problem.objective._output_evaluation_sequence
        try:
            discipline_adapter: DisciplineAdapter = (
                self.problem.objective.original.discipline_adapter
            )
        except AttributeError:  # pragma: no cover
            reset_x_before_opt = True  # pragma: no cover
        else:
            scenario_adapter: MDOScenarioAdapter = (
                discipline_adapter._DisciplineAdapter__discipline
            )
            reset_x_before_opt = scenario_adapter._reset_x0_before_opt

        if not reset_x_before_opt and all(alpha == upper_bound_alpha):
            x_opt = self.problem.database.get_function_value(
                MDOScenarioAdapterBenders.X_OPT_NAME, alpha
            )
            sub_problem_design_space = scenario_adapter.scenario.design_space

            sub_problem_design_space.set_current_value(atleast_1d(x_opt))
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

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
"""MDO scenario adapter for benders."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import ClassVar

from gemseo.algos.post_optimal_analysis import PostOptimalAnalysis
from gemseo.core.chains.chain import MDOChain
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.constraint_aggregation import ConstraintAggregation
from gemseo.disciplines.linear_combination import LinearCombination
from gemseo.disciplines.scenario_adapters.mdo_scenario_adapter import MDOScenarioAdapter
from numpy import array
from numpy import zeros

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from gemseo.core.discipline import Discipline
    from gemseo.scenarios.base_scenario import BaseScenario
    from numpy import ndarray


class MDOScenarioAdapterBenders(MDOScenarioAdapter):
    """An adapter class for MDO Scenario.

    The specified input variables update the default input data of the top level
    discipline while the output ones filter the output data from the top level
    discipline outputs.
    """

    __upper_level_constraints: list[str]
    """The list of upper level constraints."""

    __constraint_violation_discipline: Discipline | None
    """The discipline computing the constraint violation."""

    __constraint_penalty: float
    """The constraint penalty."""

    CONSTRAINT_VIOLATION_NAME: ClassVar[str] = "constraint_violation"
    X_OPT_NAME: ClassVar[str] = "x_opt"
    ITERATIONS_NAME: ClassVar[str] = "iterations"

    def __init__(
        self,
        scenario: BaseScenario,
        input_names: Sequence[str],
        output_names: Sequence[str],
        upper_level_constraints: list[str],
        constraint_penalty: float = 1000.0,
        reset_x0_before_opt: bool = False,
        set_x0_before_opt: bool = False,
        set_bounds_before_opt: bool = False,
        output_multipliers: bool = False,
        name: str = "",
        keep_opt_history: bool = False,
        opt_history_file_prefix: str = "",
        scenario_log_level: int | None = None,
    ) -> None:
        """
        Args:
            constraint_penalty: The constraint penalty used to compute
                constraint violation in sub scenario adapter.
            upper_level_constraints: The constraints in the upper level.
        """  # noqa: D205, D212
        super().__init__(
            scenario,
            input_names,
            output_names,
            reset_x0_before_opt,
            set_x0_before_opt,
            set_bounds_before_opt,
            output_multipliers,
            name,
            keep_opt_history,
            opt_history_file_prefix,
            scenario_log_level,
        )
        self.__upper_level_constraints = upper_level_constraints
        self.__constraint_penalty = constraint_penalty
        self._output_names = [
            *self._output_names,
            self.ITERATIONS_NAME,
            OuterApproximationOptimizer.IS_FEASIBLE_NAME,
            self.CONSTRAINT_VIOLATION_NAME,
            self.X_OPT_NAME,
        ]
        self.io.output_grammar.update_from_names(self._output_names)
        self.__constraint_violation_discipline = None

    def _compute_jacobian(
        self,
        input_names: Sequence[str] = (),
        output_names: Sequence[str] = (),
    ) -> None:
        """Compute the Jacobian of the adapted scenario outputs.

        The Jacobian is stored as a dictionary of numpy arrays:
        jac = {name: { input_name: ndarray(output_dim, input_dim) } }

        The bound-constraints on the scenario optimization variables
        are assumed independent of the other scenario inputs.

        The objective jacobian is computed with post-optimal sensitivity.
        The constraint jacobian is the auxiliary jacobian.
        """
        opt_problem = self.scenario.formulation.optimization_problem
        objective_names = (
            self.scenario.formulation.optimization_problem.objective.output_names
        )
        # N.B the adapter is assumed constant w.r.t. bounds
        bound_inputs = set(input_names) & set(self._bound_names)
        non_differentiable_outputs = sorted(set(output_names) - set(objective_names))
        # Initialize the Jacobian
        diff_inputs = [name for name in input_names if name not in bound_inputs]
        # N.B. there may be only bound inputs
        self._init_jacobian(diff_inputs, objective_names)

        # Compute the Jacobians of the optimization functions
        jacobians = self._compute_auxiliary_jacobians(
            diff_inputs,
            use_threading=True,
            func_names=opt_problem.objective.output_names
            + opt_problem.constraints.get_names()
            + self.__upper_level_constraints,
        )

        # Perform the post-optimal analysis
        ineq_tolerance = opt_problem.tolerances.inequality
        self.post_optimal_analysis = PostOptimalAnalysis(opt_problem, ineq_tolerance)
        post_opt_jac = self.post_optimal_analysis.execute(
            objective_names, diff_inputs, jacobians
        )
        for otp in non_differentiable_outputs:
            post_opt_jac[otp] = {}
            if otp not in [
                self.CONSTRAINT_VIOLATION_NAME,
                *self.__upper_level_constraints,
            ] or (
                otp == self.CONSTRAINT_VIOLATION_NAME
                and self.__constraint_violation_discipline is None
            ):
                self._initialize_jacobian_with_zeros(input_names, otp, post_opt_jac)
            elif otp == self.CONSTRAINT_VIOLATION_NAME:
                jac_c_v = self.__constraint_violation_discipline.linearize(
                    self.io.data, compute_all_jacobians=True
                )
                for inpt in input_names:
                    post_opt_jac[self.CONSTRAINT_VIOLATION_NAME][inpt] = jac_c_v[
                        self.CONSTRAINT_VIOLATION_NAME
                    ][inpt]
            elif (
                otp in self.__upper_level_constraints
                and otp != self.CONSTRAINT_VIOLATION_NAME
            ):
                for inpt in input_names:
                    post_opt_jac[otp][inpt] = jacobians[otp][inpt]

        self.jac.update(post_opt_jac)

    def _initialize_jacobian_with_zeros(
        self,
        inputs: Sequence[str],
        otp: str,
        post_opt_jac: dict[str, ndarray],
    ) -> None:
        """Initialize some components of the jacobian with zeros.

        Args:
           otp: The output variable name.
           post_opt_jac: The jacobian dictionary to be updated.
           inputs: The linearization should be performed with respect to these inputs.
                If None, the linearization should be performed w.r.t. all inputs.
        """
        for inpt in inputs:
            post_opt_jac[otp][inpt] = zeros((
                len(self.io.data[otp]),
                len(self.io.data[inpt]),
            ))

    def _build_constraint_violation_disciplines(self) -> None:
        """Build the constraint violation function."""
        if self.__constraint_violation_discipline is None:
            agg_disciplines: list[Discipline] = []
            for constr in self.scenario.formulation.optimization_problem.constraints:
                if constr not in self.__upper_level_constraints:
                    if constr.f_type == MDOFunction.ConstraintType.INEQ:
                        agg_disciplines.append(
                            ConstraintAggregation(
                                [constr.original_name],
                                ConstraintAggregation.EvaluationFunction.POS_SUM,
                                scale=self.__constraint_penalty,
                            )
                        )
                    else:
                        agg_disciplines.append(
                            ConstraintAggregation(
                                [constr.original_name],
                                ConstraintAggregation.EvaluationFunction.SUM,
                                scale=self.__constraint_penalty,
                            )
                        )
            agg_names: list[str] = []
            for agg in agg_disciplines:
                agg_names.extend(list(agg.io.output_grammar.names))

            cv = LinearCombination(agg_names, self.CONSTRAINT_VIOLATION_NAME)
            self.__constraint_violation_discipline = MDOChain(
                list(self.scenario.disciplines) + agg_disciplines + [cv]
            )

    def _retrieve_top_level_outputs(self) -> None:
        """Retrieve the top-level outputs.

        This method overwrites the adapter outputs with the top-level discipline outputs
        and the optimal design parameters.
        """
        formulation = self.scenario.formulation
        top_level_disciplines = formulation.get_top_level_disciplines()
        current_x = formulation.optimization_problem.design_space.get_current_value(
            as_dict=True
        )
        for name in self._output_names:
            for discipline in top_level_disciplines:
                if (
                    discipline.io.output_grammar.has_names([name])
                    and name not in current_x
                ):
                    self.io.data[name] = discipline.io.data[name]
            output_value_in_current_x = current_x.get(name)
            if output_value_in_current_x is not None:
                self.io.data[name] = output_value_in_current_x
        self.io.data[self.ITERATIONS_NAME] = array([
            float(len(formulation.optimization_problem.database))
        ])
        self.io.data[OuterApproximationOptimizer.IS_FEASIBLE_NAME] = array([
            float(formulation.optimization_problem.solution.is_feasible)
        ])
        self.io.data[self.X_OPT_NAME] = formulation.optimization_problem.solution.x_opt
        if len(self.scenario.formulation.optimization_problem.constraints) > 0:
            self._build_constraint_violation_disciplines()
            self.io.data[self.CONSTRAINT_VIOLATION_NAME] = (
                self.__constraint_violation_discipline.execute(self.io.data)[
                    self.CONSTRAINT_VIOLATION_NAME
                ]
            )
        else:
            self.io.data[self.CONSTRAINT_VIOLATION_NAME] = array([0.0])

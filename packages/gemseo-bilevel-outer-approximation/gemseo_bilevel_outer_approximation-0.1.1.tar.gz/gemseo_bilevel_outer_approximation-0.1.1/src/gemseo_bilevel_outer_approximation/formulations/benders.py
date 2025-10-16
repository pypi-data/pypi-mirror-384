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
"""A Benders Decomposition formulation."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.formulations.base_mdo_formulation import BaseMDOFormulation

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.disciplines.scenario_adapters.mdo_scenario_adapter_benders import (  # noqa: E501
    MDOScenarioAdapterBenders,
)
from gemseo_bilevel_outer_approximation.formulations.benders_settings import (
    Benders_Settings,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.algos.design_space import DesignSpace
    from gemseo.core.chains.chain import MDOChain
    from gemseo.core.discipline import Discipline
    from gemseo.core.discipline.base_discipline import BaseDiscipline
    from gemseo.disciplines.scenario_adapters.mdo_scenario_adapter import (
        MDOScenarioAdapter,
    )

LOGGER = logging.getLogger(__name__)


class Benders(BaseMDOFormulation):
    """Original problem : min f(x, y) s.t. g(x, y) <= 0 w.r.t. x in X and y in Y.

    Formulates a bi-level decomposition as follows :
    min u(y)
    w.r.t. y in Y
    s.t. u(y) = min f(x, y)
                s.t. g(x, y) <= 0
                w.r.t. x in X

    The main-problem optimizes (w.r.t. y) the optimum (w.r.t. x)
    of the sub-problem.
    The definition of X (sub-problem design space) and Y (main-problem design space)
    is either explicitly provided by the user, or is based on the
    design variable type (float, integer).
    """

    upper_level_constraints: list[str]
    """The list of upper level constraints."""

    convexification: float
    """The convexification constant."""

    sub_problem_scenario_adapter: MDOScenarioAdapter | None
    """The scenario adapter for the sub-problem."""

    __sub_problem_design_space: DesignSpace | None
    """The sub-problem design space."""

    __objective_name: str
    """The name of the objective function."""

    __minimize_objective: bool
    """Whether to minimize the objective."""

    chain: MDOChain | None
    """The sub-problem MDOChain."""

    Settings: ClassVar[type[Benders_Settings]] = Benders_Settings

    _settings: Benders_Settings

    def __init__(  # noqa: D107
        self,
        disciplines: list[Discipline],
        objective_name: str,
        design_space: DesignSpace,
        minimize_objective: bool = True,
        settings_model: Benders_Settings | None = None,
        **settings: Any,
    ) -> None:
        self.__minimize_objective = minimize_objective
        self.__objective_name = objective_name
        super().__init__(
            disciplines,
            objective_name,
            design_space,
            minimize_objective=minimize_objective,
            settings_model=settings_model,
            **settings,
        )
        self.add_observable(OuterApproximationOptimizer.IS_FEASIBLE_NAME)
        self.add_observable(MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME)
        self.add_observable(MDOScenarioAdapterBenders.ITERATIONS_NAME)
        self.add_observable(MDOScenarioAdapterBenders.X_OPT_NAME)

    def _init_before_design_space_and_objective(self) -> Discipline | None:
        self.upper_level_constraints = []
        if (
            not self._settings.split_criterion
            and not self._settings.main_problem_design_variables
        ):
            msg = (
                "Benders formulation needs either a split_criterion "
                "or a definition of the main_problem_design_variables."
            )
            raise ValueError(msg)
        self.chain = None
        self.__sub_problem_design_space = None
        self.sub_problem_scenario_adapter = None
        self.__build_sub_problem_scenario_adapter()
        return self.sub_problem_scenario_adapter

    @property
    def sub_problem_design_space(self) -> DesignSpace:
        """The sub-problem design space."""
        return self.__sub_problem_design_space

    def _update_design_space(self) -> None:
        self.design_space.filter(self.__get_main_problem_design_variables())
        self._set_default_input_values_from_design_space()

    def __build_sub_problem_scenario_adapter(self) -> None:
        """Build the scenario adapter of the sub-problem."""
        name = "sub_problem"
        self.__sub_problem_design_space = self.__build_sub_problem_dspace()

        from gemseo import create_scenario

        scenario = create_scenario(
            disciplines=self.disciplines,
            objective_name=self.__objective_name,
            design_space=self.__sub_problem_design_space,
            name=name,
            scenario_type="MDO",
            maximize_objective=not self.__minimize_objective,
            formulation_settings_model=self._settings.sub_problem_formulation_settings,
        )

        scenario.set_differentiation_method(method="user")

        scenario.set_algorithm(self._settings.sub_problem_algo_settings)

        # create sub scenario adapter
        # add inputs_parameters to Adapter inputs, for instance in cases
        # where Benders decomposition is a sub-problem of another formulation
        outputs_disc = []
        for disc in self.disciplines:
            outputs_disc += disc.io.output_grammar.names
        sc_allouts = [
            self.__objective_name,
            *self.__sub_problem_design_space.variable_names,
            *list(set(outputs_disc)),
        ]

        # scenario.add_observable("MDA residuals norm")

        # def max_MDA_residual_norm(x):
        #     out = scenario.formulation.optimization_problem.observables.
        # get_from_name(
        #         "MDA residuals norm"
        #     ).func(x)

        #     if out > 1e-6:
        #         return nan
        #     return scenario.formulation.optimization_problem.objective.original.
        # func(x)

        # residuals = scenario.formulation.optimization_problem.observables
        # .get_from_name(
        #     "MDA residuals norm"
        # )

        # def jac(x):
        #     return zeros_like(x)

        # residuals = MDOFunction(residuals.func, residuals.name, jac=jac)
        # scenario.formulation.optimization_problem.objective = (
        #     scenario.formulation.optimization_problem.objective + residuals * 1e6
        # )

        self.sub_problem_scenario_adapter = self._settings.scenario_adapter_cls(
            scenario,
            self.__get_main_problem_design_variables(),
            sc_allouts,
            reset_x0_before_opt=self._settings.reset_x0_before_opt,
            keep_opt_history=self._settings.keep_opt_history,
            opt_history_file_prefix=self._settings.opt_history_file_prefix,
            constraint_penalty=self._settings.constraint_penalty,
            upper_level_constraints=self.upper_level_constraints,
            scenario_log_level=self._settings.sub_scenario_log_level,
        )

    def __build_sub_problem_dspace(self) -> DesignSpace:
        """Build design space of sub-scenario.

        Returns:
            The sub-problem design space.
        """
        dv_toremove = self.__get_main_problem_design_variables()
        orig_dspace = deepcopy(self.design_space)
        dv_tokeep = set(orig_dspace.variable_names) - set(dv_toremove)
        return orig_dspace.filter(dv_tokeep)

    def __get_main_problem_design_variables(self) -> Iterable[str]:
        """Get main-problem design variables.

        Returns:
            The main-problem design variables.
        """
        if self._settings.main_problem_design_variables:
            return self._settings.main_problem_design_variables

        return deepcopy(self.design_space).filter_non_categorical().variable_names

    def add_constraint(
        self,
        output_name: str,
        constraint_type: MDOFunction.ConstraintType = MDOFunction.ConstraintType.INEQ,
        constraint_name: str = "",
        value: float = 0.0,
        positive: bool = False,
        main_level: bool = False,
        linearized: bool = False,
    ) -> None:
        """
        Args:
            main_level: Whether the constraint violation should be dealt with both in
                sub and main level. This is useful when constraints depends on
                categorical variables and can lead to unfeasible sub-problems.
            linearized: Whether the constraint is considered as a linear constraint in
                the main level.
        """  # noqa: D212, D205
        sub_problem_scenario = self.sub_problem_scenario_adapter.scenario

        if not linearized:
            sub_problem_scenario.add_constraint(
                output_name, constraint_type, constraint_name, value, positive
            )
        else:
            self.upper_level_constraints.append(output_name)
            sub_problem_scenario.add_observable(output_name)

        if main_level:
            if linearized:
                super().add_constraint(
                    output_name,
                    constraint_type,
                    constraint_name,
                    value,
                    positive,
                )

            elif OuterApproximationOptimizer.IS_FEASIBLE_NAME not in [
                cstr.output_names[0] for cstr in self.optimization_problem.constraints
            ]:
                super().add_constraint(
                    OuterApproximationOptimizer.IS_FEASIBLE_NAME,
                    MDOFunction.ConstraintType.EQ,
                    value=1.0,
                )

    def get_top_level_disciplines(self) -> tuple[BaseDiscipline, ...]:  # noqa: D102
        return (self.sub_problem_scenario_adapter,)

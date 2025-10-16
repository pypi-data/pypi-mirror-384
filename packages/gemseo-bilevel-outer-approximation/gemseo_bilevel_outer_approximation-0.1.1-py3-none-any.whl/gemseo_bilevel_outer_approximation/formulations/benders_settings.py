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

"""Settings for Benders decomposition."""

from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003

from gemseo.algos.base_algorithm_settings import BaseAlgorithmSettings  # noqa: TC002
from gemseo.algos.design_space import DesignSpace
from gemseo.formulations.base_formulation_settings import BaseFormulationSettings
from gemseo.formulations.disciplinary_opt_settings import DisciplinaryOpt_Settings
from pydantic import Field

from gemseo_bilevel_outer_approximation.disciplines.scenario_adapters.mdo_scenario_adapter_benders import (  # noqa: E501
    MDOScenarioAdapterBenders,
)


class Benders_Settings(BaseFormulationSettings):  # noqa: N801
    """Settings of the :class`.Benders` formulation."""

    _TARGET_CLASS_NAME = "Benders"

    constraint_penalty: float = Field(
        default=1000.0,
        description="""The constraint penalty used to compute
        constraint violation in sub scenario adapter.""",
    )

    split_criterion: str = Field(
        default=DesignSpace.DesignVariableType.INTEGER,
        description="The criterion used to split the design space.",
    )

    main_problem_design_variables: Sequence[str] = Field(
        default=(),
        description=(
            "If ``split_criterion`` is empty, the main-problem design variables. "
            "If empty, "
            "``split_criterion`` is used to get the main-problem design variables."
        ),
    )

    scenario_adapter_cls: type[MDOScenarioAdapterBenders] = Field(
        default=MDOScenarioAdapterBenders,
        description="The class for Scenario Adapter instantiation.",
    )

    reset_x0_before_opt: bool = Field(
        default=True,
        description="""If True reset starting point before each sub-problem
                execution.""",
    )

    keep_opt_history: bool = Field(
        default=False,
        description="Whether to keep databases copies after each execution.",
    )

    opt_history_file_prefix: str = Field(
        default="",
        description="""The base name for the databases to be exported.
                The full names of the databases are built from
                the provided base name suffixed by ``"_i.h5"``
                where ``i`` is replaced by the execution number,
                i.e. the number of stored databases.
                If empty, the databases are not exported.
                The databases can be exported only is ``keep_opt_history=True``.""",
    )

    sub_scenario_log_level: int | None = Field(
        default=None,
        description=(
            "The level of the root logger during the sub-scenario execution. "
            "If ``None``, do not change the level of the root logger."
        ),
    )

    sub_problem_formulation_settings: BaseFormulationSettings = Field(
        default=DisciplinaryOpt_Settings(),
        description="The sub-problem formulation settings.",
    )

    sub_problem_algo_settings: BaseAlgorithmSettings = Field(
        description="The sub-problem optimization solver settings."
    )

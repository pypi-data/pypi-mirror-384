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
"""Build a penalized scenario with Hypersphere approach."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.chains.chain import MDOChain
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.linear_combination import LinearCombination

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.scenarios.base_scenario import BaseScenario
    from gemseo.scenarios.mdo_scenario import MDOScenario

    from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
        CatalogueDesignSpace,
    )


def build_hypersphere_penalized_scenario(
    scenario: MDOScenario,
    design_space: CatalogueDesignSpace,
    penalties: Iterable[float],
    constraints: dict[str, float],
) -> BaseScenario:
    """Penalize intermediate catalog choice with external penalty.

    Args:
        scenario: The original MDO scenario including catalog design variables.
        design_space: The design space.
        penalties: The penalty coefficients.
        constraints: The name of the quantity to be constrained in the scenario.

    Returns:
        A penalized MDOScenario.
    """
    objective_name = scenario.formulation.optimization_problem.objective.name
    cost_names = [
        f"C_{name}_onehot"
        for var, disc in design_space.hyper_cube_discipline.items()
        for name in disc.io.input_grammar.names
    ]
    penalized_objective = "penalized " + objective_name
    total_discipline = MDOChain(scenario.disciplines)
    out_total = total_discipline.execute(
        input_data=design_space.get_current_value(as_dict=True)
    )
    scaling_factor = []
    for const, penalty in zip(cost_names, penalties, strict=False):
        scaling_factor.append(
            float(out_total[objective_name])
            / (float(out_total[const]) + int(out_total[const] == 0))
            * penalty
        )
    sum_disc = LinearCombination(
        input_names=[objective_name, *cost_names],
        output_name=penalized_objective,
        input_coefficients=dict(
            zip([objective_name, *cost_names], [1.0, *scaling_factor], strict=False)
        ),
    )
    from gemseo import create_scenario

    new_scenario = create_scenario(
        disciplines=[*scenario.disciplines, sum_disc],
        design_space=design_space,
        objective_name=penalized_objective,
        formulation_name="DisciplinaryOpt",
        name="ShapeFunctionPenalization",
        scenario_type="MDO",
    )
    for const_name, const_value in constraints.items():
        new_scenario.add_constraint(
            const_name,
            value=const_value,
            constraint_type=MDOFunction.ConstraintType.INEQ,
        )
    return new_scenario

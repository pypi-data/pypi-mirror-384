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
"""Disciplines for simple problems."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from gemseo import create_scenario
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.settings.opt import NLOPT_SLSQP_Settings
from numpy import array

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)

if TYPE_CHECKING:
    from gemseo_bilevel_outer_approximation.formulations.benders import Benders


def test_floudas() -> None:
    """Test the Floudas problem."""
    problem_d_disc = AnalyticDiscipline(
        name="Problem 2 Computations",
        expressions={
            "f": " -0.7*y+5*(x1-0.5)**2+0.8",
            "g_1": "-exp(x1-0.2)-x2",
            "g_2": "x2+3.1*y-1",
            "g_3": "x1-1.2*y-0.2",
        },
    )

    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x1",
        lower_bound=0.2,
        upper_bound=1,
        value=0.5,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )
    ds.add_variable(
        "x2",
        lower_bound=-2.22554,
        upper_bound=-1,
        value=-2,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )

    ds.add_categorical_variable(name="y_onehot", value=[0], catalogue=[0, 1])

    y1_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y_onehot", output="y", catalogue=array([0.0, 1.0])
    )

    convergence_tol = 1e-8

    scenario = create_scenario(
        disciplines=[
            y1_disc,
            problem_d_disc,
        ],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=NLOPT_SLSQP_Settings(
            max_iter=150,
            ineq_tolerance=1e-4,
            xtol_rel=convergence_tol,
            xtol_abs=convergence_tol,
            ftol_rel=convergence_tol,
            ftol_abs=convergence_tol,
            normalize_design_space=True,
        ),
    )
    scenario.add_constraint(
        "g_1", constraint_type=MDOFunction.ConstraintType.INEQ, main_level=True
    )
    scenario.add_constraint(
        "g_2", constraint_type=MDOFunction.ConstraintType.INEQ, main_level=True
    )
    scenario.add_constraint(
        "g_3", constraint_type=MDOFunction.ConstraintType.INEQ, main_level=True
    )
    scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=False,
        posa=1.0,
        adapt=False,
        max_step=1000,
    )
    benders_formulation: Benders = scenario.formulation
    x_opt, f_opt = (
        benders_formulation.optimization_problem.solution.x_opt,
        benders_formulation.optimization_problem.solution.f_opt,
    )
    assert (x_opt == [0, 1]).all()
    assert f_opt == pytest.approx(1.0765430833322616)

    # msg = (
    #     f"Total number of function linearization calls = "
    #     f"{scenario.formulation.sub_problem_scenario.scenario.formulation.chain.
    # n_calls_linearize}"
    # )

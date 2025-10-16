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
from gemseo import execute_post
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.settings.opt import NLOPT_SLSQP_Settings
from numpy import array

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)

if TYPE_CHECKING:
    from gemseo_bilevel_outer_approximation.formulations.benders import Benders

DesignVariableType = CatalogueDesignSpace.DesignVariableType


@pytest.mark.parametrize("gradient_free", [True, False])
def test_problem_a(tmp_wd, gradient_free: bool) -> None:
    """Test the problem A."""
    problem_a_disc = AnalyticDiscipline(
        name="Problem A Computations",
        expressions={
            "f": "2.*x1 + 3.*x2 + 1.5*y1 + 2.*y2 -0.5*y3",
            "h_1": "(x1**2. + y1 -1.25)",
            "h_2": "(x2**1.5 + 1.5*y2 -3.)",
            "g_1": "x1 + y1 -1.6",
            "g_2": "1.333*x2 + y2 -3.",
            "g_3": " -y1-y2+y3",
        },
    )

    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x1",
        lower_bound=0.0,
        upper_bound=10.0,
        value=10.0,
        type_=DesignVariableType.FLOAT,
    )
    ds.add_variable(
        "x2",
        lower_bound=0.0,
        upper_bound=10.0,
        value=10.0,
        type_=DesignVariableType.FLOAT,
    )
    ds.add_categorical_variable(name="y1_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y2_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y3_onehot", value=[0], catalogue=[0, 1])

    y1_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y1_onehot", output="y1", catalogue=array([0.0, 1.0])
    )
    y2_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y2_onehot", output="y2", catalogue=array([0.0, 1.0])
    )
    y3_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y3_onehot", output="y3", catalogue=array([0.0, 1.0])
    )
    convergence_tol = 1e-6

    scenario = create_scenario(
        disciplines=[y1_disc, y2_disc, y3_disc, problem_a_disc],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=NLOPT_SLSQP_Settings(
            max_iter=150,
            ineq_tolerance=1e-3,
            xtol_rel=convergence_tol,
            xtol_abs=convergence_tol,
            ftol_rel=convergence_tol,
            ftol_abs=convergence_tol,
            normalize_design_space=True,
            kkt_tol_abs=1e-4,
        ),
    )
    scenario.add_constraint("h_1", constraint_type=MDOFunction.ConstraintType.EQ)
    scenario.add_constraint("h_2", constraint_type=MDOFunction.ConstraintType.EQ)
    scenario.add_constraint("g_1", constraint_type=MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("g_2", constraint_type=MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("g_3", constraint_type=MDOFunction.ConstraintType.INEQ)

    scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=True,
        posa=1.0,
        adapt=True,
        gradient_free=gradient_free,
        number_of_parallel_points=2,
        number_of_processes=1,
        bilateral_adapt=True,
    )

    benders_formulation: Benders = scenario.formulation
    x_opt, f_opt = (
        benders_formulation.optimization_problem.solution.x_opt,
        benders_formulation.optimization_problem.solution.f_opt,
    )
    # msg = f"The solution of P is (x*,f(x*)) = ({x_opt}, {f_opt})"
    assert (x_opt == [1, 0, 0, 1, 0, 1]).all()
    assert f_opt == pytest.approx(7.670570392298737)
    # msg = (
    #     "Total number of function linearization calls = "
    #     f"{benders_formulation.sub_problem_scenario.scenario.formulation.
    # chain.n_calls}"
    # )

    execute_post(
        scenario,
        post_name="OuterApproximationHistory",
        fig_size=(9, 7),
        show=True,
        save=True,
    )

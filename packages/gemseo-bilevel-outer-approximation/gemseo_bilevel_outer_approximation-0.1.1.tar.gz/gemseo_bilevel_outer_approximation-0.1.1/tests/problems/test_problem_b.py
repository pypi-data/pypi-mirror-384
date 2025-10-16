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


@pytest.mark.parametrize(
    ("gradient_free", "expected_x_opt", "expected_f_opt"),
    [
        pytest.param(
            True,
            [1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0],
            -0.9434705181088264,
            marks=pytest.mark.xfail(reason="Ask S.Coniglio about this test"),
        ),
        (False, [0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1], -0.91429100057712),
    ],
)
def test_problem_b(
    tmp_wd, gradient_free: bool, expected_x_opt: list[int], expected_f_opt: float
) -> None:
    """Test the problem B."""
    problem_b_disc = AnalyticDiscipline(
        name="Problem B Computations",
        expressions={
            "f": " -(x1*x2*x3)",
            "h_1": "(-log(1 -x1) +y1*log(0.1) + y2*log(0.2) + y3*log(0.15))",
            "h_2": "-log(1 -x2) + y4*log(0.05) + y5*log(0.2) + y6*log(0.15)",
            "h_3": "- log(1 -x3) + y7*log(0.02) + y8*log(0.06)",
            "g_1": "-y1 -y2 -y3 +1.",
            "g_2": "-y4 -y5 -y6 +1.",
            "g_3": " -y7 -y8 +1.",
            "g_4": " 3.*y1 + y2 + 2.*y3 + 3.*y4 + 2.*y5 + y6 + 3.*y7 + 2.*y8-10",
            "h_4": "y1 + y2+ y3 + y4 + y5 + y6 + y7 + y8 - 5",
        },
    )

    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x1",
        lower_bound=0.0,
        upper_bound=0.9970,
        value=0.5,
        type_=DesignVariableType.FLOAT,
    )
    ds.add_variable(
        "x2",
        lower_bound=0.0,
        upper_bound=0.9985,
        value=0.5,
        type_=DesignVariableType.FLOAT,
    )
    ds.add_variable(
        "x3",
        lower_bound=0.0,
        upper_bound=0.9988,
        value=0.5,
        type_=DesignVariableType.FLOAT,
    )
    ds.add_categorical_variable(name="y1_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y2_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y3_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y4_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y5_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y6_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y7_onehot", value=[1], catalogue=[0, 1])
    ds.add_categorical_variable(name="y8_onehot", value=[1], catalogue=[0, 1])

    y1_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y1_onehot", output="y1", catalogue=array([0.0, 1.0])
    )
    y2_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y2_onehot", output="y2", catalogue=array([0.0, 1.0])
    )
    y3_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y3_onehot", output="y3", catalogue=array([0.0, 1.0])
    )
    y4_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y4_onehot", output="y4", catalogue=array([0.0, 1.0])
    )
    y5_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y5_onehot", output="y5", catalogue=array([0.0, 1.0])
    )
    y6_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y6_onehot", output="y6", catalogue=array([0.0, 1.0])
    )
    y7_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y7_onehot", output="y7", catalogue=array([0.0, 1.0])
    )
    y8_disc = ds.get_catalogue_interpolation_discipline(
        penalty=1.0, variable="y8_onehot", output="y8", catalogue=array([0.0, 1.0])
    )
    ineq_tol = 1e-5
    convergence_tol = 1e-8

    scenario = create_scenario(
        disciplines=[
            y1_disc,
            y2_disc,
            y3_disc,
            y4_disc,
            y5_disc,
            y6_disc,
            y7_disc,
            y8_disc,
            problem_b_disc,
        ],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=NLOPT_SLSQP_Settings(
            max_iter=150,
            ineq_tolerance=ineq_tol,
            eq_tolerance=ineq_tol,
            xtol_rel=convergence_tol,
            xtol_abs=convergence_tol,
            ftol_rel=convergence_tol,
            ftol_abs=convergence_tol,
            normalize_design_space=True,
            kkt_tol_abs=1e-6,
        ),
        reset_x0_before_opt=False,
    )
    scenario.add_constraint(
        "h_1", constraint_type=MDOFunction.ConstraintType.EQ, main_level=True
    )
    scenario.add_constraint(
        "h_2", constraint_type=MDOFunction.ConstraintType.EQ, main_level=True
    )
    scenario.add_constraint(
        "h_3", constraint_type=MDOFunction.ConstraintType.EQ, main_level=True
    )
    scenario.add_constraint(
        "g_1",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=True,
    )
    scenario.add_constraint(
        "g_2",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=True,
    )
    scenario.add_constraint(
        "g_3",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=True,
    )
    scenario.add_constraint(
        "g_4",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=True,
    )
    scenario.add_constraint(
        "h_4",
        constraint_type=MDOFunction.ConstraintType.EQ,
        main_level=True,
        linearized=True,
    )

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
        min_dfk=4,
        scipy=True,
        step_decreasing_activation=1000,
    )
    benders_formulation: Benders = scenario.formulation
    x_opt, f_opt = (
        benders_formulation.optimization_problem.solution.x_opt,
        benders_formulation.optimization_problem.solution.f_opt,
    )
    assert f_opt == pytest.approx(expected_f_opt)
    assert (x_opt == expected_x_opt).all()
    # msg = (
    #     "Total number of function linearization calls = "
    #     f"{scenario.formulation.sub_problem_scenario.scenario.formulation.
    # chain.n_calls}"
    # )

    execute_post(
        scenario,
        post_name="OuterApproximationHistory",
        fig_size=(9, 7),
        show=True,
        save=True,
    )

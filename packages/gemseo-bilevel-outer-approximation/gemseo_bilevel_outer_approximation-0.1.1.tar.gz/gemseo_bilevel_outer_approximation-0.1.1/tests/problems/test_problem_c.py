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


def test_problem_c(tmp_wd) -> None:
    """Test the problem C."""
    problem_c_disc = AnalyticDiscipline(
        name="Problem C Computations",
        expressions={
            "f": " 7*x1+10*x2",
            "g_1": "x1**1.2*x2**1.7-7*x1-9*x2+24",
            "g_2": "-x1-2*x2-5",
            "g_3": "-3*x1+x2-1",
            "g_4": "4*x1-3*x2-11",
            "h_1": "-x1+y1+2*y2+4*y3",
            "h_2": "-x2+y4+2*y5+y6",
        },
    )

    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x1",
        lower_bound=1.0,
        upper_bound=5.0,
        value=5.0,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )
    ds.add_variable(
        "x2",
        lower_bound=1.0,
        upper_bound=5.0,
        value=5.0,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )

    ds.add_categorical_variable(name="y1_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y2_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y3_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y4_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y5_onehot", value=[0], catalogue=[0, 1])
    ds.add_categorical_variable(name="y6_onehot", value=[0], catalogue=[0, 1])

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

    convergence_tol = 1e-6
    scenario = create_scenario(
        disciplines=[
            y1_disc,
            y2_disc,
            y3_disc,
            y4_disc,
            y5_disc,
            y6_disc,
            problem_c_disc,
        ],
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
    scenario.add_constraint(
        "h_1", constraint_type=MDOFunction.ConstraintType.EQ, main_level=True
    )
    scenario.add_constraint(
        "h_2", constraint_type=MDOFunction.ConstraintType.EQ, main_level=True
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
    scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=False,
        posa=1.0,
        adapt=True,
        max_step=1000,
    )
    benders_formulation: Benders = scenario.formulation
    x_opt, f_opt = (
        benders_formulation.optimization_problem.solution.x_opt,
        benders_formulation.optimization_problem.solution.f_opt,
    )
    assert (x_opt == [0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0]).all()
    assert f_opt == 31.0

    # msg = (
    #     "Total number of function linearization calls = "
    #     f"{scenario.formulation.sub_problem_scenario.scenario.formulation.
    # chain.n_calls_linearize}"
    # )

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

from __future__ import annotations

import os.path
import sys

import pytest
from gemseo import create_scenario
from gemseo import execute_post
from gemseo.core.discipline import Discipline
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.settings.opt import NLOPT_SLSQP_Settings
from numpy import arange
from numpy import array
from numpy.testing import assert_array_equal

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)
from tests.algos.conftest import CatTestDisc

DesignVariableType = CatalogueDesignSpace.DesignVariableType


@pytest.mark.parametrize("number_of_parallel_points", [1, 2])
@pytest.mark.parametrize("time_limit_milliseconds", [None, 1000])
@pytest.mark.parametrize("scipy", [True, False])
def test_bileveloa_optimizer_analytical(
    analytical_use_case,
    mdo_discipline_catalog,
    posa,
    adapt,
    number_of_parallel_points,
    time_limit_milliseconds,
    scipy,
    tmp_wd,
):
    """Test benders on an analytical use case.

    Run BiLevel OuterApproximation on several situations.
    """
    if sys.platform.startswith("win") and number_of_parallel_points > 1:
        pytest.skip("Parallel use of cache is not supported on windows")
    if mdo_discipline_catalog != CatTestDisc:
        pytest.skip("Avoid redundant tests")
    h5_file = "test.h5"
    analytical_use_case[0].formulation.sub_problem_scenario_adapter.set_cache(
        cache_type=Discipline.CacheType.HDF5,
        hdf_file_path=os.path.join(tmp_wd, h5_file),
    )
    opt_options = {
        "algo_name": "BILEVEL_MASTER_OUTER_APPROXIMATION",
        "max_iter": 1000,
        "normalize_design_space": True,
        "posa": posa,
        "adapt": adapt,
        "min_dfk": 0.0,
        "number_of_parallel_points": number_of_parallel_points,
        "scipy": scipy,
    }
    if time_limit_milliseconds is not None:
        opt_options["time_limit_milliseconds"] = time_limit_milliseconds
    analytical_use_case[0].execute(**opt_options)
    options = {
        "fig_size": (9, 7),
        "show": False,
        "save": False,
    }

    assert execute_post(
        analytical_use_case[0], post_name="BiLevelOuterApproximationHistory", **options
    )
    assert_array_equal(analytical_use_case[0].optimization_result.x_opt, [0, 1, 0])
    assert (
        pytest.approx(analytical_use_case[0].optimization_result.f_opt, abs=1e-10)
        == 0.0
    )
    assert os.path.exists(os.path.join(tmp_wd, h5_file))


@pytest.mark.parametrize("number_of_parallel_points", [1, 2])
@pytest.mark.parametrize("scipy", [True, False])
def test_bileveloa_optimizer_multi_component(
    analytical_use_case_multi_var, number_of_parallel_points, problem_size, scipy
):
    """Test benders on an analytical use case with multiple catgalog components."""
    analytical_use_case_multi_var[0].execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=True,
        posa=1.0,
        adapt=False,
        min_dfk=0.0,
        number_of_parallel_points=number_of_parallel_points,
        scipy=scipy,
    )
    options = {
        "fig_size": (9, 7),
        "show": False,
        "save": False,
    }

    assert execute_post(
        analytical_use_case_multi_var[0],
        post_name="BiLevelOuterApproximationHistory",
        **options,
    )
    assert_array_equal(
        analytical_use_case_multi_var[0].optimization_result.x_opt,
        array([[1, 0, 0]] * problem_size).flatten(),
    )
    assert pytest.approx(
        analytical_use_case_multi_var[0].optimization_result.f_opt
    ) == sum(arange(start=1, stop=3 * problem_size, step=3))


@pytest.mark.parametrize("number_of_parallel_points", [1, 2])
@pytest.mark.parametrize("linearize_constraints", [True, False])
@pytest.mark.parametrize("scipy", [True, False])
def test_problem_b(linearize_constraints, number_of_parallel_points, scipy):
    """Test for infeasible sub problems."""
    problem_a_disc = AnalyticDiscipline(
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
    algo_settings = NLOPT_SLSQP_Settings(
        max_iter=1000,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-5,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        normalize_design_space=True,
        kkt_tol_abs=1e-6,
    )

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
            problem_a_disc,
        ],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=algo_settings,
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
        linearized=linearize_constraints,
    )
    scenario.add_constraint(
        "g_2",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=linearize_constraints,
    )
    scenario.add_constraint(
        "g_3",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=linearize_constraints,
    )
    scenario.add_constraint(
        "g_4",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        main_level=True,
        linearized=linearize_constraints,
    )
    scenario.add_constraint(
        "h_4",
        constraint_type=MDOFunction.ConstraintType.EQ,
        main_level=True,
        linearized=True,
    )

    scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=1000,
        normalize_design_space=False,
        posa=1.0,
        adapt=False,
        number_of_parallel_points=number_of_parallel_points,
        scipy=scipy,
    )
    assert pytest.approx(scenario.formulation.optimization_problem.solution.f_opt) == -(
        1 - 0.2 * 0.15
    ) * (1 - 0.05 * 0.15) * (1 - 0.02)

    assert execute_post(
        scenario,
        post_name="BiLevelOuterApproximationHistory",
        fig_size=(9, 7),
        show=False,
        save=False,
    )


@pytest.fixture(params=[True, False])
def gradient_free_scenario(request):
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

    scenario = create_scenario(
        disciplines=[y1_disc, y2_disc, y3_disc, problem_a_disc],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=NLOPT_SLSQP_Settings(
            max_iter=150,
            ineq_tolerance=1e-3,
            xtol_rel=1e-6,
            xtol_abs=1e-6,
            ftol_rel=1e-6,
            ftol_abs=1e-6,
            normalize_design_space=True,
            kkt_tol_abs=1e-4,
        ),
        reset_x0_before_opt=request.param,
    )
    scenario.add_constraint("h_1", constraint_type=MDOFunction.ConstraintType.EQ)
    scenario.add_constraint("h_2", constraint_type=MDOFunction.ConstraintType.EQ)
    scenario.add_constraint("g_1", constraint_type=MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("g_2", constraint_type=MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("g_3", constraint_type=MDOFunction.ConstraintType.INEQ)
    return scenario


def test_gradient_free(gradient_free_scenario):
    gradient_free_scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=True,
        posa=1.0,
        adapt=True,
        gradient_free=True,
        number_of_parallel_points=2,
        number_of_processes=1,
        bilateral_adapt=True,
    )
    assert_array_equal(
        gradient_free_scenario.formulation.optimization_problem.solution.x_opt,
        array([1.0, 0.0, 0.0, 1.0, 0.0, 1.0]),
    )

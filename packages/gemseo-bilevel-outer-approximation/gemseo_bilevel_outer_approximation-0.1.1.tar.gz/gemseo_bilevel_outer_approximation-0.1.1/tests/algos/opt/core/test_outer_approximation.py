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

import pytest
from gemseo import create_scenario
from gemseo import execute_post
from gemseo.algos.optimization_problem import OptimizationProblem
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from numpy import all as np_all
from numpy import array
from numpy.testing import assert_array_equal

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)
from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.algos.opt.ortools_milp.ortools_milp_settings import (  # noqa: E501
    OrtoolsMilp_Settings,
)
from gemseo_bilevel_outer_approximation.algos.opt.scipy_milp.extended_scipy_milp_settings import (  # noqa: E501
    ExtendedScipyMILP_Settings,
)
from tests.algos.conftest import CatTestDisc


@pytest.mark.parametrize("number_of_parallel_points", [1, 2])
@pytest.mark.parametrize("time_limit_milliseconds", [None, 1000])
def test_oa_optimizer_analytical(
    analytical_use_case_oa,
    mdo_discipline_catalog,
    posa,
    adapt,
    number_of_parallel_points,
    time_limit_milliseconds,
):
    """Test benders on an analytical use case.

    Run BiLevel OuterApproximation on several situations.
    """
    # if sys.platform.startswith("win") and number_of_parallel_points > 1:
    #     pytest.skip("Parallel use of cache is not supported on windows")
    if mdo_discipline_catalog != CatTestDisc:
        pytest.skip("Avoid redundant tests")
    opt_options = {
        "algo_name": "OUTER_APPROXIMATION",
        "max_iter": 1000,
        "normalize_design_space": True,
        "posa": posa,
        "adapt": adapt,
        "min_dfk": 0.0,
        "number_of_parallel_points": number_of_parallel_points,
    }
    if time_limit_milliseconds is not None:
        opt_options["time_limit_milliseconds"] = time_limit_milliseconds
    analytical_use_case_oa[0].disciplines[0].default_input_data = {"x": array([0.0])}
    analytical_use_case_oa[0].disciplines[0].default_input_data.update(
        analytical_use_case_oa[1].get_current_value(as_dict=True)
    )
    analytical_use_case_oa[0].execute(**opt_options)
    options = {
        "fig_size": (9, 7),
        "show": False,
        "save": False,
    }

    assert execute_post(
        analytical_use_case_oa[0], post_name="OuterApproximationHistory", **options
    )
    assert_array_equal(analytical_use_case_oa[0].optimization_result.x_opt, [0, 1, 0])
    assert pytest.approx(analytical_use_case_oa[0].optimization_result.f_opt) == 0.0


def objective_function(a_onehot):
    return a_onehot[0] + a_onehot[4]


def constraint_function(a_onehot):
    return a_onehot[1] + a_onehot[5]


@pytest.fixture
def outer_approximation_solver():
    ds = CatalogueDesignSpace()
    ds.add_categorical_variable(
        name="a", value=["white", "white"], catalogue=["black", "white", "red", "green"]
    )
    problem = OptimizationProblem(ds)
    problem.objective = MDOFunction(
        objective_function, name="f", input_names="a_onehot"
    )
    problem.add_constraint(
        MDOFunction(constraint_function, name="g", input_names="a_onehot"),
        constraint_type=MDOFunction.ConstraintType.EQ,
    )
    return OuterApproximationOptimizer(problem)


def test_oa_time_limit(outer_approximation_solver):
    assert outer_approximation_solver.time_limit_milliseconds is None
    outer_approximation_solver.time_limit_milliseconds = 1000
    assert outer_approximation_solver.time_limit_milliseconds == 1000
    outer_approximation_solver.time_limit_milliseconds = None
    assert outer_approximation_solver.time_limit_milliseconds is None


def test_oa_hsize(outer_approximation_solver):
    assert outer_approximation_solver.infeasible_history_size == 1000
    assert outer_approximation_solver.feasible_history_size == 1000
    outer_approximation_solver.infeasible_history_size = 10
    outer_approximation_solver.feasible_history_size = 10
    assert outer_approximation_solver.infeasible_history_size == 10
    assert outer_approximation_solver.feasible_history_size == 10


def test_check_independent_planes(outer_approximation_solver):
    assert outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([0, 0, 1]),
        array([0, 0, 1]),
        0,
    )
    assert outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([1, 1, 1]),
        array([0, 0, 1]),
        0,
    )
    assert not outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([1, 1, 1]),
        array([1, 1, 1]),
        3,
    )
    assert not outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([1, 1, 1]),
        array([0, 0, 0]),
        0,
    )
    assert not outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([1, 0, 0]),
        array([1, 1, 1]),
        0,
    )
    assert not outer_approximation_solver._check_independent_constraint(
        [array([1, 1, 1]), array([1, 0, 0])],
        [array([0, 0, 0]), array([1, 0, 0])],
        [0, 0],
        array([1, 0, 0]),
        array([1, 0, 0]),
        0,
    )


def test_filter_distance_history(outer_approximation_solver):
    outer_approximation_solver.distance_filter_ratio = 2
    outer_approximation_solver.current_step = 1
    input_data = {
        "slopes_hist": [array([1, 0, 0]), array([0, 1, 0])],
        "alpha_hist": [array([1, 0, 0]), array([0, 1, 0])],
        "fopt_hist": [0.0, 1.0],
        "alpha_best": None,
        "eliminated_alpha_hist": [],
        "size": 2,
    }
    slopes_hist, alpha_hist, fopt_hist, _eliminated_alpha_hist = (
        outer_approximation_solver._filter_distance_history(**input_data)
    )
    assert np_all(slopes_hist == array([array([1, 0, 0]), array([0, 1, 0])]))
    assert np_all(alpha_hist == array([array([1, 0, 0]), array([0, 1, 0])]))
    assert fopt_hist == [0.0, 1.0]
    outer_approximation_solver.distance_filter_ratio = 2
    outer_approximation_solver.current_step = 1
    input_data = {
        "slopes_hist": [array([1, 0, 0]), array([0, 1, 0])],
        "alpha_hist": [array([1, 0, 0]), array([0, 1, 0])],
        "fopt_hist": [0.0, 1.0],
        "alpha_best": None,
        "eliminated_alpha_hist": [],
        "size": 1,
    }
    slopes_hist, alpha_hist, fopt_hist, _eliminated_alpha_hist = (
        outer_approximation_solver._filter_distance_history(**input_data)
    )
    assert np_all(slopes_hist == array([array([1, 0, 0])]))
    assert np_all(alpha_hist == array([array([1, 0, 0])]))
    assert fopt_hist == [0.0]
    outer_approximation_solver.distance_filter_ratio = 1
    outer_approximation_solver.current_step = 1
    input_data = {
        "slopes_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 0, 0, 1, 0])],
        "alpha_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 1, 0, 1, 1])],
        "fopt_hist": [0.0, 1.0],
        "alpha_best": array([1, 0, 0, 1, 0, 0]),
        "eliminated_alpha_hist": [],
        "size": 2,
    }
    slopes_hist, alpha_hist, fopt_hist, _eliminated_alpha_hist = (
        outer_approximation_solver._filter_distance_history(**input_data)
    )
    assert np_all(slopes_hist == array([array([1, 0, 0, 1, 0, 0])]))
    assert np_all(alpha_hist == array([array([1, 0, 0, 1, 0, 0])]))
    assert fopt_hist == [0.0]


def test_filter_history(outer_approximation_solver):
    input_data = {
        "slopes_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 0, 0, 1, 0])],
        "alpha_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 1, 0, 1, 1])],
        "fopt_hist": [0.0, 1.0],
        "eliminated_alpha_hist": [],
        "history_size": 1,
    }
    slopes_hist, alpha_hist, fopt_hist, _eliminated_alpha_hist = (
        outer_approximation_solver._filter_history(**input_data)
    )
    assert np_all(slopes_hist == array([array([0, 1, 0, 0, 1, 0])]))
    assert np_all(alpha_hist == array([array([0, 1, 1, 0, 1, 1])]))
    assert fopt_hist == [1.0]
    input_data = {
        "slopes_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 0, 0, 1, 0])],
        "alpha_hist": [array([1, 0, 0, 1, 0, 0]), array([0, 1, 1, 0, 1, 1])],
        "fopt_hist": [0.0, 1.0],
        "eliminated_alpha_hist": [],
        "history_size": 0,
    }
    slopes_hist, alpha_hist, fopt_hist, _eliminated_alpha_hist = (
        outer_approximation_solver._filter_history(**input_data)
    )
    assert slopes_hist == []
    assert alpha_hist == []
    assert fopt_hist == []


@pytest.fixture
def scenario_onehot():
    """A simple scenario to execute (Problem A computations)."""
    problem_a_disc = AnalyticDiscipline(
        name="Problem A Computations",
        expressions={
            "f": "1.5*y1 + 2.*y2 -0.5*y3",
            "g_3": " -y1-y2+y3+1",
        },
    )

    ds = CatalogueDesignSpace()
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
        formulation_name="DisciplinaryOpt",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
    )
    scenario.add_constraint("g_3", constraint_type=MDOFunction.ConstraintType.INEQ)
    return scenario


@pytest.mark.parametrize("gradient_free", [False, True])
def test_gradient_free(scenario_onehot, gradient_free: bool):
    """Test the impact of the ``gradient_free`` argument."""
    scenario_onehot.execute(
        algo_name="OUTER_APPROXIMATION",
        max_iter=100,
        normalize_design_space=True,
        posa=1.0,
        adapt=True,
        gradient_free=gradient_free,
        number_of_parallel_points=4,
        number_of_processes=1,
        bilateral_adapt=False,
        min_dfk=2,
        scipy=True,
        step_decreasing_activation=1000,
    )
    assert_array_equal(
        scenario_onehot.formulation.optimization_problem.solution.x_opt,
        array([0.0, 1.0, 1.0, 0.0, 1.0, 0.0]),
    )


def test_solving_with_eq_constraint() -> None:
    """Test to solve a scenario with equality constraints."""
    problem_a_disc = AnalyticDiscipline(
        name="Problem A Computations",
        expressions={
            "f": "1.5*y1 + 2.*y2 -0.5*y3",
            "g_3": " -y1-y2+y3+1",
        },
    )

    ds = CatalogueDesignSpace()
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
        formulation_name="DisciplinaryOpt",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
    )
    scenario.add_constraint("g_3", constraint_type=MDOFunction.ConstraintType.EQ)
    scenario.execute(
        algo_name="OUTER_APPROXIMATION",
        max_iter=10,
        gradient_free=True,
        number_of_parallel_points=2,
        adapt=True,
        scipy=True,
    )

    assert_array_equal(
        scenario.formulation.optimization_problem.solution.x_opt,
        array([0.0, 1.0, 1.0, 0.0, 1.0, 0.0]),
    )


@pytest.mark.parametrize("normalize_design_space", [False, True])
@pytest.mark.parametrize("adapt", [False, True])
@pytest.mark.parametrize("bilateral_adapt", [False, True])
@pytest.mark.parametrize("scipy", [False, True])
@pytest.mark.parametrize("log_milp", [False, True])
def test_milp_settings(
    outer_approximation_solver,
    normalize_design_space: bool,
    adapt: bool,
    bilateral_adapt: bool,
    scipy: bool,
    log_milp: bool,
) -> None:
    """Check the settings of the MILP algorithm."""
    outer_approximation_solver.optimize(
        normalize_design_space=normalize_design_space,
        eq_tolerance=1,
        max_iter=2,
        time_limit_milliseconds=3,
        ub_tol=4,
        posa=5,
        min_dfk=6,
        adapt=adapt,
        bilateral_adapt=bilateral_adapt,
        scipy=scipy,
        gradient_free=True,
        log_milp=log_milp,
    )
    settings = outer_approximation_solver._milp_settings
    assert settings.normalize_design_space == normalize_design_space
    assert settings.eq_tolerance == 1
    assert settings.max_iter == 2
    assert "time_limit_milliseconds" not in settings
    assert "ub_tol" not in settings
    assert "posa" not in settings
    assert "min_dfk" not in settings
    assert "use_adaptive_convexification" not in settings
    assert "use_bilateral_adaptation" not in settings
    assert "scipy" not in settings
    if scipy:
        assert isinstance(settings, ExtendedScipyMILP_Settings)
    else:
        assert isinstance(settings, OrtoolsMilp_Settings)

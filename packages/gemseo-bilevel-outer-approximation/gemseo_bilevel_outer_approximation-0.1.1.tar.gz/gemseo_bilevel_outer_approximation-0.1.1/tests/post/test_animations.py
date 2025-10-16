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

from os.path import isfile

import pytest
from gemseo import create_scenario
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.post.topology_view import TopologyView
from gemseo.post.topology_view_settings import TopologyView_Settings
from gemseo.problems.topology_optimization.topopt_initialize import (
    initialize_design_space_and_discipline_to,
)
from gemseo.utils.testing.pytest_conftest import tmp_wd
from numpy import array
from numpy import ones_like
from numpy import zeros_like

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)
from gemseo_bilevel_outer_approximation.post.topology_animation import (
    TopologyGifAnimation,
)
from gemseo_bilevel_outer_approximation.post.upper_bound_animation import (
    UpperBoundAnimation,
)

n_x = 10
n_y = 5


@pytest.fixture
def gemseo_tmp_wd():
    # This is used as a temporary solution to avoid raising check problems.
    return tmp_wd


@pytest.fixture
def to_scenario(gemseo_tmp_wd):
    volume_fraction = 0.3
    problem_name = "Short_Cantilever"
    penalty1 = 5
    ds, discs = initialize_design_space_and_discipline_to(
        problem_name,
        n_x=n_x,
        n_y=n_y,
        e0=1.0,
        nu=0.3,
        penalty=penalty1,
        min_member_size=1.5,
        vf0=volume_fraction,
    )
    empty_elements = discs[1].empty_elements
    ds = CatalogueDesignSpace()

    alpha_0 = ["full"] * n_y * n_x
    for i in empty_elements:
        alpha_0[i] = "empty"
    ds.add_categorical_variable(
        "alpha", value=alpha_0, catalogue=array(["empty", "full"])
    )
    fixed_var_index = list(
        set([2 * i for i in empty_elements] + [2 * i + 1 for i in empty_elements])
    )
    lower_bound = zeros_like(ds.get_current_value())
    lower_bound[fixed_var_index] = ds.get_current_value()[fixed_var_index]
    upper_bound = ones_like(ds.get_current_value())
    upper_bound[fixed_var_index] = ds.get_current_value()[fixed_var_index]

    discs = [
        ds.get_catalogue_interpolation_discipline(
            penalty=1.0, variable="alpha", output="x", catalogue=array([0.0, 1.0])
        ),
        *discs,
    ]

    run_options = {
        "algo_name": "OUTER_APPROXIMATION",
        "max_iter": 2,
        "normalize_design_space": True,
        "posa": 1,
        "adapt": False,
        # "time_limit_milliseconds": 1000,
        "upper_bound_stall": 30,
        "min_dfk": 0,
        "bilateral_adapt": False,
        "max_step": 1000,
        "min_step": 2,
        "feasible_history_size": 10,
        "infeasible_history_size": 1,
        "step_decreasing_activation": 1,
        "scipy": True,
        "constraint_scaling": 1e3,
        "node_limit": 100,
        "mip_rel_gap": 1e-3,
        "number_of_parallel_points": 1,
        "number_of_processes": 1,
        "parallel_exploration_factor": 0,
        "convexification_constant": 0,
        "distance_filter_ratio": 1,
    }
    scenario = create_scenario(
        disciplines=discs,
        formulation_name="DisciplinaryOpt",
        objective_name="compliance",
        design_space=ds,
        maximize_objective=False,
    )
    scenario.add_constraint(
        "volume fraction", MDOFunction.ConstraintType.INEQ, value=volume_fraction
    )
    scenario.add_observable("x")
    scenario.execute(**run_options)
    return scenario


def test_animations(tmp_wd, to_scenario):
    frame_generator_options = {"n_x": n_x, "n_y": n_y, "observable": "x"}
    problem = to_scenario.formulation.optimization_problem

    post_processing = TopologyGifAnimation(problem)
    settings = post_processing.Settings(
        gif_file_path="design_evolution",
        post_processing=TopologyView(problem),
        post_processing_settings=TopologyView_Settings(**frame_generator_options),
    )
    post_processing.execute(settings_model=settings)
    assert isfile("design_evolution.gif")

    post_processing = UpperBoundAnimation(problem)
    settings = post_processing.Settings(
        gif_file_path="best_design_evolution",
        post_processing=TopologyView(problem),
        post_processing_settings=TopologyView_Settings(**frame_generator_options),
    )
    post_processing.execute(settings_model=settings)
    assert isfile("best_design_evolution.gif")

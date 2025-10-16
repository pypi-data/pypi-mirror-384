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
"""Topology Optimization example."""

from __future__ import annotations

# from examples.NLMIP.conftest import post_process_topology_problem
from gemseo import create_scenario
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.problems.topology_optimization.topopt_initialize import (
    initialize_design_space_and_discipline_to,
)
from matplotlib import colors
from matplotlib import pyplot as plt
from numpy import array
from numpy import ones_like
from numpy import zeros_like

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)


def test_gradient_free_topology_optimization(tmp_wd) -> None:
    """Test the gradient free topology optimization."""
    n_x = 25
    n_y = 25
    volume_fraction = 0.3
    problem_name = "L-Shape"
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
        "max_iter": 10,
        "normalize_design_space": True,
        "posa": 1,
        # "time_limit_milliseconds": 1000,
        "upper_bound_stall": 30,
        "min_dfk": 0,
        "max_step": 200,
        "min_step": 2,
        "feasible_history_size": 2000,
        "infeasible_history_size": 2000,
        "step_decreasing_activation": 1,
        "scipy": True,
        "constraint_scaling": 1e3,
        "node_limit": 100,
        "mip_rel_gap": 1e-3,
        "parallel_exploration_factor": 0,
        "convexification_constant": 0,
        "adapt": True,
        "gradient_free": True,
        "number_of_parallel_points": 10,
        "number_of_processes": 1,
        "bilateral_adapt": True,
        "distance_filter_ratio": 2,
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

    plt.ion()  # Ensure that redrawing is possible
    fig, ax = plt.subplots()
    alpha_opt = scenario.optimization_result.x_opt
    x_opt = discs[0].execute(ds.convert_array_to_dict(alpha_opt))["x"]
    im = ax.imshow(
        -x_opt.reshape((n_x, n_y)).T,
        cmap="gray",
        interpolation="none",
        norm=colors.Normalize(vmin=-1, vmax=0),
    )
    fig.show()
    im.set_array(-x_opt.reshape((n_x, n_y)).T)
    fig.canvas.draw()
    plt.savefig(f"{problem_name}_solution_{penalty1}.png")

    # post_process_topology_problem(scenario, problem_name, penalty1, n_x, n_y)

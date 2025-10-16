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

import pytest

# from examples.NLMIP.conftest import post_process_topology_problem
from gemseo import create_scenario
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.problems.topology_optimization.topopt_initialize import (
    initialize_design_space_and_discipline_to,
)
from matplotlib import colors
from matplotlib import pyplot as plt
from numpy import array

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)


@pytest.mark.parametrize(
    "options",
    [
        {
            "adapt": False,
            "min_dfk": 0,
            "bilateral_adapt": False,
            "mip_rel_gap": 1e-3,
            "number_of_parallel_points": 1,
            "number_of_processes": 1,
            "parallel_exploration_factor": 0,
            "convexification_constant": 0,
            "distance_filter_ratio": 1,
        },
        {
            "adapt": True,
            "min_dfk": 1,
            "bilateral_adapt": True,
            "scipy": True,
            "constraint_scaling": 1e3,
            "node_limit": 1000,
            # "convexification_constant":10000
        },
    ],
)
def test_topology_optimization(tmp_wd, options) -> None:
    """Test the topology optimization."""
    n_x = 50
    n_y = 25
    run_options = {
        "algo_name": "OUTER_APPROXIMATION",
        "max_iter": 10,
        "normalize_design_space": True,
        "posa": 1,
        "upper_bound_stall": 30,
        "max_step": 250,
        "min_step": 2,
        "feasible_history_size": 10,
        "infeasible_history_size": 1,
        "step_decreasing_activation": 1,
        "scipy": True,
        "constraint_scaling": 1e3,
        "node_limit": 100,
        "time_limit_milliseconds": 1000,
    }
    run_options.update(options)
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

    discs = [
        ds.get_catalogue_interpolation_discipline(
            penalty=1.0, variable="alpha", output="x", catalogue=array([0.0, 1.0])
        ),
        *discs,
    ]

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
    plt.savefig(problem_name + f"_solution_{int(penalty1)}.png")

    # post_process_topology_problem(scenario, problem_name, penalty1, n_x, n_y)

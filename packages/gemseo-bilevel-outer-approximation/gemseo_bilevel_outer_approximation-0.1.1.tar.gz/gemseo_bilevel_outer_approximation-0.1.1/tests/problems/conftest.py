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
"""Integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.post import TopologyView_Settings
from gemseo.post.animation import Animation
from gemseo.post.topology_view import TopologyView
from gemseo.utils.testing.pytest_conftest import *  # noqa: F401,F403

from gemseo_bilevel_outer_approximation.post.outer_approximation_history import (
    OuterApproximationHistory,
)
from gemseo_bilevel_outer_approximation.post.outer_approximation_history_settings import (  # noqa: E501
    OuterApproximationHistory_Settings,
)
from gemseo_bilevel_outer_approximation.post.topology_animation import (
    TopologyGifAnimation,
)
from gemseo_bilevel_outer_approximation.post.upper_bound_animation import (
    UpperBoundAnimation,
)

if TYPE_CHECKING:
    from gemseo.scenarios.mdo_scenario import MDOScenario


def post_process_topology_problem(
    scenario: MDOScenario, problem_name: str, penalty: int, n_x: int, n_y: int
) -> None:
    """Post-process the topology problem.

    Args:
        scenario: The scenario.
        problem_name: The name of the problem.
        penalty: The penalty value.

    """
    scenario.post_process(
        post_name="BasicHistory",
        variable_names=["compliance"],
        save=True,
        show=False,
        file_name=f"{problem_name}_c_history_{penalty}.png",
    )
    scenario.post_process(
        post_name="BasicHistory",
        variable_names=["volume fraction"],
        save=True,
        show=False,
        file_name=f"{problem_name}_vf_history_{penalty}.png",
    )
    scenario.post_process(
        post_name="BasicHistory",
        variable_names=["volume fraction"],
        save=True,
        show=False,
        file_name=f"{problem_name}_vf_history_{penalty}.png",
    )
    scenario.post_process(
        post_name="OuterApproximationHistory",
        fig_size=(9, 7),
        show=True,
        file_path=f"Convergence_OuterApproximation_{penalty}",
        save=True,
    )
    frame_generator_options = {
        "n_x": n_x,
        "n_y": n_y,
        "observable": "x",
        #  "frame_rate": 100,
    }

    post_processing = TopologyGifAnimation(scenario.formulation.optimization_problem)
    settings = post_processing.Settings(
        gif_file_path="design_evolution",
        post_processing=TopologyView(scenario.formulation.optimization_problem),
        post_processing_settings=TopologyView_Settings(**frame_generator_options),
        **frame_generator_options,
    )
    scenario.post_process(settings_model=settings)

    post_processing = UpperBoundAnimation(scenario.formulation.optimization_problem)
    settings = post_processing.Settings(
        gif_file_path="best_design_evolution",
        post_processing=TopologyView(scenario.formulation.optimization_problem),
        post_processing_settings=TopologyView_Settings(**frame_generator_options),
        **frame_generator_options,
    )
    scenario.post_process(settings_model=settings)

    post_processing = Animation(scenario.formulation.optimization_problem)
    settings = post_processing.Settings(
        gif_file_path="outer_approximation_history",
        post_processing=OuterApproximationHistory(
            scenario.formulation.optimization_problem
        ),
        post_processing_settings=OuterApproximationHistory_Settings(fig_size=(9, 7)),
        fig_size=(9, 7),
    )
    scenario.post_process(settings_model=settings)

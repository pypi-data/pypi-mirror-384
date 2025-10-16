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
"""Gif animation of best solution in outer approximation."""

from __future__ import annotations

from typing import ClassVar

from gemseo.post.animation import Animation

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.post.upper_bound_animation_settings import (
    UpperBoundAnimation_Settings,
)


class UpperBoundAnimation(Animation):
    """Best design animation."""

    Settings: ClassVar[type[UpperBoundAnimation_Settings]] = (
        UpperBoundAnimation_Settings
    )

    def _generate_frames(
        self,
        settings: UpperBoundAnimation_Settings,
    ) -> list[list[str]]:
        from gemseo import execute_post

        frames = []
        for iteration in range(
            0, len(self.optimization_problem.database), settings.frame_rate
        ):
            upper_bound_alpha = self.optimization_problem.database.get_function_value(
                OuterApproximationOptimizer.UPPER_BOUND_ALPHA_NAME,
                self.optimization_problem.database.get_x_vect(iteration + 1),
            )
            index = self.optimization_problem.database.get_iteration(upper_bound_alpha)
            options = {}
            options["file_path"] = f"frame_{iteration + 1}"
            options["iterations"] = index
            frames.append(
                execute_post(
                    self.optimization_problem,
                    post_name=settings.opt_post_processor,
                    file_path=f"{self._FRAME}_{iteration}",
                    iterations=iteration,
                ).output_files
            )
        return frames

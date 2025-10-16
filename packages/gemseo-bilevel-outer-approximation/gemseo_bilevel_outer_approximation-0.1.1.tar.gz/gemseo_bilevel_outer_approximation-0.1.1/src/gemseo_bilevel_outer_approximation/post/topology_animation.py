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
"""Topology optimization GIF animation."""

from __future__ import annotations

from typing import ClassVar

from gemseo.post.animation import Animation

from gemseo_bilevel_outer_approximation.post.topology_animation_settings import (
    TopologyAnimation_Settings,
)


class TopologyGifAnimation(Animation):
    """The class for Topology Optimization Animations."""

    Settings: ClassVar[type[TopologyAnimation_Settings]] = TopologyAnimation_Settings

    def _generate_frames(
        self,
        settings: TopologyAnimation_Settings,
    ) -> list[list[str]]:
        """Generate the frames.

        Args:
            frame_rate: The rate of frame per iterations.
            frame_generator: The name of the class to be used as frame generator.
            options: The frame generator options.

        Returns:
            The frame figure paths.
        """
        from gemseo import execute_post

        return [
            execute_post(
                self.optimization_problem,
                post_name=settings.opt_post_processor,
                file_path=f"{self._FRAME}_{iteration}",
                iterations=iteration,
            ).output_files
            for iteration in range(
                1, len(self.optimization_problem.database) + 1, settings.frame_rate
            )
        ]

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

# Copyright (c) 2022 IRT-AESE.
# All rights reserved.
#
# Contributors:
#    AUTHORS:
#        :author: Pierre-Jean Barjhoux
#        :author: Simone Coniglio
"""Outer Approximation History."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import ClassVar
from typing import TypeVar

from matplotlib import pyplot
from matplotlib.ticker import MaxNLocator

from gemseo_bilevel_outer_approximation.disciplines.scenario_adapters.mdo_scenario_adapter_benders import (  # noqa: E501
    MDOScenarioAdapterBenders,
)
from gemseo_bilevel_outer_approximation.post.bilevel_outer_approximation_history_settings import (  # noqa: E501
    BiLevelOuterApproximationHistory_Settings,
)
from gemseo_bilevel_outer_approximation.post.outer_approximation_history import (
    OuterApproximationHistory,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy import ndarray

T = TypeVar("T", bound=BiLevelOuterApproximationHistory_Settings)


class BiLevelOuterApproximationHistory(OuterApproximationHistory):
    """Class for post-processing BiLevel Outer Approximation history."""

    Settings: ClassVar[type[BiLevelOuterApproximationHistory_Settings]] = (
        BiLevelOuterApproximationHistory_Settings
    )

    def _plot(self, settings: T) -> None:
        super()._plot(settings)
        is_feasible = self.database.get_function_history(self.IS_FEASIBLE)
        constraint_violation = self.database.get_function_history(
            MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME
        )
        iteration = self.database.get_function_history(self.BI_LEVEL_ITER)

        font_size = 15
        if sum(~is_feasible.astype(bool)) > 0:
            fig2, axe2 = pyplot.subplots(figsize=settings.fig_size)
            self.__plot_oa_cv_history(axe2, constraint_violation, iteration, font_size)
            fig2.tight_layout()
            self._add_figure(fig2)

    def __plot_oa_cv_history(
        self,
        axe: Axes,
        constraint_violation: ndarray,
        iteration: ndarray,
        font_size: float,
        from_iter: int = 0,
    ) -> None:
        """Plot constraint violation history.

        Args:
            axe: The figure axes.
            constraint_violation: The constraint violation at each iteration.
            iteration: The vector of main problem iteration.
            font_size: The font size.
            from_iter: The iteration from which the plot should start.
        """
        n_iter = len(constraint_violation)
        axe.xaxis.set_major_locator(MaxNLocator(integer=True))
        axe.grid(True)
        axe.set_xlim([from_iter + 0.5, n_iter + 0.5])
        axe.set_xlabel("iterations", fontsize=font_size)
        axe.set_ylabel("Constrtaint violation", fontsize=font_size)
        axe.step(
            iteration[from_iter:],
            constraint_violation[from_iter:],
            label=MDOScenarioAdapterBenders.CONSTRAINT_VIOLATION_NAME,
            color="black",
            where="post",
        )
        axe.legend(numpoints=1, fontsize=font_size)

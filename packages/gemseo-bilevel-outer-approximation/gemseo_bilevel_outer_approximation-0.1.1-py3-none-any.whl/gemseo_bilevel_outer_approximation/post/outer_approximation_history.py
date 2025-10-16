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

from gemseo.post.base_post import BasePost
from matplotlib import pyplot
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.post.outer_approximation_history_settings import (  # noqa: E501
    OuterApproximationHistory_Settings,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy import ndarray

T = TypeVar("T", bound=OuterApproximationHistory_Settings)


class OuterApproximationHistory(BasePost):
    """Class for post-processing BiLevel Outer Approximation history."""

    PRIMAL_SOL = OuterApproximationOptimizer.PRIMAL_SOL_NAME
    LOWER_BOUND = OuterApproximationOptimizer.LOWER_BOUND_NAME
    UPPER_BOUND = OuterApproximationOptimizer.UPPER_BOUND_NAME
    IS_FEASIBLE = OuterApproximationOptimizer.IS_FEASIBLE_NAME
    BI_LEVEL_ITER = OuterApproximationOptimizer.BI_LEVEL_ITER_NAME

    Settings: ClassVar[type[OuterApproximationHistory_Settings]] = (
        OuterApproximationHistory_Settings
    )

    def _plot(self, settings: T) -> None:
        params = {
            "text.usetex": False,
            "font.family": "serif",
        }
        rcParams.update(params)
        rcParams["legend.loc"] = "best"

        minlp_sol = self.database.get_function_history(self.PRIMAL_SOL)
        milp_sol = self.database.get_function_history(self.LOWER_BOUND)
        upper_bounds = self.database.get_function_history(self.UPPER_BOUND)
        is_feasible = self.database.get_function_history(self.IS_FEASIBLE)
        iteration = self.database.get_function_history(self.BI_LEVEL_ITER)

        font_size = 15

        fig, axe = pyplot.subplots(figsize=settings.fig_size)

        self.__plot_outer_approximation_history(
            axe, minlp_sol, milp_sol, upper_bounds, is_feasible, iteration, font_size
        )
        fig.tight_layout()

        self._add_figure(fig)

    def __plot_outer_approximation_history(
        self,
        axe: Axes,
        minlp_sol: ndarray,
        milp_sol: ndarray,
        upper_bounds: ndarray,
        is_feasible: ndarray,
        iteration: ndarray,
        font_size: float,
        from_iter: int = 0,
    ) -> None:
        """Plot bounds history.

        Args:
            axe: The figure axes.
            minlp_sol: The current optimum objective history.
            milp_sol: The lower bound history.
            upper_bounds: The upper bound history.
            iteration: The vector of main problem iteration.
            is_feasible: Whether the lower level is feasible at each iteration.
            font_size: The font size.
            from_iter: The iteration from which the plot should start.
        """
        n_iter = max(iteration)
        obj_name = self.optimization_problem.objective_name

        axe.xaxis.set_major_locator(MaxNLocator(integer=True))

        axe.grid(True)
        axe.set_xlim([from_iter + 0.5, n_iter + 0.5])
        axe.set_xlabel("iterations", fontsize=font_size)
        axe.set_ylabel(obj_name, fontsize=font_size)
        axe.plot(
            iteration[is_feasible.astype(bool)],
            minlp_sol[is_feasible.astype(bool)],
            label=self.PRIMAL_SOL,
            color="blue",
            marker="*",
            linestyle="",
        )  # where='post',
        if sum(~is_feasible.astype(bool)) > 0:
            axe.plot(
                iteration[~is_feasible.astype(bool)],
                minlp_sol[~is_feasible.astype(bool)],
                label="unfeasible solution",
                color="red",
                marker="*",
                linestyle="",
            )  # where='post',

        axe.step(
            iteration[from_iter:],
            milp_sol[from_iter:],
            label=self.LOWER_BOUND,
            color="red",
            where="post",
        )
        axe.step(
            iteration[from_iter:],
            upper_bounds[from_iter:],
            label=self.UPPER_BOUND,
            color="green",
            where="post",
        )
        axe.plot(
            [iteration[-1]],
            [upper_bounds[-1]],
            linestyle="",
            color="g",
            marker="*",
            markersize=12,
            label="optimum",
        )
        axe.legend(numpoints=1, fontsize=font_size)

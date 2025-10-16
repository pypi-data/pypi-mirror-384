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
"""The bilevel master OuterApproximation settings module."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003

from gemseo.algos.opt.base_gradient_based_algorithm_settings import (
    BaseGradientBasedAlgorithmSettings,
)
from gemseo.algos.opt.base_optimizer_settings import BaseOptimizerSettings
from numpy import inf
from pydantic import Field
from pydantic import NonNegativeFloat
from pydantic import NonNegativeInt
from pydantic import PositiveFloat
from pydantic import PositiveInt
from pydantic import StrictBool


class BiLevelMasterOuterApproximation_Settings(  # noqa: N801
    BaseOptimizerSettings, BaseGradientBasedAlgorithmSettings
):
    """The BiLevel Master OuterApproximation settings."""

    _TARGET_CLASS_NAME = "BILEVEL_MASTER_OUTER_APPROXIMATION"

    normalize_design_space: bool = Field(
        default=False,
        frozen=True,
        description=(
            "The design space normalization must be ``False``. It cannot be changed."
        ),
    )

    upper_bound_stall: NonNegativeInt = Field(
        default=10,
        description=(
            """The maximum number of main problem iterations
            not changing the upper bound."""
        ),
    )

    number_of_parallel_points: PositiveInt = Field(
        default=1,
        description=(
            "The number of parallel points to evaluate in the master problem."
        ),
    )

    upper_bound: float = Field(default=inf, description="The initial upper bound.")

    ub_tol: NonNegativeFloat = Field(
        default=1.0e-3,
        description="The tolerance between upper bound and lower bound.",
    )

    posa: PositiveFloat = Field(
        default=1.0,
        description="The post-optimal sensitivity amplification constant.",
    )

    adapt: StrictBool = Field(
        default=False, description="Whether to exploit adaptative convexification."
    )
    scipy: StrictBool = Field(
        default=False, description="Whether to use Scipy as MILP solver."
    )
    min_dfk: NonNegativeFloat = Field(
        default=0,
        description="The convexity margin used by adaptive convexification.",
    )

    time_limit_milliseconds: NonNegativeInt | None = Field(
        default=None,
        description=(
            "The maximum execution time in milliseconds. "
            "If None, do not set any time limit."
        ),
    )
    constraint_history_size: Mapping[str, NonNegativeInt] | None = Field(
        default=None, description="The size of the history per constraint name."
    )
    presolve: StrictBool = Field(
        default=True,
        description=(
            "Whether to attempt to detect infeasibility,"
            "unboundedness or problem simplifications before solving."
            "Refer to the SciPy documentation for more details."
        ),
    )

    mip_rel_gap: NonNegativeFloat = Field(
        default=0.0,
        description=(
            "Termination criterion for MIP solver: solver will terminate"
            "when the gap between the primal objective value and the dual objective"
            "bound, scaled by the primal objective value, is <= mip_rel_gap."
        ),
    )

    distance_filter_ratio: NonNegativeFloat | None = Field(
        default=None,
        description=(
            "The ratio between current step and the history filter. "
            "If None, do not apply any filter."
        ),
    )

    gradient_free: StrictBool = Field(
        default=False, description="Whether to use sensitivities."
    )
    bilateral_adapt: StrictBool = Field(default=False, description="")
    disp: StrictBool = Field(default=False, description="")  # Is it used?

    convexification_constant: float = Field(default=0.0, description="")
    feasible_history_size: PositiveInt = Field(default=1000, description="")
    infeasible_history_size: NonNegativeInt = Field(default=1000, description="")
    step_decreasing_activation: PositiveInt = Field(default=3, description="")
    constraint_scaling: NonNegativeFloat = Field(default=1000, description="")
    node_limit: PositiveInt = Field(
        default=10_000_000,
        description="For MILP solver, the maximal number of nodes.",
    )
    max_step: PositiveInt = Field(default=10, description="")
    min_step: PositiveInt = Field(default=1, description="")
    number_of_processes: PositiveInt = Field(default=1, description="")

    log_milp: bool = Field(default=True, description="Whether to log the MILP problem.")

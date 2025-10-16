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
"""The outer approximation settings module."""

from __future__ import annotations

from pydantic import Field
from pydantic import NonNegativeFloat

from gemseo_bilevel_outer_approximation.algos.opt.bilevel_master_outer_approximation.bilevel_master_outer_approximation_settings import (  # noqa: E501
    BiLevelMasterOuterApproximation_Settings,
)


class OuterApproximation_Settings(BiLevelMasterOuterApproximation_Settings):  # noqa: N801
    """The Outer Approximation settings."""

    _TARGET_CLASS_NAME = "OuterApproximation_APPROXIMATION"

    parallel_exploration_factor: NonNegativeFloat = Field(
        default=0.0,
        description="""""",
    )

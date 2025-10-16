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
"""The Ortools MILP settings module."""

from __future__ import annotations

from functools import partial

from gemseo.algos.opt.base_milp_settings import BaseMILPSettings
from gemseo.algos.opt.base_optimizer_settings import BaseOptimizerSettings
from gemseo.utils.pydantic import copy_field
from pydantic import Field
from pydantic import NonNegativeFloat
from pydantic import NonNegativeInt

copy_field_opt = partial(copy_field, model=BaseOptimizerSettings)


class OrtoolsMilp_Settings(BaseMILPSettings):  # noqa: N801
    """The Ortools MILP settings."""

    _TARGET_CLASS_NAME = "OrtoolsMILP"

    milp_time_limit: NonNegativeInt | None = Field(
        default=None,
        description=(
            "Maximum amount of seconds allowed for the optimization. "
            "If None, do not set any time limit for the MILP solver."
        ),
    )

    eq_tolerance: NonNegativeFloat = copy_field_opt("eq_tolerance", default=1e-3)

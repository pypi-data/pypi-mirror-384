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
"""The extended Scipy MILP settings."""

from __future__ import annotations

from gemseo.algos.opt.scipy_milp.settings.scipy_milp_settings import SciPyMILP_Settings
from pydantic import Field
from pydantic import NonNegativeInt


class ExtendedScipyMILP_Settings(SciPyMILP_Settings):  # noqa: D101, N801
    """The extended Scipy MILP settings."""

    _TARGET_CLASS_NAME = "ExtendedScipyMILP"

    milp_time_limit: NonNegativeInt | None = Field(
        default=None,
        description=(
            "Maximum amount of seconds allowed for the optimization. "
            "If None, do not set any time limit for the MILP solver."
        ),
    )

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
"""The extended Scipy Milp module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from gemseo.algos.opt.scipy_milp.scipy_milp import ScipyMILP
from gemseo.algos.opt.scipy_milp.scipy_milp import ScipyMILPAlgorithmDescription

from gemseo_bilevel_outer_approximation.algos.opt.scipy_milp.extended_scipy_milp_settings import (  # noqa: E501
    ExtendedScipyMILP_Settings,
)


@dataclass
class ExtendedScipyMILPAlgorithmDescription(ScipyMILPAlgorithmDescription):
    """The description of the Extended SciPy MILP library."""

    Settings: type[ExtendedScipyMILP_Settings] = ExtendedScipyMILP_Settings
    """The option validation model for SciPy linear programming library."""


class ExtendedScipyMILP(ScipyMILP):
    """The extended Scipy MILP library."""

    ALGORITHM_INFOS: ClassVar[dict[str, ExtendedScipyMILPAlgorithmDescription]] = {
        "Scipy_MILP": ExtendedScipyMILPAlgorithmDescription(
            algorithm_name="Branch & Cut algorithm",
            description=("Mixed-integer linear programming"),
            internal_algorithm_name="milp",
            website="https://docs.scipy.org/doc/scipy/reference/scipy.optimize.milp.html",
        ),
    }

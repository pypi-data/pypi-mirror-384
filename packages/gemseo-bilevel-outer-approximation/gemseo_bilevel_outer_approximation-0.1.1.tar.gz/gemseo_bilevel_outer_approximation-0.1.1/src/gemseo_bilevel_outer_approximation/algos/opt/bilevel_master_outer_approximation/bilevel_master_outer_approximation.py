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
"""Bi-level Outer Approximation library wrapper."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.algos.opt.base_optimization_library import BaseOptimizationLibrary
from gemseo.algos.opt.base_optimization_library import OptimizationAlgorithmDescription

from gemseo_bilevel_outer_approximation.algos.opt.bilevel_master_outer_approximation.bilevel_master_outer_approximation_settings import (  # noqa: E501
    BiLevelMasterOuterApproximation_Settings,
)
from gemseo_bilevel_outer_approximation.algos.opt.core.bilevel_outer_approximation import (  # noqa: E501
    BiLevelOuterApproximation,
)

if TYPE_CHECKING:
    from gemseo.algos.optimization_problem import OptimizationProblem

LOGGER = logging.getLogger(__name__)


@dataclass
class BiLevelMasterOuterApproximationAlgorithmDescription(
    OptimizationAlgorithmDescription
):
    """The description of BiLevelMasterOuterApproximation."""

    library_name: str = "BiLevelMasterOuterApproximation"


class BiLevelMasterOuterApproximation(
    BaseOptimizationLibrary[BiLevelMasterOuterApproximation_Settings]
):
    """Bi-level Outer Approximation optimization library interface."""

    lib_dict: dict[str, dict[Any, Any]]
    """The optimization library for input problem validation."""

    ALGORITHM_INFOS: ClassVar[
        dict[str, BiLevelMasterOuterApproximationAlgorithmDescription]
    ] = {
        "BILEVEL_MASTER_OUTER_APPROXIMATION": BiLevelMasterOuterApproximationAlgorithmDescription(  # noqa: E501
            algorithm_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
            description="BILEVEL_MASTER_OUTER_APPROXIMATION",
            handle_equality_constraints=True,
            handle_inequality_constraints=True,
            handle_integer_variables=True,
            internal_algorithm_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
            require_gradient=False,
            positive_constraints=False,
            Settings=BiLevelMasterOuterApproximation_Settings,
        )
    }

    def _run(self, problem: OptimizationProblem) -> tuple[Any, Any]:
        self._f_tol_tester.relative = self._settings.ftol_rel
        self._f_tol_tester.absolute = self._settings.ftol_abs
        return BiLevelOuterApproximation(problem).optimize(
            **self._settings.model_dump()
        ), None

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
#        :author: Simone Coniglio
"""Bi-level Outer Approximation library wrapper."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from gemseo.algos.opt.base_optimization_library import BaseOptimizationLibrary
from gemseo.algos.opt.base_optimization_library import OptimizationAlgorithmDescription

from gemseo_bilevel_outer_approximation.algos.opt.core.outer_approximation_optimizer import (  # noqa: E501
    OuterApproximationOptimizer,
)
from gemseo_bilevel_outer_approximation.algos.opt.outer_approximation.outer_approximation_settings import (  # noqa: E501
    OuterApproximation_Settings,
)

if TYPE_CHECKING:
    from gemseo.algos.optimization_problem import OptimizationProblem

LOGGER = logging.getLogger(__name__)


class OuterApproximationLibrary(BaseOptimizationLibrary[OuterApproximation_Settings]):
    """Bi-level Outer Approximation optimization library interface."""

    ALGORITHM_INFOS: ClassVar[dict[str, OptimizationAlgorithmDescription]] = {
        "OUTER_APPROXIMATION": OptimizationAlgorithmDescription(
            "OUTER_APPROXIMATION",
            "OUTER_APPROXIMATION",
            "OUTER_APPROXIMATION",
            require_gradient=False,
            handle_equality_constraints=True,
            handle_inequality_constraints=True,
            positive_constraints=False,
            handle_integer_variables=True,
            Settings=OuterApproximation_Settings,
        )
    }

    def _run(self, problem: OptimizationProblem) -> tuple[Any, Any]:
        self._f_tol_tester.relative = self._settings.ftol_rel
        self._f_tol_tester.absolute = self._settings.ftol_abs
        return OuterApproximationOptimizer(problem).optimize(
            **self._settings.model_dump()
        ), None

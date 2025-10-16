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
"""Corrected convexification of a GEMSEO discipline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.discipline import Discipline
from numpy import array
from numpy import reshape
from numpy import sum as np_sum

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.typing import StrKeyMapping

    from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
        CatalogueDesignSpace,
    )


class ConvexificationCorrection(Discipline):
    """Class that compute the convexification correction."""

    convexification: float
    """The convexification constant."""
    catalogue_size: list[int]
    """The catalogue sizes."""
    variables: Iterable[str]
    """The variables to be convexified.

    If None, all cat. variables are convexified.
    """

    def __init__(
        self,
        design_space: CatalogueDesignSpace,
        variables: Iterable[str],
        convexification: float = 0.0,
    ) -> None:
        """
        Args:
            design_space: The catalogue design space of the optimization problem.
            variables: The variables to be convexified.
            convexification: The convexification constant.
        """  # noqa: D205, D212
        super().__init__()
        output_names = ["convexification"]
        self.variables = variables
        self.catalogue_size = [design_space.n_catalogues[var] for var in variables]
        self.convexification = convexification
        x_dict = design_space.get_current_value(as_dict=True, variable_names=variables)
        self.input_grammar.update_from_names(variables)
        self.output_grammar.update_from_names(output_names)
        self.default_input_data.update(x_dict)
        self.linearization_mode = "finite_differences"

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        categorical_variables = [input_data[variable] for variable in self.variables]
        correction = 0.0
        if self.convexification > 0.0:
            for cat_var, cat_size in zip(
                categorical_variables, self.catalogue_size, strict=False
            ):
                number_of_components = int(len(cat_var) / cat_size)
                cat_var = reshape(cat_var, (number_of_components, cat_size))
                correction += (
                    self.convexification
                    * np_sum(cat_var * (cat_var - 1))
                    / float(number_of_components)
                )
        return {"convexification": array([correction])}

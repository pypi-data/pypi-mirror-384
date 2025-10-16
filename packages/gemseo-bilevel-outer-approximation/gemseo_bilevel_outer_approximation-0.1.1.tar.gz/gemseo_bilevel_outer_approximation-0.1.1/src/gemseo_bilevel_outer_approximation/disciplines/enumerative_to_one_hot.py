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

"""Transformation of enumerative design variables into one hot encoding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from numpy import eye
from numpy import zeros

from gemseo_bilevel_outer_approximation.disciplines.base_catalogue_discipline import (
    BaseCatalogueDiscipline,
)

if TYPE_CHECKING:
    from gemseo.typing import StrKeyMapping
    from numpy import ndarray


class EnumerativeToOneHot(BaseCatalogueDiscipline):
    """Discipline that transform enumerative design variable into one hot encoding."""

    def __init__(
        self,
        n_components: int,
        catalogue: ndarray,
        variable_name: str,
        output_name: str,
        name: str = "",
    ) -> None:
        """
        Args:
            n_components: The size of the categorical design variable.
            catalogue: The catalogue of possible choices.
            variable_name: The input variable name.
            output_name: The output variable name.
        """  # noqa: D212, D205
        super().__init__(
            n_components=n_components,
            catalogue=catalogue,
            variable_name=variable_name,
            output_name=output_name,
            name=name,
        )
        self.input_grammar.update_from_data({variable_name: zeros(n_components)})
        self._n_catalogues = len(catalogue)
        self.output_grammar.update_from_data({
            output_name: zeros(self._n_catalogues * n_components),
        })

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        enum = input_data[self._variable_name]
        eeye = eye(self._n_catalogues)
        out = zeros((self._n_catalogues * self._n_components,))
        for k in range(len(enum)):
            out[k * self._n_catalogues : (k + 1) * self._n_catalogues] = eeye[
                :, enum[k]
            ]
        return {self._output_name: out}

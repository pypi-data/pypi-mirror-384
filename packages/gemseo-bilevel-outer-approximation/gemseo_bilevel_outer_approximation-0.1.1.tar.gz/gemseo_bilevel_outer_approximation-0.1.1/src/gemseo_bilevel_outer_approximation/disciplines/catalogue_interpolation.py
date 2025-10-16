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

"""Catalogue interpolation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from numpy import atleast_2d
from numpy import eye
from numpy import kron
from numpy import reshape
from numpy import tile
from numpy import zeros

from gemseo_bilevel_outer_approximation.disciplines.base_catalogue_discipline import (
    BaseCatalogueDiscipline,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.typing import StrKeyMapping
    from numpy import ndarray


class CatalogueInterpolation(BaseCatalogueDiscipline):
    """Discipline for catalogue interpolation."""

    __minimum_value: float
    """The ensured minimum interpolated."""

    __ensure_minimum: bool
    """True, if the interpolation on the catalog should ensure a minimum value."""

    __contrast: float
    """The ratio between the ensured minimum and the minimum value in the catalog."""

    __penalty: float
    """The exponent adopted by the SIMP approach for intermediate choice
    penalization."""

    def __init__(
        self,
        n_components: int,
        catalogue: ndarray[Any],
        variable_name: str,
        output_name: str,
        penalty: float = 1.0,
        contrast: float = 1000.0,
        ensure_minimum: bool = False,
    ) -> None:
        """
        Args:
            n_components:  The number of component of the catalog design variables.
            catalogue: The catalog used for the interpolation.
            variable_name: The name of the categorical variable in input.
            output_name: The name of discipline output.
            penalty: The exponent adopted by the SIMP approach for intermediate choice
                penalization.
            contrast: The ratio between the ensured minimum and the minimum value in the
                catalog.
            ensure_minimum: True, if the interpolation on the catalog should ensure a
                minimum value.
        """  # noqa: D212, D205
        super().__init__(
            n_components=n_components,
            catalogue=catalogue,
            variable_name=variable_name,
            output_name=output_name,
            name=output_name + " interpolator",
        )

        self.__penalty = penalty
        self.__contrast = contrast
        self.__ensure_minimum = ensure_minimum
        if not self.__ensure_minimum:
            self.__minimum_value = 0.0
        else:
            self.__minimum_value = min(self._catalogue.flatten()) / self.__contrast

        default_var = zeros((n_components, self._n_catalogues))
        default_var[:, 0] = 1
        self.io.input_grammar.update_from_names([variable_name])
        self.io.output_grammar.update_from_names([output_name])
        self.default_input_data = {
            variable_name: default_var.flatten(),
        }

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        variable_0 = input_data[self._variable_name]
        variable_0[variable_0 < 0] = 0
        variable = (
            reshape(variable_0, (self._n_components, self._n_catalogues))
            ** self.__penalty
        )
        catalogue = atleast_2d(self._catalogue).T
        return {
            self._output_name: (
                variable.dot(catalogue - self.__minimum_value)
            ).flatten()
            + self.__minimum_value
        }

    def _compute_jacobian(
        self,
        input_names: Iterable[str] = (),
        output_names: Iterable[str] = (),
    ) -> None:
        variable = self.io.data[self._variable_name]
        variable = reshape(variable, (self._n_components, self._n_catalogues))
        self._init_jacobian(
            init_type=self.InitJacobianType.SPARSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        self.jac = {}
        self.jac[self._output_name] = {}
        self.jac[self._output_name][self._variable_name] = kron(
            eye(self._n_components), self._catalogue - self.__minimum_value
        ) * tile(
            self.__penalty * variable ** (self.__penalty - 1), (1, self._n_components)
        )

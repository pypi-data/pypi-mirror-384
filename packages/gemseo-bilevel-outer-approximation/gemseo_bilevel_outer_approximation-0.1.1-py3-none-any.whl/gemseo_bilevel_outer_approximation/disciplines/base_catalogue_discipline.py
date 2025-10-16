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

"""To one hot encoding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.discipline import Discipline

if TYPE_CHECKING:
    from numpy import ndarray


class BaseCatalogueDiscipline(Discipline):
    """Base discipline that deals with catalogues."""

    _n_catalogues: int
    """The number of catalogues."""
    _output_name: str
    """The output variable name."""
    _variable_name: str
    """The input variable name."""
    _catalogue: ndarray
    """The catalogue of possible choices."""
    _n_components: int
    """The size of the categorical design variable."""

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
        """  # noqa: D205, D212
        super().__init__(name=name)
        self._n_components = n_components
        self._catalogue = catalogue
        self._variable_name = variable_name
        self._output_name = output_name
        self._n_catalogues = len(catalogue)

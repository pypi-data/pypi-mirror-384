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

"""Discrete catalogue converter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from numpy import ndarray
    from sklearn.preprocessing import LabelEncoder
    from sklearn.preprocessing import OneHotEncoder

    from gemseo_bilevel_outer_approximation.disciplines.hypercube_to_one_hot import (
        HypercubeToOneHot,
    )


class DiscretCatalogConverter:
    """Class converting discrete variable to catalog arrays."""

    __onehot_encoder: OneHotEncoder
    """The one-hot encoder object."""
    __label_encoder: LabelEncoder
    """The label encoder object."""
    __catalogue: ndarray
    """The catalogue array."""
    __name: str
    """The name of the categorical variable."""
    __use_hyper_cube: bool
    """True if use hyper cube representation."""
    __hypercube_to_one_hot: HypercubeToOneHot | None
    """The HypercubeToOneHot discipline. If None, it is not used."""
    __names_to_n_components: dict[str, int]
    """The dimension of the categorical variable."""
    __names_to_n_catalogues: dict[str, int]
    """The number of element in the catalogue for each variable."""

    def __init__(
        self,
        onehot_encoder: OneHotEncoder,
        label_encoder: LabelEncoder,
        catalogue: ndarray,
        name: str,
        use_hyper_cube: bool,
        names_to_n_components: dict[str, int],
        names_to_n_catalogues: dict[str, int],
        hypercube_to_one_hot: HypercubeToOneHot | None = None,
    ) -> None:
        """
        Args:
            onehot_encoder: The one-hot encoder object.
            label_encoder: The label encoder object.
            catalogue: The catalogue array.
            name: The name of the categorical variable.
            use_hyper_cube: Whether to use a hyper cube representation.
            names_to_n_components: The dimension of the categorical variable.
            names_to_n_catalogues: The number of element in the catalogue.
            hypercube_to_one_hot: The HypercubeToOneHot discipline.
                If None, it is not used.
        """  # noqa: D205, D212
        self.__names_to_n_catalogues = names_to_n_catalogues
        self.__names_to_n_components = names_to_n_components
        self.__hypercube_to_one_hot = hypercube_to_one_hot
        self.__use_hyper_cube = use_hyper_cube
        self.__name = name
        self.__catalogue = catalogue
        self.__label_encoder = label_encoder
        self.__onehot_encoder = onehot_encoder

    def compute(self, x: ndarray) -> ndarray:
        """Translate binary variable array into a catalog selection.

        Args:
            x: The integer variable vector.

        Returns:
            The solution in terms of catalog choices.
        """
        if not self.__use_hyper_cube:
            return self.__catalogue[
                (
                    self.__label_encoder.inverse_transform(
                        self.__onehot_encoder.inverse_transform(
                            x.reshape(
                                self.__names_to_n_components[self.__name],
                                self.__names_to_n_catalogues[self.__name],
                            )
                        )
                    )
                ).flatten()
            ]
        return self.__catalogue[
            (
                self.__label_encoder.inverse_transform(
                    self.__onehot_encoder.inverse_transform(
                        self.__hypercube_to_one_hot.execute({self.__name: x})[
                            self.__name + "_onehot"
                        ].reshape(
                            self.__names_to_n_components[self.__name],
                            self.__names_to_n_catalogues[self.__name],
                        )
                    )
                )
            ).flatten()
        ]

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
"""Catalogue Design Space class."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any

from gemseo.algos.design_space import DesignSpace
from gemseo.core.chains.chain import MDOChain
from numpy import arange
from numpy import array
from numpy import atleast_1d
from numpy import concatenate
from numpy import ones
from numpy import ones_like
from numpy import str_
from numpy import where
from numpy import zeros_like
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder

from gemseo_bilevel_outer_approximation.algos.design_space.discrete_catalogue_converter import (  # noqa: E501
    DiscretCatalogConverter,
)
from gemseo_bilevel_outer_approximation.disciplines.catalogue_interpolation import (
    CatalogueInterpolation,
)
from gemseo_bilevel_outer_approximation.disciplines.hypercube_to_one_hot import (
    HypercubeToOneHot,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable

    from gemseo.core.discipline import Discipline
    from numpy import ndarray


class CatalogueDesignSpace(DesignSpace):
    """The class for design space with mixed integer design variables."""

    discrete_var_to_catalogue_choice: dict[str, Any]
    """The translator from discrete variables to catalog choice."""

    hyper_cube_discipline: dict[str, HypercubeToOneHot]
    """The disciplines translating hypercube design variables to one-hot encoding."""

    hypercube: dict[str, bool]
    """Whether the shape function penalization is used per design variable."""

    integer_encoding: dict[str, Any]
    """The integer encoders per catalog design variable."""

    categorical_variables: list[str]
    """The categorical design variables."""

    n_components: dict[str, int]
    """The number of components per catalog design variable."""

    catalogues: dict[str, ndarray[Any]]
    """The catalog per catalog design variable."""

    n_catalogues: dict[str, int]
    """The number of catalog choice per catalog design variable."""

    __catalogue_weights: dict[str, int | float]
    """The weights of the catalogue values of a categorical variable."""

    def __init__(self, name: str = "") -> None:  # noqa: D107
        super().__init__(name)
        self.catalogues = {}
        self.n_catalogues = {}
        self.n_components = {}
        self.categorical_variables = []
        self.integer_encoding = {}
        self.hypercube = {}
        self.hyper_cube_discipline = {}
        self.discrete_var_to_catalogue_choice = {}
        self.__catalogue_weights = {}

    def add_categorical_variable(
        self,
        name: str,
        value: ndarray | Iterable[int | str | float],
        catalogue: Iterable[Any],
        hyper_cube: bool | None = False,
        repeat_vertex: bool = False,
        weights: ndarray[int | float] | None = None,
    ) -> None:
        """Add categorical design variables to the design space.

        Args:
            name: The name of the design variable to be added.
            value: The design variable value.
            catalogue: The set of elements among which the design variables take values.
            hyper_cube: True if hypercube shape function should be used.
            repeat_vertex: If True, repeat the vertices on unused catalog choices.
            weights: The weights of the catalogue values in the computation
                of the distance between two values of the categorical variable.
                If ``None``: if the catalogue values are numerical use them as weights,
                otherwise set every weight to one.
        """
        # 1) store the number of catalogue
        self.n_catalogues[name] = len(catalogue)
        self.n_components[name] = len(value)
        self.categorical_variables.append(name)
        # 2) compute the one hot encoding of value
        catalogue_array = array(catalogue)
        catalogue_data = arange(len(catalogue))
        label_encoder = LabelEncoder()
        integer_encoded = label_encoder.fit_transform(catalogue_data)
        self.catalogues[name] = array(catalogue)[integer_encoded]
        self.integer_encoding[name] = integer_encoded
        self.hypercube[name] = hyper_cube
        onehot_encoder = OneHotEncoder(sparse_output=False)
        integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
        onehot_encoder.fit_transform(integer_encoded)
        value_list = [where(val == catalogue_array)[0][0] for val in value]
        integer_encoded_value = label_encoder.transform(array(value_list))
        integer_encoded_value = integer_encoded_value.reshape(
            len(integer_encoded_value), 1
        )

        onehot_encoded_value = (
            onehot_encoder.transform(integer_encoded_value).flatten().astype(float)
        )
        if not hyper_cube:
            self.discrete_var_to_catalogue_choice[name] = (
                self.__get_discrete_var_to_catalogue_choice_function(
                    onehot_encoder, label_encoder, catalogue_array, name, hyper_cube
                )
            )
            # 3) compute lb and upper ub
            l_b = zeros_like(onehot_encoded_value).astype(float)
            u_b = ones_like(onehot_encoded_value).astype(float)
            # 3) Add a design Variable to the design space (with one hot encoding)
            self.add_variable(
                name=name,
                lower_bound=l_b,
                upper_bound=u_b,
                value=onehot_encoded_value,
                type_=self.DesignVariableType.FLOAT,
                size=len(onehot_encoded_value),
            )
        else:
            hyp = HypercubeToOneHot(
                n_components=len(value),
                catalogue=catalogue,
                variable_name=name,
                output_name=name + "_onehot",
                repeat_vertex=repeat_vertex,
            )
            hyp_var = concatenate([
                array(list(hyp.cat_dict.keys())[list(hyp.cat_dict.values()).index(val)])
                for val in value
            ]).astype(float)
            self.hyper_cube_discipline[name] = hyp
            self.discrete_var_to_catalogue_choice[name] = (
                self.__get_discrete_var_to_catalogue_choice_function(
                    onehot_encoder,
                    label_encoder,
                    catalogue_array,
                    name,
                    hyper_cube,
                    hyp,
                )
            )
            # 3) compute lb and upper ub
            l_b = zeros_like(hyp_var).astype(float)
            u_b = ones_like(hyp_var).astype(float)
            # 3) Add a design Variable to the design space (with one hot encoding)
            self.add_variable(
                name=name,
                lower_bound=l_b,
                upper_bound=u_b,
                value=hyp_var,
                type_=self.DesignVariableType.FLOAT,
                size=len(hyp_var),
            )

        if weights is None and catalogue_array.dtype.type is str_:
            self.__catalogue_weights[name] = ones(len(catalogue))
        elif weights is None:
            self.__catalogue_weights[name] = catalogue
        else:
            self.__catalogue_weights[name] = weights

    def get_catalogue_weights(self, name: str) -> ndarray[int | float]:
        """Return the weights of the catalogue values of a categorical variable.

        Args:
            name: The name of the categorical variable.

        Returns:
            The weights of the catalogue values of the categorical variable.
        """
        return self.__catalogue_weights[name]

    def __get_discrete_var_to_catalogue_choice_function(
        self,
        onehot_encoder: OneHotEncoder,
        label_encoder: LabelEncoder,
        catalogue_array: ndarray,
        name: str,
        hyper_cube: bool,
        hyp: HypercubeToOneHot = None,
    ) -> Callable:
        """Provide discrete variable to catalog choice converter method.

        Args:
            onehot_encoder: The one-hot encoder object.
            label_encoder: The label encoder object.
            catalogue_array: The catalogue array.
            name: The name of the categorical variable.
            hyper_cube: True if use hyper cube representation.
            hyp: The HypercubeToOneHot discipline, If None, it is not used.

        Returns:
            The function that converts vector of discrete variables in vector of catalog
            choices.
        """
        return DiscretCatalogConverter(
            onehot_encoder,
            label_encoder,
            catalogue_array,
            name,
            hyper_cube,
            self.n_components,
            self.n_catalogues,
            hyp,
        ).compute

    def filter_non_categorical(self) -> CatalogueDesignSpace:
        """Filter the design space to keep a sub-set of categorical variables.

        Returns:
            The filtered design space.
        """
        variable_names = deepcopy(self.variable_names)
        for name in variable_names:
            if name not in self.categorical_variables:
                self.remove_variable(name)
        return self

    def filter_by_type(
        self,
        types_to_keep: DesignSpace.DesignVariableType
        | Iterable[DesignSpace.DesignVariableType],
    ) -> CatalogueDesignSpace:
        """Filter the design space to keep a sub-set of variables of type <type>.

        Args:
            types_to_keep: The types of variables to be kept in design space.

        Returns:
            A filtered copy of the original CatalogueDesignSpace.
        """
        types_to_keep = atleast_1d(types_to_keep)

        variables_to_keep = []
        for variable_name in self.variable_names:
            type_variable = self.get_type(variable_name)
            if type_variable in types_to_keep:
                variables_to_keep.append(variable_name)

        return self.filter(variables_to_keep, copy=True)

    def get_catalogue_interpolation_discipline(
        self,
        penalty: float,
        variable: str,
        output: str,
        catalogue: ndarray,
        contrast: float = 1000.0,
        ensure_minimum: bool = False,
    ) -> Discipline:
        """Return a discipline that interpolates among a continuous catalog.

        Args:
            penalty: The exponent adopted by the SIMP approach for intermediate choice
                penalization.
            variable: The name of the categorical design variable.
            output: The name of discipline output.
            catalogue: The catalog used for the interpolation.
            ensure_minimum: True, if the interpolation on the catalog should ensure a
                minimum value.
            contrast: The ratio between the ensured minimum and the minimum value in the
                catalog.

        Returns:
            A discipline that compute from relaxed one hot encoding or hypercube
            design space variable the catalog output.
        """
        if not self.hypercube[variable]:
            return CatalogueInterpolation(
                variable_name=variable,
                n_components=self.n_components[variable],
                catalogue=catalogue[self.integer_encoding[variable]],
                penalty=penalty,
                output_name=output,
                contrast=contrast,
                ensure_minimum=ensure_minimum,
            )

        ohi = CatalogueInterpolation(
            variable_name=variable + "_onehot",
            n_components=self.n_components[variable],
            catalogue=catalogue,
            penalty=penalty,
            output_name=output,
            contrast=contrast,
            ensure_minimum=ensure_minimum,
        )
        return MDOChain(
            disciplines=[self.hyper_cube_discipline[variable], ohi],
            name=variable + " hc interpolator",
        )

    def get_catalogue_interpolation_discipline_from_dict(
        self,
        variable: str,
        dictionary: dict[str, dict[str, Any]],
        contrast: float = 1000.0,
        ensure_minimum: bool = False,
    ) -> MDOChain:
        """Generate a discipline that interpolates among a continuous catalog.

        Args:
            ensure_minimum: True, if the interpolation on the catalog should ensure a
                minimum value.
            contrast: The ratio between the ensured minimum and the minimum value in the
                catalog.
            variable: The name of the categorical design variable.
            dictionary: The variable containing output, catalog and penalty information.

        Returns:
            A gemseo discipline that compute from relaxed one hot encoding or hypercube
            design space variable all catalogues outputs in the dictionary.
        """
        discipline_list = []
        if self.hypercube[variable]:
            discipline_list.append(self.hyper_cube_discipline[variable])
        for output, sub_dict in dictionary.items():
            catalogue, penalty = sub_dict["catalogue"], sub_dict["penalty"]
            if not self.hypercube[variable]:
                discipline_list.append(
                    CatalogueInterpolation(
                        variable_name=variable,
                        n_components=self.n_components[variable],
                        catalogue=catalogue[self.integer_encoding[variable]],
                        penalty=penalty,
                        output_name=output,
                        contrast=contrast,
                        ensure_minimum=ensure_minimum,
                    )
                )
            else:
                discipline_list.append(
                    CatalogueInterpolation(
                        variable_name=variable + "_onehot",
                        n_components=self.n_components[variable],
                        catalogue=catalogue,
                        penalty=penalty,
                        output_name=output,
                        contrast=contrast,
                        ensure_minimum=ensure_minimum,
                    )
                )
        return MDOChain(
            disciplines=discipline_list,
            name=variable + " interpolator",
        )

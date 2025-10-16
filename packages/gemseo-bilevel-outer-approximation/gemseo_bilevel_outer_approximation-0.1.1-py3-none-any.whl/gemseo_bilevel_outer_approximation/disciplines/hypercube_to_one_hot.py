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

"""Transformation of hypercube design variables into one hot encoding."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING
from typing import Any

from numpy import array
from numpy import atleast_2d
from numpy import ceil
from numpy import eye
from numpy import log2
from numpy import ones
from numpy import prod
from numpy import reshape
from numpy import sqrt
from numpy import sum as np_sum
from numpy import tile
from numpy import zeros
from numpy import zeros_like
from numpy.ma import argmin
from scipy.linalg import block_diag

from gemseo_bilevel_outer_approximation.disciplines.base_catalogue_discipline import (
    BaseCatalogueDiscipline,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.typing import StrKeyMapping
    from numpy import ndarray


class HypercubeToOneHot(BaseCatalogueDiscipline):
    """Discipline that transform hypercube design variable into one hot encoding."""

    __repeat_vertex: bool
    """Whether to repeat the vertices on unused catalog choices."""

    __hypercube_dimension: int
    """The hypercube dimension."""

    def __init__(
        self,
        n_components: int,
        catalogue: ndarray[Any],
        variable_name: str,
        output_name: str,
        repeat_vertex: bool = False,
        name: str = "",
    ) -> None:
        """
        Args:
            n_components:The number of component of the catalog design
            variables.
            catalogue: The catalog of the categorical design variable.
            variable_name: The name of the categorical variable in input.
            output_name: The name of the  variable in output.
            repeat_vertex: If True, repeat the vertices on unused catalog choices.
        """  # noqa: D205, D212
        super().__init__(
            n_components=n_components,
            catalogue=catalogue,
            variable_name=variable_name,
            output_name=output_name,
            name=name,
        )
        self.__repeat_vertex = repeat_vertex
        self.__hypercube_dimension = int(ceil(log2(self._n_catalogues)))

        self.shape_function_dict = {k: [k] for k in range(self._n_catalogues)}
        if 2**self.__hypercube_dimension > self._n_catalogues:
            for k in range(2**self.__hypercube_dimension - self._n_catalogues):
                self.shape_function_dict[k].append(self._n_catalogues + k)
            catalogue = array(
                list(catalogue)
                + [
                    catalogue[k]
                    for k in range(2**self.__hypercube_dimension - self._n_catalogues)
                ]
            )
        self.xcsi = zeros((2**self.__hypercube_dimension, self.__hypercube_dimension))
        self._build_xcsi_mat()

        self.io.input_grammar.update_from_data({
            variable_name: zeros(self.__hypercube_dimension * n_components)
        })
        self.io.output_grammar.update_from_data({
            output_name: zeros(2**self.__hypercube_dimension * n_components),
            f"C_{output_name}": array([0.0]),
        })
        eta0 = zeros(self.__hypercube_dimension * n_components)
        self.default_input_data = {variable_name: eta0}
        cat_dict = {}
        one_hot_dict = {}
        for it, key in enumerate(self._catalogue):
            cat_dict[tuple((self.xcsi + 1)[it, :] / 2)] = key
            one_hot_dict[tuple(eye(2**self.__hypercube_dimension)[it, :])] = key
        self.cat_dict = cat_dict
        self.one_hot_dict = one_hot_dict

    def _build_xcsi_mat(self) -> None:
        """Build the xcsi matrix."""
        for m in range(2**self.__hypercube_dimension):
            binary = format(m, "b")
            prefix = "0" * (self.__hypercube_dimension - len(format(m, "b")))
            binary = prefix + binary
            for k in range(self.__hypercube_dimension):
                self.xcsi[m, k] = 2 * int(binary[k]) - 1

    def _run(self, input_data: StrKeyMapping) -> StrKeyMapping | None:
        eta = input_data[self._variable_name]
        eta = -1 + 2 * eta
        hypercube_var_reshaped = reshape(
            eta, (self._n_components, self.__hypercube_dimension)
        )
        shape_function0 = zeros((2**self.__hypercube_dimension, self._n_components))
        for k in range(self._n_components):
            mat = (
                1
                + tile(hypercube_var_reshaped[k, :], (2**self.__hypercube_dimension, 1))
                * self.xcsi
            )
            shape_function0[:, k] = (
                1 / 2**self.__hypercube_dimension * prod(mat, axis=1)
            )
        shape_function = zeros((self._n_catalogues, self._n_components))
        if self.__repeat_vertex and 2**self.__hypercube_dimension > self._n_catalogues:
            for k, val in self.shape_function_dict.items():
                if len(val) > 1:
                    shape_function[k, :] = np_sum(shape_function0[val, :], axis=0)
                else:
                    shape_function[k, :] = shape_function0[val[0], :]
        elif (
            not self.__repeat_vertex
            and 2**self.__hypercube_dimension > self._n_catalogues
        ):
            shape_function[: self._n_catalogues, :] = shape_function0[
                : self._n_catalogues, :
            ] + tile(
                np_sum(shape_function0[self._n_catalogues :, :], axis=0)
                / self._n_catalogues,
                (self._n_catalogues, 1),
            )
        else:
            shape_function = shape_function0

        return {
            self._output_name: shape_function.T.ravel(),
            f"C_{self._output_name}": self._compute_cost(shape_function),
        }

    def _compute_jacobian(
        self,
        input_names: Iterable[str] = (),
        output_names: Iterable[str] = (),
    ) -> None:
        eta = self.io.data[self._variable_name]
        eta = -1 + 2 * eta
        hypercube_var_reshaped = reshape(
            eta, (self._n_components, self.__hypercube_dimension)
        )
        dshape_function_d_hypercube0 = zeros((
            2**self.__hypercube_dimension,
            self._n_components,
            self.__hypercube_dimension,
        ))
        for k in range(self._n_components):
            mat = (
                1
                + tile(hypercube_var_reshaped[k, :], (2**self.__hypercube_dimension, 1))
                * self.xcsi
            )
            for j in range(self.__hypercube_dimension):
                mat_mod = deepcopy(mat)
                mat_mod[:, j] = 1
                dshape_function_d_hypercube0[:, k, j] = (
                    1
                    / 2**self.__hypercube_dimension
                    * prod(mat_mod, axis=1)
                    * self.xcsi[:, j]
                )
        dshape_function_d_hypercube = zeros((
            self._n_catalogues,
            self._n_components,
            self.__hypercube_dimension,
        ))
        if self.__repeat_vertex and 2**self.__hypercube_dimension > self._n_catalogues:
            for k, val in self.shape_function_dict.items():
                if len(val) > 1:
                    dshape_function_d_hypercube[k, :, :] = np_sum(
                        dshape_function_d_hypercube0[val, :, :], axis=0
                    )
                else:
                    dshape_function_d_hypercube[k, :, :] = dshape_function_d_hypercube0[
                        val[0], :, :
                    ]
        elif (
            not self.__repeat_vertex
            and 2**self.__hypercube_dimension > self._n_catalogues
        ):
            dshape_function_d_hypercube[: self._n_catalogues, :, :] = (
                dshape_function_d_hypercube0[: self._n_catalogues, :, :]
                + tile(
                    np_sum(
                        dshape_function_d_hypercube0[self._n_catalogues :, :, :],
                        axis=0,
                    )
                    / self._n_catalogues,
                    (self._n_catalogues, 1, 1),
                )
            )
        else:
            dshape_function_d_hypercube = dshape_function_d_hypercube0
        self._init_jacobian(
            init_type=self.InitJacobianType.SPARSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        self.jac = {self._output_name: {}, f"C_{self._output_name}": {}}
        self.jac[self._output_name][self._variable_name] = 2 * block_diag(
            *(dshape_function_d_hypercube[:, k, :] for k in range(self._n_components))
        )
        self.jac[f"C_{self._output_name}"][self._variable_name] = atleast_2d(
            -2
            * self.io.data[self._output_name].T.dot(
                self.jac[self._output_name][self._variable_name]
            )
        )

    def compute_discrete_solution(self, eta: ndarray) -> ndarray:
        """Compute the closest solution to an intermediate value of input.

        Args:
            eta: The vector of intermediate catalog variables approximating a
                discrete solution.

        Returns:
            The vector of the closest discrete solution.
        """
        # compute the distance of current solution from integer
        eta = reshape(eta, (self._n_components, self.__hypercube_dimension)).T
        discrete_choice_possibilities = list(self.cat_dict.keys())
        discrete_catalogue = zeros((len(self._catalogue), self.__hypercube_dimension))

        for it, dd in enumerate(discrete_choice_possibilities):
            discrete_catalogue[it, :] = array(dd)
        discrete_eta = zeros_like(eta.T)
        it = 0
        for c_eta in eta.T:
            distance = sqrt(
                np_sum(
                    (
                        discrete_catalogue
                        - tile(c_eta, (len(discrete_choice_possibilities), 1))
                    )
                    ** 2,
                    axis=1,
                )
            )
            choice_id = argmin(distance)
            discrete_eta[it, :] = discrete_catalogue[choice_id, :]
            it += 1
        return discrete_eta.ravel()

    @staticmethod
    def _compute_cost(shape_function: ndarray) -> ndarray:
        """Compute a cost function for non discreteness.

        Args:
            shape_function: The vector of hypercube shape functions.

        Returns:
            The cost function for intermediate variables penalization.
        """
        uel = ones((shape_function.shape[1], 1))
        ucat = ones((shape_function.shape[0], 1))
        return (uel.T.dot(uel - (shape_function.T**2).dot(ucat))).flatten()

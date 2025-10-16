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
"""Convexify a GEMSEO discipline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.chains.chain import MDOChain
from gemseo.disciplines.linear_combination import LinearCombination

from gemseo_bilevel_outer_approximation.algos.convexification.convexification_correction import (  # noqa: E501
    ConvexificationCorrection,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from gemseo.core.discipline import Discipline
    from numpy import ndarray

    from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
        CatalogueDesignSpace,
    )


class ConvexificationDiscipline(MDOChain):
    r"""Class that convexifies a discipline output.

    Given a discipline
    :math:`f : (x,y) \rightarrow f\ in \mathbb{R}^{n_{\textrm{outputs}}}`, where the
    continuous inputs are
    :math:`x \in D \subset \mathbb{R}^{n_{\textrm{component}}}` and the relaxed one
    hot encoding inputs are
    :math:`y \in [ 0,1]^{n_{\textrm{component}}\times n_{\textrm{catalogue}}}`;
    Convexification modifies the original discipline as follows:
    :math:`\tilde{f} : (x,y) \rightarrow \tilde{f} \in
    \mathbb{R}^{n_{\textrm{outputs}}}`
    where :math:`\tilde{f}(x,y)=f(x,y) + kC(y)` where :math:`k\geq 0` is the
    convexification constant and
    :math:`C(y) : y \rightarrow C\in\mathbb{R}^{n_{\textrm{outputs}}} | C_i
    \ is \  convex \ and \ C_i (0) = C_i (1) =0
    \forall i =1,2,...,n_{\textrm{outputs}}`
    In this discipline the convex term is chosen to be equal to:

    .. math::

        C_i(y) =\frac{1}{n_{\textrm{component}}n_{\textrm{catalogue}}^2}
        \sum_{j=1}^{n_{\textrm{component}}}\sum_{k=1}^{n_{\textrm{catalogue}}}
        \sum_{m=1}^{n_{\textrm{catalogue}}}{(y^{(j)}_m-I_{m,k})^2-(I_{m,1}-I_{m,k})^2}

    where  :math:`y^{(j)}\in \mathbb{R}^{n_{\textrm{catalogue}}}` represent the
    relaxed one-hot encoded vector of the :math:`j-th` component and I is the
    :math:`n_{\textrm{catalogue}} \times n_{\textrm{catalogue}}` identity matrix.
    """

    default_inputs: dict[str, ndarray]
    """The GEMSEO discipline default inputs dictionary."""

    convexification: float
    """The convexification constant."""

    catalogue_size: Iterable[int]
    """The catalog size per design variable."""

    convexified_outputs: Iterable[str]
    """The discipline outputs to be convexified."""

    variables: Iterable[str]
    """`The discipline inputs to be part of convexification."""

    def __init__(
        self,
        discipline: Discipline,
        design_space: CatalogueDesignSpace,
        variables: Iterable[str] = (),
        convexified_outputs: Iterable[str] = (),
        convexification: float = 0.0,
    ) -> None:
        """
        Args:
            discipline: The GEMSEO discipline that need to be convexified.
            design_space: The catalogue design space of the optimization problem.
            variables: The variables to be convexified.
                If empty, all categorical variables are convexified.
            convexified_outputs: The outputs that need to be convexified.
                If empty, all discipline outputs are convexified.
            convexification: The convexification constant.
        """  # noqa: D205, D212
        self.variables = variables or list(design_space.n_catalogues.keys())
        self.convexified_outputs = convexified_outputs or list(
            discipline.io.output_grammar.names
        )

        output_names = [input_name + "_conv" for input_name in self.convexified_outputs]
        self.catalogue_size = [design_space.n_catalogues[var] for var in variables]
        self.convexification = convexification
        convex_disc = ConvexificationCorrection(
            design_space=design_space,
            variables=self.variables,
            convexification=convexification,
        )
        lcs = [
            LinearCombination(
                input_names=[convexified_output, "convexification"],
                output_name=output_name,
            )
            for convexified_output, output_name in zip(
                self.convexified_outputs, output_names, strict=False
            )
        ]
        super().__init__(disciplines=[convex_disc, *lcs])

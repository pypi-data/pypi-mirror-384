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

"""Convexification module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gemseo.core.chains.chain import MDOChain

from gemseo_bilevel_outer_approximation.algos.convexification.convexification_correction import (  # noqa: E501
    ConvexificationCorrection as ConvexificationCorrection,
)
from gemseo_bilevel_outer_approximation.algos.convexification.convexification_discipline import (  # noqa: E501
    ConvexificationDiscipline,
)

if TYPE_CHECKING:
    from gemseo.algos.design_space import DesignSpace
    from gemseo.core.discipline import Discipline

    from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
        CatalogueDesignSpace as CatalogueDesignSpace,
    )


def build_convexification_chain(
    discipline: Discipline,
    design_space: DesignSpace,
    variables: list[str] = (),
    convexified_outputs: list[str] = (),
    convexification: float = 0.0,
) -> MDOChain:
    """Build a copy of an input discipline, with same input and convexified output.

    Args:
        discipline: The GEMSEO discipline to be copied.
        design_space: The catalog design space.
        variables: The design variables to be considered for convexification.
            If empty, all categorical design variable in design space are used for
            convexification.
        convexified_outputs: The name ot the outputs to be convexified.
            If empty, all discipline outputs are convexified.
        convexification: The convexification constant.

    Returns:
        The MDOChain including original discipline and the convexification discipline.
    """
    convexification_discipline = ConvexificationDiscipline(
        discipline, design_space, variables, convexified_outputs, convexification
    )
    return MDOChain([discipline, convexification_discipline])

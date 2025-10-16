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

from __future__ import annotations

import pytest
from gemseo.core.chains.chain import MDOChain
from numpy import array

from gemseo_bilevel_outer_approximation.algos.convexification import (
    build_convexification_chain,
)


@pytest.fixture(params=[[["f"], (), 10.0], [(), ["alpha_onehot"], 0.0]])
def convexified_chain(analytical_use_case, request):
    """Compute a chain between original discipline and convexified one.

    Args:
        analytical_use_case: The fixture containing both scenario and original
            design space.
        request:The pytest request fixture.
    """
    return build_convexification_chain(
        discipline=analytical_use_case[0].disciplines[0],
        design_space=analytical_use_case[1],
        convexified_outputs=request.param[0],
        variables=request.param[1],
        convexification=request.param[2],
    )


# @pytest.fixture
# def convexified_scenario(analytical_use_case):
#     """Create a convexified scenario."""
#     return convexify_scenario(
#         analytical_use_case[0],
#         design_space=analytical_use_case[1],
#         convexification=1000.0,
#     )


def test_is_instance_convexification(convexified_chain):
    """Test if convexified chain is an MDOChain."""
    assert isinstance(convexified_chain, MDOChain)


def test_convexification_execution(convexified_chain, analytical_use_case):
    """Test if convexified chain is an MDOChain."""
    assert convexified_chain.execute(
        analytical_use_case[1].get_current_value(as_dict=True)
    )["convexification"] == array([0.0])


@pytest.mark.parametrize("convexification", [0.0, 1000.0])
def test_convexified_scenario(analytical_use_case, convexification):
    """Test that the solution of the convexified scenario is the analytical one."""
    if convexification == 0:
        pytest.skip("Test valid only for convexified scenario.")
    else:
        analytical_use_case[0].execute(
            algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
            max_iter=10,
            normalize_design_space=False,  # True ?
            posa=1.0,
            convexification_constant=convexification,
        )

        assert (
            analytical_use_case[0].optimization_result.x_opt
            == array([0, 1, 0], dtype=int)
        ).all()
        assert (
            pytest.approx(analytical_use_case[0].optimization_result.f_opt, abs=1e-10)
            == 0.0
        )

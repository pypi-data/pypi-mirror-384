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
from numpy import array

from tests.algos.conftest import CatTestDisc


def test_hypercube_optimizer_analytical(
    analytical_use_case_hypercube, mdo_discipline_catalog
):
    """Test Shape Function Penalization on an analytical use case."""
    if mdo_discipline_catalog != CatTestDisc:
        pytest.skip()

    analytical_use_case_hypercube[0].execute(
        algo_name="NLOPT_MMA",
        max_iter=100,
        normalize_design_space=True,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )

    assert (
        pytest.approx(
            analytical_use_case_hypercube[0].optimization_result.f_opt, abs=1e-8
        )
        == 0.0
    )
    alpha_translator = analytical_use_case_hypercube[
        1
    ].discrete_var_to_catalogue_choice["alpha"]
    approximate_to_discrete_solution = (
        analytical_use_case_hypercube[1]
        .hyper_cube_discipline["alpha"]
        .compute_discrete_solution
    )
    alpha_opt = analytical_use_case_hypercube[1].convert_array_to_dict(
        analytical_use_case_hypercube[0].optimization_result.x_opt
    )["alpha"]
    assert alpha_translator(approximate_to_discrete_solution(alpha_opt)) == array([
        "Blue"
    ])

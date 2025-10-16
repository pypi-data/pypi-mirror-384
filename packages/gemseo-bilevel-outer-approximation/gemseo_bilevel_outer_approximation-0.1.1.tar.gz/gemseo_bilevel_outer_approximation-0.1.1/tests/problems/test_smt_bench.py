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
"""SMT benchmark problem with gradient-less BiLevel OuterApproximation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from gemseo import create_discipline
from gemseo import create_scenario
from gemseo import execute_post
from gemseo.settings.opt import NLOPT_BFGS_Settings
from numpy import array

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)

if TYPE_CHECKING:
    from gemseo_bilevel_outer_approximation.formulations.benders import Benders


def test_smt_bench(tmp_wd) -> None:
    """Test the SMT bench."""
    ds = CatalogueDesignSpace()
    ds.add_variable("x1", lower_bound=-5.0, upper_bound=5.0, value=0.0, type_="float")
    ds.add_categorical_variable(
        name="c1_onehot", value=["blue"], catalogue=["blue", "red", "green"]
    )
    ds.add_categorical_variable(
        name="c2_onehot", value=["large"], catalogue=["large", "small"]
    )
    ds.add_categorical_variable(name="i_onehot", value=[0], catalogue=[0, 1, 2])

    def function_test_mixed_integer(
        x1=0.0,
        c1_onehot=None,
        c2_onehot=None,
        i_onehot=None,
    ):
        """Function for mixed integer.

        Args:
            x1: A continuous design variable.
            c1_onehot:The first categorical one hot encoding design variable.
            c2_onehot:The second categorical one hot encoding design variable.
            i_onehot:The discrete one hot encoding design variable.

        Returns:The function value.
        """
        if c1_onehot is None:
            c1_onehot = np.array([1.0, 0.0, 0.0])
        if c2_onehot is None:
            c2_onehot = np.array([1.0, 0.0])
        if i_onehot is None:
            i_onehot = np.array([1.0, 0.0, 0.0])
        # alphabetic order is used from label encoder, this means that c1_onehot =0,1,
        # 0 means green
        x2 = c1_onehot.dot(np.array([1.0, 0.0, 0.0]))
        x3 = c1_onehot.dot(np.array([0.0, 1.0, 0.0]))
        x4 = c1_onehot.dot(np.array([0.0, 0.0, 1.0]))
        #  enum 2
        x5 = c2_onehot.dot(np.array([1.0, 0.0]))
        x6 = c2_onehot.dot(np.array([0.0, 1.0]))
        # int
        ii = i_onehot.dot(np.array([0.0, 1.0, 2.0]))
        y = array([
            (x2 + 2 * x3 + 3 * x4) * x5 * x1
            + (x2 + 2 * x3 + 3 * x4) * x6 * 0.95 * x1
            + ii
        ])
        return y  # noqa: RET504

    disc = create_discipline("AutoPyDiscipline", py_func=function_test_mixed_integer)

    scenario = create_scenario(
        disciplines=[disc],
        formulation_name="Benders",
        objective_name="y",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=NLOPT_BFGS_Settings(
            max_iter=100,
            xtol_rel=1e-8,
            xtol_abs=1e-8,
            ftol_rel=1e-8,
            ftol_abs=1e-8,
            ineq_tolerance=1e-5,
            eq_tolerance=1e-3,
            normalize_design_space=False,
        ),
        reset_x0_before_opt=False,
    )
    scenario.execute(
        algo_name="BILEVEL_MASTER_OUTER_APPROXIMATION",
        max_iter=10,
        normalize_design_space=True,
        posa=1.0,
        adapt=True,
        gradient_free=True,
        number_of_parallel_points=3,
        number_of_processes=1,
        bilateral_adapt=False,
        min_dfk=2,
        scipy=True,
        step_decreasing_activation=1000,
    )
    benders_formulation: Benders = scenario.formulation
    x_opt, f_opt = (
        benders_formulation.optimization_problem.solution.x_opt,
        benders_formulation.optimization_problem.solution.f_opt,
    )
    assert (x_opt == [0, 0, 1, 1, 0, 1, 0, 0]).all()
    assert f_opt == pytest.approx(-14.9999998)

    # msg = "Total number of function linearization calls = {}".format(
    #     scenario.formulation.sub_problem_scenario.scenario.formulation.disciplines[
    #         0
    #     ].n_calls_linearize
    # )

    execute_post(
        scenario,
        post_name="OuterApproximationHistory",
        fig_size=(9, 7),
        show=True,
        save=True,
    )

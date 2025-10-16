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

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from gemseo import create_scenario
from gemseo.core.discipline import Discipline
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.settings.opt import L_BFGS_B_Settings
from gemseo.settings.opt import NLOPT_MMA_Settings
from gemseo.utils.testing.pytest_conftest import *  # noqa: F401,F403
from numpy import arange
from numpy import array
from numpy import atleast_2d

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)

if TYPE_CHECKING:
    from gemseo.typing import StrKeyMapping


def cat_test(x, alpha_onehot):
    """Objective function."""
    f = x**2 + alpha_onehot[0] ** 2 + alpha_onehot[2] ** 2
    return f  # noqa: RET504


def cat_test_concave(x, alpha_onehot):
    """Objective function."""
    f = (
        x**2
        + 2.0 * (2 * alpha_onehot[0] - alpha_onehot[0] ** 2)
        + (2 * alpha_onehot[2] - alpha_onehot[2] ** 2)
    )
    return f  # noqa: RET504


def cat_test_concave2(x, alpha_onehot):
    """Objective function."""
    f = (
        x**2
        + 2.0 * (3 * alpha_onehot[0] - 2 * alpha_onehot[0] ** 2)
        + (3 * alpha_onehot[2] - 2 * alpha_onehot[2] ** 2)
    )
    return f  # noqa: RET504


def cat_test_concave3(x, alpha_onehot):
    """Objective function."""
    f = (
        x**2
        + 2.0 * (3 * alpha_onehot[0] - 2 * alpha_onehot[0] ** 2)
        + (3 * alpha_onehot[2] - 2 * alpha_onehot[2] ** 2)
        + (1 - 6 * alpha_onehot[1] ** 2 + 5 * alpha_onehot[1])
    )
    return f  # noqa: RET504


class CatTestDisc(Discipline):
    """Mdo discipline for categorical design variable  use case."""

    def __init__(self):  # noqa: D107
        super().__init__()
        self.input_grammar.update_from_names(["x", "alpha_onehot"])
        self.output_grammar.update_from_names(["f"])

    def _run(self, input_data: StrKeyMapping):
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]
        f = cat_test(x, alpha)
        self.io.data["f"] = f

        # def _compute_jacobian(self, inputs=None, outputs=None):
        self._has_jacobian = True
        self._init_jacobian(
            init_type=self.InitJacobianType.DENSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        # x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.jac["f"]["x"] = atleast_2d(2 * x)
        self.jac["f"]["alpha_onehot"] = atleast_2d(
            array([2 * alpha[0], 0, 2 * alpha[2]])
        )
        return


class CatTestDiscConcave(Discipline):
    """Mdo discipline for categorical design variable  use case."""

    def __init__(self):  # noqa: D107
        super().__init__()
        self.input_grammar.update_from_names(["x", "alpha_onehot"])
        self.output_grammar.update_from_names(["f"])

    def _run(self, input_data: StrKeyMapping):
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]
        f = cat_test_concave(x, alpha)
        self.io.data["f"] = f

        # def _compute_jacobian(self, inputs=None, outputs=None):
        self._has_jacobian = True
        self._init_jacobian(
            init_type=self.InitJacobianType.DENSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        # x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.jac["f"]["x"] = atleast_2d(2 * x)
        self.jac["f"]["alpha_onehot"] = atleast_2d(
            array([(2 - 2 * alpha[0]) * 2.0, 0, 2 - 2 * alpha[2]])
        )
        return


class CatTestDiscConcave2(Discipline):
    """Mdo discipline for categorical design variable  use case."""

    def __init__(self):  # noqa: D107
        super().__init__()
        self.input_grammar.update_from_names(["x", "alpha_onehot"])
        self.output_grammar.update_from_names(["f"])

    def _run(self, input_data: StrKeyMapping):
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]
        f = cat_test_concave2(x, alpha)
        self.io.data["f"] = f

    def _compute_jacobian(self, input_data=None, output_data=None):
        self._init_jacobian(
            init_type=self.InitJacobianType.DENSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.jac["f"]["x"] = atleast_2d(2 * x)
        self.jac["f"]["alpha_onehot"] = atleast_2d(
            array([(3 - 4 * alpha[0]) * 2.0, 0, 3 - 4 * alpha[2]])
        )
        return


class CatTestDiscConcave3(Discipline):
    """Mdo discipline for categorical design variable  use case."""

    def __init__(self):  # noqa: D107
        super().__init__()
        self.input_grammar.update_from_names(["x", "alpha_onehot"])
        self.output_grammar.update_from_names(["f"])

    def _run(self, input_data: StrKeyMapping):
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]
        f = cat_test_concave3(x, alpha)
        self.io.data["f"] = f

    def _compute_jacobian(self, input_data=None, output_data=None):
        self._init_jacobian(
            init_type=self.InitJacobianType.DENSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.jac["f"]["x"] = atleast_2d(2 * x)
        self.jac["f"]["alpha_onehot"] = atleast_2d(
            array([(3 - 4 * alpha[0]) * 2, -6 * alpha[1] + 5, 3 - 4 * alpha[2]])
        )
        return


class CatTestDiscMultiVar(Discipline):
    """Mdo discipline for categorical design variable  use case."""

    def __init__(self, n):  # noqa: D107
        super().__init__()
        self.input_grammar.update_from_names(["x", "alpha_onehot"])
        self.coefficients = arange(start=1, stop=n * 3 + 1, step=1)
        self.output_grammar.update_from_names(["f"])

    def _run(self, input_data: StrKeyMapping):
        x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.io.data["f"] = x**2 + self.coefficients.dot(alpha)

        # def _compute_jacobian(self, inputs=None, outputs=None):
        self._has_jacobian = True
        self._init_jacobian(
            init_type=self.InitJacobianType.DENSE,
            input_names=self.io.input_grammar.names,
            output_names=self.io.output_grammar.names,
        )
        # x, alpha = self.io.data["x"], self.io.data["alpha_onehot"]

        self.jac["f"]["x"] = atleast_2d(2 * x)
        self.jac["f"]["alpha_onehot"] = atleast_2d(self.coefficients)


@pytest.fixture(params=["Red", "Blue", "Yellow"], scope="session")
def initial_guess(request):
    """Return the initial guess category."""
    return request.param


@pytest.fixture(params=[1.0, 10.0], scope="session")
def posa(request):
    """Return the initial guess category."""
    return request.param


@pytest.fixture(params=[True, False], scope="session")
def adapt(request):
    """Return the initial guess category."""
    return request.param


@pytest.fixture(
    params=[CatTestDisc, CatTestDiscConcave, CatTestDiscConcave2, CatTestDiscConcave3],
    scope="session",
)
def mdo_discipline_catalog(request):
    """Return the MDO discipline to be used as analytical test case."""
    return request.param


@pytest.fixture(
    params=[2, 3, 4],
    scope="session",
)
def problem_size(request):
    """Return the MDO discipline to be used as analytical test case."""
    return request.param


@pytest.fixture
def analytical_use_case_oa(mdo_discipline_catalog, initial_guess):
    """Analytical Use Case Fixture.

    Returns:
        Return an instance of CatTestDisc.
    """
    disc = mdo_discipline_catalog()
    ds = CatalogueDesignSpace()
    # ds.add_variable(
    #     "x",
    #     lower_bound=-1.0,
    #     upper_bound=1.0,
    #     value=1.0,
    #     type_=DesignVariableType.FLOAT,
    # )
    ds.add_categorical_variable(
        name="alpha_onehot", value=[initial_guess], catalogue=["Red", "Blue", "Yellow"]
    )
    design_space = deepcopy(ds)
    scenario = create_scenario(
        disciplines=[disc],
        formulation_name="DisciplinaryOpt",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
    )
    return scenario, design_space


@pytest.fixture
def analytical_use_case(mdo_discipline_catalog, initial_guess):
    """Analytical Use Case Fixture.

    Returns:
        Return an instance of CatTestDisc.
    """
    disc = mdo_discipline_catalog()
    disc2 = AnalyticDiscipline(expressions={"g": "x**2-1"}, name="Simple")
    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x",
        lower_bound=-1.0,
        upper_bound=1.0,
        value=1.0,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )
    ds.add_categorical_variable(
        name="alpha_onehot", value=[initial_guess], catalogue=["Red", "Blue", "Yellow"]
    )
    design_space = deepcopy(ds)
    algo_settings = NLOPT_MMA_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
        normalize_design_space=False,
    )
    scenario = create_scenario(
        disciplines=[disc, disc2],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=algo_settings,
    )
    scenario.add_constraint(
        "g",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        value=0.0,
        constraint_name="g",
    )
    return scenario, design_space


@pytest.fixture
def analytical_use_case_multi_var(problem_size, initial_guess):
    """Analytical Use Case Fixture.

    Returns:
        Return an instance of CatTestDisc.
    """
    disc = CatTestDiscMultiVar(problem_size)
    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x",
        lower_bound=-1.0,
        upper_bound=1.0,
        value=1.0,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )
    ds.add_categorical_variable(
        name="alpha_onehot",
        value=[initial_guess] * problem_size,
        catalogue=["Red", "Blue", "Yellow"],
    )
    design_space = deepcopy(ds)
    algo_settings = L_BFGS_B_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
        normalize_design_space=False,
    )
    scenario = create_scenario(
        disciplines=[disc],
        formulation_name="Benders",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
        sub_problem_algo_settings=algo_settings,
    )
    return scenario, design_space


@pytest.fixture(scope="session")
def analytical_use_case_hypercube(mdo_discipline_catalog, initial_guess):
    """Analytical Use Case Fixture.

    Returns:
        Return an instance of CatTestDisc.
    """
    disc = mdo_discipline_catalog()
    disc2 = AnalyticDiscipline(expressions={"g": "x**2-1"}, name="Simple")
    ds = CatalogueDesignSpace()
    ds.add_variable(
        "x",
        lower_bound=-1.0,
        upper_bound=1.0,
        value=1.0,
        type_=CatalogueDesignSpace.DesignVariableType.FLOAT,
    )
    ds.add_categorical_variable(
        name="alpha",
        value=[initial_guess],
        catalogue=["Red", "Blue", "Yellow"],
        hyper_cube=True,
    )

    scenario = create_scenario(
        disciplines=[ds.hyper_cube_discipline["alpha"], disc, disc2],
        formulation_name="MDF",
        objective_name="f",
        design_space=ds,
        maximize_objective=False,
    )
    scenario.add_constraint(
        "g",
        constraint_type=MDOFunction.ConstraintType.INEQ,
        value=0.0,
        constraint_name="g",
    )
    return scenario, ds

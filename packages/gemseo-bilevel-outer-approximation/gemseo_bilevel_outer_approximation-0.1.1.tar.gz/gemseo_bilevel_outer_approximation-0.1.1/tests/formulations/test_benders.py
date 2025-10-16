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
# Contributors:
#    INITIAL AUTHORS - API and implementation and/or documentation
#        :author: Francois Gallard
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
from __future__ import annotations

import re

import pytest
from gemseo import create_design_space
from gemseo import create_scenario
from gemseo.core.chains.chain import MDOChain
from gemseo.core.discipline import Discipline
from gemseo.core.mdo_functions.mdo_function import MDOFunction
from gemseo.disciplines.analytic import AnalyticDiscipline
from gemseo.formulations.mdf_settings import MDF_Settings
from gemseo.settings.opt import NLOPT_COBYLA_Settings
from gemseo.settings.opt import NLOPT_MMA_Settings
from gemseo.settings.opt import SLSQP_Settings
from numpy import array
from numpy import ones

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)
from gemseo_bilevel_outer_approximation.formulations.benders import Benders

DesignVariableType = CatalogueDesignSpace.DesignVariableType


@pytest.fixture
def sellar_problem():
    """Define a Sellar problem."""
    disc_sellar_system = AnalyticDiscipline(
        expressions={
            "obj": "x_local**2 + x_shared_2 + y_1**2 + exp(-y_2)",
            "c_1": "3.16 - y_1**2",
            "c_2": "y_2 - 24.0",
        }
    )

    disc_sellar_1 = AnalyticDiscipline(
        expressions={
            "y_1": "(x_shared_1 ** 2 + x_shared_2 + x_local - 0.2 * y_2) ** 0.5"
        }
    )

    disc_sellar_2 = AnalyticDiscipline(
        expressions={"y_2": "abs(y_1) + x_shared_1 + x_shared_2"}
    )
    disciplines = [disc_sellar_system, disc_sellar_1, disc_sellar_2]
    design_space = create_design_space()
    design_space.add_variable(
        "x_local", 1, lower_bound=0.0, upper_bound=10.0, value=array([1.0])
    )
    design_space.add_variable(
        "x_shared_1", 1, lower_bound=-10, upper_bound=10.0, value=array([4.0])
    )
    design_space.add_variable(
        "x_shared_2", 1, lower_bound=0.0, upper_bound=10.0, value=array([3.0])
    )
    design_space.add_variable(
        "y_1", 1, lower_bound=-100.0, upper_bound=100.0, value=array([1.0])
    )
    design_space.add_variable(
        "y_2", 1, lower_bound=-100.0, upper_bound=100.0, value=array([1.0])
    )
    algo_settings = SLSQP_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )

    scenario = create_scenario(
        disciplines=disciplines,
        formulation_name="Benders",
        objective_name="obj",
        design_space=design_space,
        maximize_objective=False,
        sub_problem_algo_settings=algo_settings,
        main_problem_design_variables=["x_shared_2"],
        split_criterion="",
        sub_problem_formulation_settings=MDF_Settings(main_mda_name="MDAGaussSeidel"),
    )
    scenario.add_constraint("c_1", MDOFunction.ConstraintType.INEQ)
    scenario.add_constraint("c_2", MDOFunction.ConstraintType.INEQ)
    return scenario


@pytest.fixture
def dummy_benders_scenario():  # type (...) -> MDOScenario
    """Create a dummy Benders scenario.

    It has to be noted that there is no strongly coupled discipline in this example.
    It implies that MDA1 will not be created. Yet, MDA2 will be created,
    as it is built with all the sub-disciplines passed to the Benders formulation.

    Returns: A dummy Benders MDOScenario.
    """
    disc_expressions = {
        "disc_1": (["x_1"], ["a"]),
        "disc_2": (["a", "x_2"], ["b"]),
        "disc_3": (["x", "x_3", "b"], ["obj"]),
    }
    discipline_1, discipline_2, discipline_3 = create_disciplines_from_desc(
        disc_expressions
    )

    system_design_space = CatalogueDesignSpace()
    system_design_space.add_variable("x_1", type_=DesignVariableType.FLOAT)
    system_design_space.add_variable("x_2", type_=DesignVariableType.FLOAT)
    system_design_space.add_categorical_variable("x_3", value=[0], catalogue=[0, 1, 2])
    algo_settings = NLOPT_MMA_Settings(
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )

    return create_scenario(
        disciplines=[discipline_1, discipline_2, discipline_3],
        formulation_name="Benders",
        objective_name="obj",
        design_space=system_design_space,
        maximize_objective=False,
        sub_problem_algo_settings=algo_settings,
    )


class UselessDiscipline(Discipline):
    """Useless Discipline.

    Has no _run method. It is used to test the Benders formulation.
    """

    def _run(self):
        pass


def create_disciplines_from_desc(disc_desc):
    """Return the disciplines from their descriptions.

    Args:
        disc_desc: The disc_desc of a discipline, either a list of classes or a dict.
    """
    if isinstance(disc_desc, tuple):
        # these are disciplines classes
        return [cls() for cls in disc_desc]

    disciplines = []
    data = ones(1)

    disc_desc_items = sorted(disc_desc.items())

    for name, io_names in disc_desc_items:
        disc = UselessDiscipline(name)
        input_d = dict.fromkeys(io_names[0], data)
        disc.input_grammar.update_from_data(input_d)
        output_d = dict.fromkeys(io_names[1], data)
        disc.output_grammar.update_from_data(output_d)
        disciplines += [disc]

    return disciplines


def test_benders_dummy(dummy_benders_scenario):
    """Test the Benders decomposition.

    This test generates a Benders scenario which does not aim to be run as it has no
    physical significance. It is checked that integer variables are set as input of the
    slave problem and the objective function and optimal solution of x_1 and x_2 are
    slave problem outputs.
    """
    disciplines = dummy_benders_scenario.formulation.disciplines
    assert "x_3" in dummy_benders_scenario.design_space.variable_names
    assert (
        "x_1"
        in dummy_benders_scenario.formulation.sub_problem_design_space.variable_names
    )
    assert (
        "x_2"
        in dummy_benders_scenario.formulation.sub_problem_design_space.variable_names
    )
    assert "obj" in MDOChain(disciplines).io.output_grammar.names


@pytest.mark.parametrize("input_names", [None, "alpha"])
def test_mdo_scenario_jac(sellar_problem, input_names):
    """Test Benders formulation for the sellar problem."""
    if input_names is None:
        out = sellar_problem.formulation.sub_problem_scenario_adapter.check_jacobian(
            linearization_mode="auto",
            threshold=1e-3,
            step=1e-4,
            output_names=[
                sellar_problem.formulation.optimization_problem.objective.name
            ],
            input_names=input_names,
        )
        assert out
    else:
        with pytest.raises(ValueError):
            sellar_problem.formulation.sub_problem_scenario_adapter.check_jacobian(
                linearization_mode="auto",
                threshold=1e-3,
                step=1e-4,
                output_names=[
                    sellar_problem.formulation.optimization_problem.objective.name
                ],
                input_names=input_names,
            )


def test_benders_sellar(sellar_problem):
    """Test Benders formulation for the sellar problem."""
    sellar_problem.execute(max_iter=100, algo_name="L-BFGS-B")
    out = sellar_problem.optimization_result
    assert (out.x_opt == array([0, 0], dtype=float)).all()
    assert pytest.approx(out.f_opt, 1e-2) == 3.18


def test_benders_instantiation():
    """Test Benders formulation instantiation."""
    disc_sellar_system = AnalyticDiscipline(
        expressions={
            "obj": "x_local**2 + x_shared_2 + y_1**2 + exp(-y_2)",
            "c_1": "3.16 - y_1**2",
            "c_2": "y_2 - 24.0",
        }
    )

    disc_sellar_1 = AnalyticDiscipline(
        expressions={
            "y_1": "(x_shared_1 ** 2 + x_shared_2 + x_local - 0.2 * y_2) ** 0.5"
        }
    )

    disc_sellar_2 = AnalyticDiscipline(
        expressions={"y_2": "abs(y_1) + x_shared_1 + x_shared_2"}
    )
    disciplines = [disc_sellar_system, disc_sellar_1, disc_sellar_2]
    design_space = create_design_space()
    design_space.add_variable(
        "x_local", 1, lower_bound=0.0, upper_bound=10.0, value=ones(1)
    )
    design_space.add_variable(
        "x_shared_1", 1, lower_bound=-10, upper_bound=10.0, value=array([4.0])
    )
    design_space.add_variable(
        "x_shared_2", 1, lower_bound=0.0, upper_bound=10.0, value=array([3.0])
    )
    design_space.add_variable(
        "y_1", 1, lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )
    design_space.add_variable(
        "y_2", 1, lower_bound=-100.0, upper_bound=100.0, value=ones(1)
    )
    algo_settings = SLSQP_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )
    bf = Benders(
        disciplines=disciplines,
        objective_name="obj",
        design_space=design_space,
        sub_problem_algo_settings=algo_settings,
        split_criterion="",
        main_problem_design_variables=["x_shared_2", "x_local"],
    )
    assert isinstance(bf, Benders)


def test_integer_and_float_design_variables():
    """Test that integer and float design variables are taken into account."""
    discipline_integer = AnalyticDiscipline({"y": "x_int + x_float"})

    design_space = CatalogueDesignSpace()
    design_space.add_variable("x_int", type_="integer", lower_bound=-4, upper_bound=4)
    design_space.add_variable("x_float", lower_bound=-3, upper_bound=5)
    design_space.categorical_variables.append(
        "x_int"
    )  # To remove when splitting criterion is functional.

    algo_settings = NLOPT_COBYLA_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )
    bender_formulation = Benders(
        disciplines=[discipline_integer],
        objective_name="y",
        design_space=design_space,
        sub_problem_algo_settings=algo_settings,
    )

    assert bender_formulation.optimization_problem.evaluate_functions(array([1])) == (
        {
            "y": -2.0,
            "is_feasible": 1.0,
            "constraint_violation": 0.0,
            "iterations": 18.0,
            "x_opt": -3.0,
        },
        {},
    )


def test_integer_and_float_design_variables_scenario():
    """Test that integer/float design variables are taken into account in a scenario."""
    discipline_integer = AnalyticDiscipline({"y": "x_int + x_float"})

    design_space = CatalogueDesignSpace()
    design_space.add_variable("x_float", lower_bound=-3, upper_bound=5, value=1)

    # Any integer variable MUST be considered as a catalogue.
    design_space.add_categorical_variable(
        "i_x_int",
        value=[0],
        catalogue=array([0, 1, 2, 3, 4, 5, 6, 7, 8]),
    )

    disc = design_space.get_catalogue_interpolation_discipline(
        1.0, "i_x_int", "x_int", catalogue=array([-4, -3, -2, -1, 0, 1, 2, 3, 4])
    )

    algo_settings = NLOPT_COBYLA_Settings(
        max_iter=100,
        xtol_rel=1e-8,
        xtol_abs=1e-8,
        ftol_rel=1e-8,
        ftol_abs=1e-8,
        ineq_tolerance=1e-5,
        eq_tolerance=1e-3,
    )
    scenario = create_scenario(
        disciplines=[disc, discipline_integer],
        formulation_name="Benders",
        objective_name="y",
        design_space=design_space,
        sub_problem_algo_settings=algo_settings,
    )

    opt_options = {
        "algo_name": "BILEVEL_MASTER_OUTER_APPROXIMATION",
        "max_iter": 1000,
        "gradient_free": True,
    }

    scenario.execute(**opt_options)
    assert (
        scenario.optimization_result.x_opt == array([1, 0, 0, 0, 0, 0, 0, 0, 0])
    ).all()
    assert scenario.optimization_result.f_opt == -7.0


def test_wrong_configuration():
    disc_expressions = {
        "disc_1": (["x_1"], ["a"]),
        "disc_2": (["a", "x_2"], ["b"]),
        "disc_3": (["x", "x_3", "b"], ["obj"]),
    }
    disciplines = create_disciplines_from_desc(disc_expressions)

    system_design_space = CatalogueDesignSpace()
    system_design_space.add_variable("x_1", type_=DesignVariableType.FLOAT)
    system_design_space.add_variable("x_2", type_=DesignVariableType.FLOAT)
    system_design_space.add_categorical_variable("x_3", value=[0], catalogue=[0, 1, 2])

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Benders formulation needs either a split_criterion "
            "or a definition of the main_problem_design_variables."
        ),
    ):
        Benders(
            disciplines,
            objective_name="obj",
            design_space=system_design_space,
            sub_problem_algo_settings=NLOPT_COBYLA_Settings(max_iter=100),
            split_criterion="",
            main_problem_design_variables=(),
        )

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
from numpy.testing import assert_equal

from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueDesignSpace,
)
from gemseo_bilevel_outer_approximation.algos.design_space.catalogue_design_space import (  # noqa: E501
    CatalogueInterpolation,
)
from gemseo_bilevel_outer_approximation.disciplines.enumerative_to_one_hot import (
    EnumerativeToOneHot,
)


@pytest.fixture(params=[True, False])
def hypercube_interpolation(request):
    """Hypercube interpolation fixture."""
    return request.param


@pytest.fixture
def catalogue_design_space_class(hypercube_interpolation):
    """Create an instance of a CatalogueDesignSpace.

    Returns:
        cds: CatalogueDesignSpace object.
    """
    cds = CatalogueDesignSpace()
    cds.add_categorical_variable(
        name="letter",
        value=["A"],
        catalogue=array(["A", "B", "C"]),
        hyper_cube=hypercube_interpolation,
    )
    return cds


@pytest.fixture(params=[[2, False], [3, False], [3, True]])
def catalogue_design_space_hypercube_class(request):
    """Create an instance of a CatalogueDesignSpace.

    Returns:
        cds: CatalogueDesignSpace object.
    """
    cds = CatalogueDesignSpace()
    cds.add_categorical_variable(
        name="letter",
        value=["A"],
        catalogue=array(["A", "B", "C"][: request.param[0]]),
        hyper_cube=True,
        repeat_vertex=request.param[1],
    )
    return cds


@pytest.fixture(params=[True, False])
def interpolation_from_catalogue(catalogue_design_space_class, request):
    """Create an interpolation discipline using dictionary."""
    dictionary = {
        "grade": {"catalogue": array([10.0, 5.0, 1.0]), "penalty": 1.0},
        "weight": {"catalogue": array([1.0, 2.0, 5.0]), "penalty": 1.0},
    }
    return (
        catalogue_design_space_class.get_catalogue_interpolation_discipline_from_dict(
            variable="letter",
            dictionary=dictionary,
            ensure_minimum=request.param,
        )
    )


@pytest.fixture
def catalogue_interpolation_from_cds(catalogue_design_space_class):
    """Fixture for catalogue interpolation discipline from catalog design space."""
    return catalogue_design_space_class.get_catalogue_interpolation_discipline(
        penalty=1.0,
        variable="letter",
        output="weight",
        catalogue=array([10.0, 100.0, 1000.0]),
    )


@pytest.fixture(
    params=[array([1.0, 0.0, 0.0]), array([0.0, 1.0, 0.0]), array([0.0, 0.0, 1.0])]
)
def one_hot_input(request):
    """One-hot encoding input vor interpolating discipline."""
    return request.param


@pytest.fixture(params=[array([0.0, 0.0]), array([1.0, 0.0]), array([0.0, 1.0])])
def hc_input(request):
    """Hyper cube design space input."""
    return request.param


@pytest.fixture
def catalogue_interpolation():
    """Create an instance of Catalogue interpolation."""
    return CatalogueInterpolation(
        catalogue=array([10.0, 20.0]),
        n_components=2,
        variable_name="alpha",
        output_name="E",
        penalty=3.0,
    )


def test_categorical_variable_exists(catalogue_design_space_class):
    """Test if the categorical design variable exist in the list of design variable."""
    assert "letter" in catalogue_design_space_class.variable_names


def test_value_from_one_hot_encoding(
    catalogue_design_space_class, hypercube_interpolation
):
    """Test if one-hot encoding is correct for the initial categorical variable."""
    if hypercube_interpolation:
        assert (
            catalogue_design_space_class.get_current_value(as_dict=True)["letter"]
            == array([0, 0], dtype=float)
        ).all()
    else:
        assert (
            catalogue_design_space_class.get_current_value(as_dict=True)["letter"]
            == array([1, 0, 0], dtype=int)
        ).all()


def test_lower_bound(catalogue_design_space_class, hypercube_interpolation):
    """Test if lower bound is correctly set."""
    if hypercube_interpolation:
        assert (
            catalogue_design_space_class.get_lower_bound("letter")
            == array([0, 0], dtype=float)
        ).all()
    else:
        assert (
            catalogue_design_space_class.get_lower_bound("letter")
            == array([0, 0, 0], dtype=int)
        ).all()


def test_upper_bound(catalogue_design_space_class, hypercube_interpolation):
    """Test if upper bound is correctly set."""
    if hypercube_interpolation:
        assert (
            catalogue_design_space_class.get_upper_bound("letter")
            == array([1, 1], dtype=float)
        ).all()
    else:
        assert (
            catalogue_design_space_class.get_upper_bound("letter")
            == array([1, 1, 1], dtype=int)
        ).all()


def test_catalogue_interpolation(catalogue_interpolation):
    """Test discipline exectution."""
    out = catalogue_interpolation.execute(
        input_data={"alpha": array([0.0, 1.0, 1.0, 0.0])}
    )
    assert (out["E"] == array([20.0, 10.0])).all()


def test_catalogue_interpolation_jacobian(catalogue_interpolation):
    """Test discipline jacobian."""
    out = catalogue_interpolation.check_jacobian(
        input_data={"alpha": array([0.0, 1.0, 1.0, 0.0])},
        linearization_mode="auto",
        threshold=1e-6,
    )
    assert out


def test_catalogue_interpolation_from_cds(
    catalogue_interpolation_from_cds, one_hot_input, hc_input, hypercube_interpolation
):
    """Test discipline catalogue interpolation from cds."""
    if hypercube_interpolation:
        out = catalogue_interpolation_from_cds.execute(input_data={"letter": hc_input})
        if (hc_input == array([0.0, 0.0])).all():
            assert out["weight"] == array([10.0])
        elif (hc_input == array([0.0, 1.0])).all():
            assert out["weight"] == array([100.0])
        elif (hc_input == array([1.0, 0.0])).all():
            assert out["weight"] == array([1000.0])
    else:
        out = catalogue_interpolation_from_cds.execute(
            input_data={"letter": one_hot_input}
        )
        if (one_hot_input == array([1.0, 0.0, 0.0])).all():
            assert out["weight"] == array([10.0])
        elif (one_hot_input == array([0.0, 1.0, 0.0])).all():
            assert out["weight"] == array([100.0])
        elif (one_hot_input == array([0.0, 0.0, 1.0])).all():
            assert out["weight"] == array([1000.0])


def test_ci_from_cds_on_initial_value(
    catalogue_interpolation_from_cds, catalogue_design_space_class
):
    """Test of catalog interpolation from catalogue design space."""
    out = catalogue_interpolation_from_cds.execute(
        input_data=catalogue_design_space_class.get_current_value(as_dict=True)
    )
    assert out["weight"] == array([10.0])


def test_hypercube(catalogue_design_space_hypercube_class):
    """Test hypercube design space class."""
    x_dict = catalogue_design_space_hypercube_class.get_current_value(as_dict=True)
    assert (
        catalogue_design_space_hypercube_class.hyper_cube_discipline["letter"].cat_dict[
            tuple(x_dict["letter"])
        ]
        == "A"
    )


def test_hypercube_jacobian(catalogue_design_space_hypercube_class):
    """Test hypercube design space discipline jacobian."""
    j_check = catalogue_design_space_hypercube_class.hyper_cube_discipline[
        "letter"
    ].check_jacobian(
        linearization_mode="auto",
        threshold=1e-3,
        step=1e-4,
    )
    assert j_check


@pytest.fixture(
    params=[
        CatalogueDesignSpace.DesignVariableType.INTEGER,
        CatalogueDesignSpace.DesignVariableType.FLOAT,
        [
            CatalogueDesignSpace.DesignVariableType.INTEGER,
            CatalogueDesignSpace.DesignVariableType.FLOAT,
        ],
    ]
)
def types_to_keep(request):
    """Return design variable type."""
    return request.param


@pytest.mark.parametrize(
    ("my_types_to_keep", "expected_length"),
    [
        (CatalogueDesignSpace.DesignVariableType.INTEGER, 0),
        (CatalogueDesignSpace.DesignVariableType.FLOAT, 1),
        (
            [
                CatalogueDesignSpace.DesignVariableType.INTEGER,
                CatalogueDesignSpace.DesignVariableType.FLOAT,
            ],
            1,
        ),
    ],
)
def test_filter_design_space(
    catalogue_design_space_class, my_types_to_keep, expected_length: int
):
    """Test filter_by_type method."""
    catalogue_design_space_class.filter_by_type(types_to_keep=my_types_to_keep)
    assert (
        len(catalogue_design_space_class.filter_by_type(types_to_keep=my_types_to_keep))
        == expected_length
    )


@pytest.fixture(params=[0, None, 3, [0, 3], [0.0], [1], 2, 1.5, [0, 0, 1]])
def index_to_remove(request):
    """Return index of design variable to be removed."""
    return request.param


def test_interpolation_discipline(
    interpolation_from_catalogue, catalogue_design_space_class
):
    """Test the execution of the interpolation discipline."""
    out = interpolation_from_catalogue.execute(
        catalogue_design_space_class.get_current_value(as_dict=True)
    )
    assert out["grade"] == 10.0
    assert out["weight"] == 1.0
    interpolation_from_catalogue.disciplines[1].penalty = 5.0
    assert interpolation_from_catalogue.disciplines[1].penalty == 5.0


def test_enum_to_onehot_disc():
    """Test converting enumerative to one hot converters."""
    e2oh = EnumerativeToOneHot(
        n_components=3,
        catalogue=["Red", "Blue", "Green"],
        variable_name="alpha_enum",
        output_name="alpha_onehot",
    )
    out = e2oh.execute({"alpha_enum": array([0, 2, 1])})
    assert (out["alpha_onehot"][0:3] == array([1, 0, 0])).all()
    assert (out["alpha_onehot"][3:6] == array([0, 0, 1])).all()
    assert (out["alpha_onehot"][6:] == array([0, 1, 0])).all()


def test_conversion_integer_to_catalogue(catalogue_design_space_class):
    """Test the conversion of integer solution to catalogue choice."""
    assert catalogue_design_space_class.discrete_var_to_catalogue_choice["letter"](
        catalogue_design_space_class.get_current_value()
    ) == array(["A"])


@pytest.mark.parametrize(
    ("catalogue", "weights", "actual_weights"),
    [
        (["a", "b"], None, [1, 1]),
        (["a", "b"], [2, 3], [2, 3]),
        ([10, 20], None, [10, 20]),
        ([10, 20], [2, 3], [2, 3]),
    ],
)
def test_catalogue_weights(catalogue, weights, actual_weights) -> None:
    """Check the weights of catalogue values."""
    space = CatalogueDesignSpace()
    space.add_categorical_variable("x", catalogue[:1], catalogue, weights=weights)
    assert_equal(space.get_catalogue_weights("x"), actual_weights)

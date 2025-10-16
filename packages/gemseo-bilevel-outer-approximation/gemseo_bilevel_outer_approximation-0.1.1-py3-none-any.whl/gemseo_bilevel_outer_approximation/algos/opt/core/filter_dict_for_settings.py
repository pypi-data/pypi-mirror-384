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
"""Filter a dictionary by selecting the inputs for a setting."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from gemseo.algos.base_algorithm_settings import BaseAlgorithmSettings
    from gemseo.typing import StrKeyMapping


# TODO: better name
# Will be deleted when using exclusively pydantic settings.
def filter_dict_for_settings(
    settings: type[BaseAlgorithmSettings], options: StrKeyMapping
) -> dict[str, Any]:
    """Filter a dictionary by selecting the inputs for a setting.

    Args:
        settings: The Pydantic model defining the settings.
        options: A dictionary of options to filter.

    Returns:
        The filtered dictionary.
    """
    fields_to_consider = settings.model_fields

    return {k: options[k] for k in fields_to_consider if k in options}

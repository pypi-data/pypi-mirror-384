# Copyright 2024 - 2025 Aegiq Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import TYPE_CHECKING, Literal, overload

import drawsvg
import matplotlib.figure
import matplotlib.pyplot as plt

from lightworks.sdk.utils.exceptions import DisplayError

from .draw_circuit_mpl import DrawCircuitMPL
from .draw_circuit_svg import DrawCircuitSVG

if TYPE_CHECKING:
    from lightworks.sdk.circuit import PhotonicCircuit


@overload
def display(
    circuit: "PhotonicCircuit",
    display_loss: bool = ...,
    mode_labels: list[str] | None = ...,
    display_type: Literal["svg"] = ...,
    show_parameter_values: bool = ...,
    display_barriers: bool = ...,
) -> drawsvg.Drawing: ...


@overload
def display(
    circuit: "PhotonicCircuit",
    display_loss: bool = ...,
    mode_labels: list[str] | None = ...,
    display_type: Literal["mpl"] = ...,
    show_parameter_values: bool = ...,
    display_barriers: bool = ...,
) -> tuple[matplotlib.figure.Figure, plt.Axes]: ...


# display function to interact with relevant classes
def display(
    circuit: "PhotonicCircuit",
    display_loss: bool = False,
    mode_labels: list[str] | None = None,
    display_type: Literal["svg", "mpl"] = "svg",
    show_parameter_values: bool = False,
    display_barriers: bool = False,
) -> tuple[matplotlib.figure.Figure, plt.Axes] | drawsvg.Drawing:
    """
    Used to display a circuit from lightworks in the chosen format.

    Args:

        circuit (PhotonicCircuit) : The circuit which is to be displayed.

        display_loss (bool, optional) : Choose whether to display loss
            components in the figure, defaults to False.

        mode_labels (list|None, optional) : Optionally provided a list of mode
            labels which will be used to name the mode something other than
            numerical values. Can be set to None to use default values.

        display_type (str, optional) : Selects whether the drawsvg or
            matplotlib module should be used for displaying the circuit. Should
            either be 'svg' or 'mpl', defaults to 'svg'.

        show_parameter_values (bool, optional) : Shows the values of parameters
            instead of the associated labels if specified.

        display_barriers (bool, optional) : Shows included barriers within the
            created visualization if this is required.

    Returns:

        (fig, ax) | Drawing : The created figure and axis or drawing for the
            display plot, depending on which display type is used.

    Raised:

        DisplayError : In any cases where an invalid display type is provided
            an exception will be raised.

    """
    if display_type == "mpl":
        disp = DrawCircuitMPL(
            circuit,
            display_loss,
            mode_labels,
            show_parameter_values,
            display_barriers,
        )
        return disp.draw()
    if display_type == "svg":
        disp_svg = DrawCircuitSVG(
            circuit,
            display_loss,
            mode_labels,
            show_parameter_values,
            display_barriers,
        )
        return disp_svg.draw()
    raise DisplayError("Display type not recognised.")

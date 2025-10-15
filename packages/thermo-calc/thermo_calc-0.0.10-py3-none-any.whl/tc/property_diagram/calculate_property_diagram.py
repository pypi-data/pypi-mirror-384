from pathlib import Path

from tc_python import (
    Linear,
    TCPython,
    ThermodynamicQuantity,
)
from tc_python.step_or_map_diagrams import CalculationAxis, PropertyDiagramResult
from tc_python.server import SetUp

from typing_extensions import cast

from tc.database.utils import select_thermocalc_database
from tc.schema import Composition

from .defaults import TEMPERATURE_MIN, TEMPERATURE_MAX, MIN_STEPS


def calculate_property_diagram(
    composition: Composition,
    temperature_min=TEMPERATURE_MIN,
    temperature_max=TEMPERATURE_MAX,
    min_steps=MIN_STEPS,
    save_path: Path | None = None,
) -> PropertyDiagramResult:
    database = select_thermocalc_database(composition)

    elements = composition.elements()
    fractions = composition.fractions()

    with TCPython() as start:
        start = cast(SetUp, start)
        start.set_cache_folder("cache")
        start.set_ges_version(6)

        temperature = cast(ThermodynamicQuantity, ThermodynamicQuantity.temperature())
        calculation_axis = CalculationAxis(temperature)
        calculation_axis = calculation_axis.set_min(temperature_min)

        if calculation_axis is None:
            raise Exception(f"Failed to set temperature_min: {temperature_min}")

        calculation_axis = calculation_axis.set_max(temperature_max)

        if calculation_axis is None:
            raise Exception(f"Failed to set temperature_max: {temperature_max}")

        axis_type = Linear().set_min_nr_of_steps(min_steps)

        if axis_type is None:
            raise Exception(f"Failed to set axis_type with min steps: {min_steps}")

        calculation_axis = calculation_axis.with_axis_type(axis_type)

        if calculation_axis is None:
            raise Exception("Failed to set calculation_axis with linear axis type")

        property_diagram_calculation = (
            start.select_database_and_elements(database, elements)
            .get_system()
            .with_property_diagram_calculation()
            .with_axis(calculation_axis)
        )

        if property_diagram_calculation is None:
            raise Exception("Failed property diagram calculation")

        property_diagram = property_diagram_calculation.with_axis(calculation_axis)

        if property_diagram is None:
            raise Exception("property_diagram is None")

        # Set composition via mass fractions. Skip the first element; Thermo-Calc will normalize.
        for el, wf in list(fractions.items())[1:]:
            property_diagram.set_condition(f"W({el})", wf)

        result = property_diagram.calculate()

        if save_path is not None:
            result.save_to_disk(str(save_path))

    return result

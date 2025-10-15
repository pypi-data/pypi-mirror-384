from pathlib import Path
from pint import Quantity
from tc_python import TCPython, ThermodynamicQuantity, PhaseNameStyle
from tc_python.server import SetUp
from typing_extensions import cast

from tc.schema import Resistivity

TEMPERATURE_SPAN = 5.0


def compute_resistivity_at_temperature(
    name: str,
    result_path: Path,
    temperature_ref: float,
) -> Resistivity:
    """
    Ohm * m
    """
    with TCPython() as start:
        start = cast(SetUp, start)
        property_diagram = (
            SetUp().load_result_from_disk().property_diagram(str(result_path))
        )
        property_diagram.set_phase_name_style(PhaseNameStyle.ALL)

        temperature = cast(ThermodynamicQuantity, ThermodynamicQuantity.temperature())
        electric_resistivity = cast(
            ThermodynamicQuantity, ThermodynamicQuantity.electric_resistivity()
        )

        groups = property_diagram.get_values_grouped_by_quantity_of(
            temperature,
            electric_resistivity,
        )

    best_rho = None
    best_err = float("inf")
    for group in groups.values():
        for T, rho in zip(group.x, group.y):
            err = abs(T - temperature_ref)
            if err < best_err:
                best_err = err
                best_rho = rho

    if best_rho is None:
        raise RuntimeError("No resistivity data returned from Thermo-Calc.")

    electric_resistivity = cast(Quantity, Quantity(best_rho, "ohm * m"))

    resistivity = Resistivity(name=name, electric_resistivity=electric_resistivity)

    return resistivity

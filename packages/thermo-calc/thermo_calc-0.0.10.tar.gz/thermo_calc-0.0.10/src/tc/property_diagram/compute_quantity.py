from pathlib import Path
from tc_python import TCPython, ThermodynamicQuantity, PhaseNameStyle
from tc_python.server import SetUp
from typing_extensions import cast


def compute_quantity_at_temperature(
    result_path: Path,
    temperature_ref: float,
    thermodynamic_quantity: ThermodynamicQuantity,
) -> float:
    with TCPython() as start:
        start = cast(SetUp, start)
        property_diagram = (
            SetUp().load_result_from_disk().property_diagram(str(result_path))
        )
        property_diagram.set_phase_name_style(PhaseNameStyle.ALL)

        temperature = cast(ThermodynamicQuantity, ThermodynamicQuantity.temperature())

        groups = property_diagram.get_values_grouped_by_quantity_of(
            temperature,
            thermodynamic_quantity,
        )

    best_value = None
    best_err = float("inf")
    for group in groups.values():
        for T, value in zip(group.x, group.y):
            err = abs(T - temperature_ref)
            if err < best_err:
                best_err = err
                best_value = value

    if best_value is None:
        raise RuntimeError(f"No data found for {thermodynamic_quantity}")

    return best_value

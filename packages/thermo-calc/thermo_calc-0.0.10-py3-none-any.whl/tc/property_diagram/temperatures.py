import math

from pathlib import Path
from pint import Quantity
from tc_python import TCPython, ThermodynamicQuantity, PhaseNameStyle
from tc_python.server import SetUp
from typing_extensions import cast

from tc.schema import PhaseTransformationTemperatures


def compute_temperatures(
    name: str, result_path: Path
) -> PhaseTransformationTemperatures:
    with TCPython() as start:
        start = cast(SetUp, start)
        property_diagram = (
            SetUp().load_result_from_disk().property_diagram(str(result_path))
        )
        property_diagram.set_phase_name_style(PhaseNameStyle.ALL)

        temperature = cast(ThermodynamicQuantity, ThermodynamicQuantity.temperature())
        volume_fraction = cast(
            ThermodynamicQuantity,
            ThermodynamicQuantity.volume_fraction_of_a_phase("LIQUID"),
        )

        groups = property_diagram.get_values_grouped_by_quantity_of(
            temperature,
            volume_fraction,
        )

    solidus_T = None
    liquidus_T = None

    for group in groups.values():
        xT = group.x
        yL = group.y

        # Find solidus: last temperature where liquid fraction is essentially 0
        for i in range(len(yL)):
            if yL[i] > 1e-6:  # First point where liquid starts forming
                solidus_T = xT[i - 1] if i > 0 else xT[i]
                break

        # Find liquidus: first temperature where liquid fraction is essentially 1
        for i in range(len(yL)):
            if abs(yL[i] - 1.0) < 1e-6:  # First point where it's fully liquid
                liquidus_T = xT[i]
                break

    if solidus_T is None and liquidus_T is None:
        raise RuntimeError(
            f"Could not determine solidus and liquidus temperatures. Potentially an invalid composition, please try a different composition."
        )

    if solidus_T is None:
        raise RuntimeError(
            f"Could not determine solidus temperature. Potentially an invalid composition, please try a different composition."
        )

    if liquidus_T is None:
        raise RuntimeError(
            f"Could not determine liquidus temperature. Potentially an invalid composition, please try a different composition."
        )

    if math.isnan(solidus_T) or math.isnan(liquidus_T):
        raise RuntimeError(
            f"Encountered invalid liquidus / solidus temperature values. Potentially an invalid composition, please try a different composition."
        )

    temperature_melt = cast(Quantity, Quantity((liquidus_T + solidus_T) / 2, "K"))
    temperature_liquidus = cast(Quantity, Quantity(liquidus_T, "K"))
    temperature_solidus = cast(Quantity, Quantity(solidus_T, "K"))

    phase_transformation_temperatures = PhaseTransformationTemperatures(
        name=name,
        temperature_melt=temperature_melt,
        temperature_liquidus=temperature_liquidus,
        temperature_solidus=temperature_solidus,
    )

    return phase_transformation_temperatures

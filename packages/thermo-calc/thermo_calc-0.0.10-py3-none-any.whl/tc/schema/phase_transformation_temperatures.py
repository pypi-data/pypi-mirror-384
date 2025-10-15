from typing_extensions import TypedDict
from pintdantic import QuantityDict, QuantityModel, QuantityField

DEFAULT = {
    "name": "Stainless Steel 316L",
    "temperature_melt": (1673, "kelvin"),
    "temperature_liquidus": (1710.26, "kelvin"),
    "temperature_solidus": (1683.68, "kelvin"),
}


class PhaseTransformationTemperaturesDict(TypedDict):
    name: str

    # Melting Temperature (K)
    temperature_melt: QuantityDict

    # Liquidus Temperature (K)
    temperature_liquidus: QuantityDict

    # Solidus Temperature (K)
    temperature_solidus: QuantityDict


class PhaseTransformationTemperatures(QuantityModel):
    """
    Phase Transformation Temperatures calculated by tc-python.
    """

    name: str = DEFAULT["name"]

    temperature_melt: QuantityField = DEFAULT["temperature_melt"]
    temperature_liquidus: QuantityField = DEFAULT["temperature_liquidus"]
    temperature_solidus: QuantityField = DEFAULT["temperature_solidus"]

from typing_extensions import TypedDict
from pintdantic import QuantityDict, QuantityModel, QuantityField

# DEFAULT = {
#     "name": "Stainless Steel 316L",
#     "temperature_melt": (1673, "kelvin"),
#     "temperature_liquidus": (1710.26, "kelvin"),
#     "temperature_solidus": (1683.68, "kelvin"),
# }


class ResistivityDict(TypedDict):
    name: str

    # Solidus Temperature (Ohm * m)
    electric_resistivity: QuantityDict


class Resistivity(QuantityModel):
    """
    Resistivity values calculated by tc-python
    """

    name: str

    electric_resistivity: QuantityField

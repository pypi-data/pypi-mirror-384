from .__main__ import app

from .calculate_property_diagram import register_property_diagram_calculate
from .temperatures import register_compute_temperatures

_ = register_property_diagram_calculate(app)
_ = register_compute_temperatures(app)

__all__ = ["app"]

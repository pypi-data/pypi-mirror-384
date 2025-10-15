from .__main__ import app

from .alloy_composition import register_alloy_composition
from .alloy_list import register_alloy_list

_ = register_alloy_composition(app)
_ = register_alloy_list(app)

__all__ = ["app"]

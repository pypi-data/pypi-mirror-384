from .__main__ import app

from .composition import register_schema_composition

_ = register_schema_composition(app)

__all__ = ["app"]

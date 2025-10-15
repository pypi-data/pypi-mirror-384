from .__main__ import app
from .install import register_mcp_install

_ = register_mcp_install(app)

__all__ = ["app"]

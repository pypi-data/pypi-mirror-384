from .__main__ import app
from .version import register_version
from .install import register_install

__all__ = ["app"]

from tc.mcp.cli import app as mcp_app
from tc.alloy.cli import app as alloy_app
from tc.schema.cli import app as schema_app
from tc.property_diagram.cli import app as property_diagram_app

app.add_typer(mcp_app, name="mcp")
app.add_typer(alloy_app, name="alloy")
app.add_typer(schema_app, name="schema")
app.add_typer(property_diagram_app, name="property-diagram")

_ = register_version(app)
_ = register_install(app)

if __name__ == "__main__":
    app()

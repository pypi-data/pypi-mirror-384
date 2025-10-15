from mcp.server.fastmcp import FastMCP

from tc.alloy.mcp import register_alloy_resources, register_alloy_known_alloy
from tc.schema.mcp import register_schema_composition
from tc.property_diagram.mcp import (
    register_property_diagram_calculate,
    register_property_diagram_compile_material,
    register_property_diagram_compute_temperatures,
    register_property_diagram_compute_resistivity_at_temperature,
)

app = FastMCP(name="thermo-calc")

_ = register_alloy_known_alloy(app)
_ = register_alloy_resources(app)
_ = register_schema_composition(app)
_ = register_property_diagram_calculate(app)
_ = register_property_diagram_compute_temperatures(app)
_ = register_property_diagram_compute_resistivity_at_temperature(app)
_ = register_property_diagram_compile_material(app)


def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()

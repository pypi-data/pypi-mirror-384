from mcp.server import FastMCP
from pathlib import Path


def register_property_diagram_compute_resistivity_at_temperature(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Compute Resistivity values at a given temperature.",
        description="Calculate the resistivity values at a specified temperature (K) given an alloy composition filename. filename should include `.json` extension and temperature values are range values with units of K.",
        structured_output=True,
    )
    def property_diagram_compute_resistivity_at_temperature(
        workspace_name: str,
        property_diagram_name: str,
        temperature_ref: float,
    ) -> ToolSuccess[Path] | ToolError:
        from tc.property_diagram.resistivity import compute_resistivity_at_temperature

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        property_diagram_path = (
            workspace_path / "property_diagrams" / property_diagram_name
        )
        result_path = property_diagram_path / "result"
        resistivity_path = property_diagram_path / "resistivity.json"
        try:
            resistivity_at_temperature = compute_resistivity_at_temperature(
                name=property_diagram_name,
                result_path=result_path,
                temperature_ref=temperature_ref,
            )
            resistivity_at_temperature.save(resistivity_path)
            return tool_success(resistivity_path)

        except Exception as e:
            return tool_error(
                "Failed to get resistivity at temperature",
                "COMPUTE_RESISTIVITY_AT_TEMPERATURE_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = property_diagram_compute_resistivity_at_temperature

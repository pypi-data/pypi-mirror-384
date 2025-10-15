from mcp.server import FastMCP
from pathlib import Path


def register_property_diagram_compute_temperatures(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Compute Phase Transformation Solidus / Liquidus Temperatures",
        description="Calculate the solidus and liquids temperature given an alloy composition filename. filename should include `.json` extension and temperature_min and temperature_max values are range values with units of K.",
        structured_output=True,
    )
    def property_diagram_compute_temperatures(
        workspace_name: str,
        property_diagram_name: str,
    ) -> ToolSuccess[Path] | ToolError:
        from tc.property_diagram.temperatures import compute_temperatures

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        property_diagram_path = (
            workspace_path / "property_diagrams" / property_diagram_name
        )
        result_path = property_diagram_path / "result"
        phase_transformation_temperatures_path = (
            property_diagram_path / "temperatures.json"
        )
        try:
            temperatures = compute_temperatures(
                name=property_diagram_name, result_path=result_path
            )
            temperatures.save(phase_transformation_temperatures_path)
            return tool_success(phase_transformation_temperatures_path)

        except Exception as e:
            return tool_error(
                "Failed to get phase transformation liquidus and solidus temperatures",
                "COMPUTE_TEMPERATURES_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = property_diagram_compute_temperatures

from mcp.server import FastMCP
from pathlib import Path


def register_property_diagram_calculate(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error
    from tc.schema.composition import Composition
    from tc.property_diagram.calculate_property_diagram import (
        TEMPERATURE_MAX,
        TEMPERATURE_MIN,
    )

    @app.tool(
        title="Calculate Property Diagram",
        description="Calculate the property diagram of a given composition as save result as pickle file for later use. composition_filename should include `.json` extension and temperature_min and temperature_max values are range values with units of K.",
        structured_output=True,
    )
    def property_diagram_calculate(
        workspace_name: str,
        composition_filename: str,
        temperature_min: float = TEMPERATURE_MIN,
        temperature_max: float = TEMPERATURE_MAX,
    ) -> ToolSuccess[Path] | ToolError:
        from tc.property_diagram.calculate_property_diagram import (
            calculate_property_diagram,
        )

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        composition_path = workspace_path / "compositions" / composition_filename
        composition = Composition.load(composition_path)
        property_diagram_result_folder_path = (
            workspace_path / "property_diagrams" / composition.name
        )
        property_diagram_result_folder_path.mkdir(parents=True, exist_ok=True)

        result_path = property_diagram_result_folder_path / "result"

        try:
            calculate_property_diagram(
                composition=composition,
                temperature_min=temperature_min,
                temperature_max=temperature_max,
                save_path=result_path,
            )

            return tool_success(result_path)

        except Exception as e:
            return tool_error(
                "Failed to calculate property diagram",
                "CALCULATE_PROPERTY_DIAGRAM_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = property_diagram_calculate

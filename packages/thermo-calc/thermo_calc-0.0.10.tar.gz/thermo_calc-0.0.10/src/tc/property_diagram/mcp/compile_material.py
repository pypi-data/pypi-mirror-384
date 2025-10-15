from mcp.server import FastMCP
from pathlib import Path


def register_property_diagram_compile_material(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Compile material from property diagram.",
        description="Compile the computed material quantities into a Material class object for use in other tools in other MCP servers. Requires that temperature values have been calculated.",
        structured_output=True,
    )
    def property_diagram_compile_material(
        workspace_name: str,
        property_diagram_name: str,
        temperature_ref: float,
    ) -> ToolSuccess[Path] | ToolError:
        import math
        from tc.property_diagram.compute_quantity import compute_quantity_at_temperature
        from tc.schema.material import Material
        from tc.schema.phase_transformation_temperatures import (
            PhaseTransformationTemperatures,
        )

        from tc_python import ThermodynamicQuantity
        from typing_extensions import cast

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        property_diagram_path = (
            workspace_path / "property_diagrams" / property_diagram_name
        )

        result_path = property_diagram_path / "result"

        try:
            hm_t = cast(
                ThermodynamicQuantity,
                ThermodynamicQuantity.user_defined_function("HM.T"),
            )
            cp = compute_quantity_at_temperature(
                result_path=result_path,
                temperature_ref=temperature_ref,
                thermodynamic_quantity=hm_t,
            )

            b = cast(
                ThermodynamicQuantity, ThermodynamicQuantity.user_defined_function("B")
            )
            mass = compute_quantity_at_temperature(
                result_path=result_path,
                temperature_ref=temperature_ref,
                thermodynamic_quantity=b,
            )

            v = cast(
                ThermodynamicQuantity, ThermodynamicQuantity.user_defined_function("V")
            )
            volume = compute_quantity_at_temperature(
                result_path=result_path,
                temperature_ref=temperature_ref,
                thermodynamic_quantity=v,
            )

            if volume <= 0:
                return tool_error(
                    "Volume is less than or equal to zero",
                    "DENSITY_CALCULATION_FAILED",
                    exception_type="Divide by zero",
                    exception_message="Divide by zero",
                )

            density = mass / volume

            thermal_conductivity_quantity = cast(
                ThermodynamicQuantity, ThermodynamicQuantity.thermal_conductivity()
            )
            thermal_conductivity = compute_quantity_at_temperature(
                result_path=result_path,
                temperature_ref=temperature_ref,
                thermodynamic_quantity=thermal_conductivity_quantity,
            )

            electric_resistivity_quantity = cast(
                ThermodynamicQuantity, ThermodynamicQuantity.electric_resistivity()
            )
            electric_resisitivity = compute_quantity_at_temperature(
                result_path=result_path,
                temperature_ref=temperature_ref,
                thermodynamic_quantity=electric_resistivity_quantity,
            )

            wavelength_m = 1070.0e-9  # m
            absorptivity = 0.365 * math.sqrt(
                float(electric_resisitivity) / float(wavelength_m)
            )

            temperatures_path = property_diagram_path / "temperatures.json"
            temperatures = PhaseTransformationTemperatures.load(temperatures_path)

            material_path = (
                workspace_path / "materials" / f"{property_diagram_name}.json"
            )
            material = Material(
                name=property_diagram_name,
                specific_heat_capacity=(cp, "joules / (kilogram * kelvin)"),
                absorptivity=(absorptivity, "dimensionless"),
                thermal_conductivity=(thermal_conductivity, "watts / (meter * kelvin)"),
                density=(density, "gram / (meter) ** 3"),
                temperature_melt=temperatures.temperature_melt,
                temperature_liquidus=temperatures.temperature_liquidus,
                temperature_solidus=temperatures.temperature_solidus,
            )

            material.save(material_path)
            return tool_success(material_path)

        except Exception as e:
            return tool_error(
                "Failed to compile material",
                "COMPILE_MATERIAL_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = property_diagram_compile_material

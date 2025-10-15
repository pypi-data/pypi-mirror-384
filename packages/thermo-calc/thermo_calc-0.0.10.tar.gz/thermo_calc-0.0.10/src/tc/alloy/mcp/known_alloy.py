from mcp.server import FastMCP


def register_alloy_known_alloy(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error
    from tc.alloy.types import Alloy
    from tc.schema.composition import Composition

    @app.tool(
        title="List Known Alloys",
        description="Provides a list known alloys that have compositions and material properties.",
        structured_output=True,
    )
    def known_alloy_list() -> ToolSuccess[list[str] | None]:
        from tc.alloy.known_alloy import get_known_alloy_names

        known_alloy_names = get_known_alloy_names()

        return tool_success(known_alloy_names)

    @app.tool(
        title="Get Known Alloy Composition",
        description="Provide the elements and composition for a known alloy.",
        structured_output=True,
    )
    def known_alloy_composition(
        workspace_name: str, alloy: Alloy
    ) -> ToolSuccess[Composition | None] | ToolError:
        from tc.alloy.known_alloy import get_known_alloy_composition
        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace_name)
            composition = get_known_alloy_composition(alloy)
            composition_path = workspace_path / "compositions" / f"{alloy.name}.json"
            composition.save(composition_path)

            return tool_success(composition)

        except Exception as e:
            return tool_error(
                "Failed to get alloy composition",
                "ALLOY_COMPOSITION_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = (known_alloy_composition, known_alloy_list)

from mcp.server.fastmcp import FastMCP


def register_schema_composition(app: FastMCP):
    from tc.mcp.types import ToolSuccess, ToolError
    from tc.mcp.utils import tool_success, tool_error
    from tc.schema.composition import Composition

    @app.tool(
        title="Composition Schema",
        description="Creates a composition schema object given a set of elements and their compositions and saves to a given workspace. Inputs to composition should be a fraction (i.e. 95% Fe and 5% C would expect to have inputs of 0.95 Fe and 0.05 C)",
        structured_output=True,
    )
    def schema_composition(
        workspace_name: str,
        name: str,
        Fe: float | None = None,
        C: float | None = None,
        # TCFe alloys
        H: float | None = None,
        Mg: float | None = None,
        Ca: float | None = None,
        Y: float | None = None,
        Ti: float | None = None,
        Zr: float | None = None,
        V: float | None = None,
        Nb: float | None = None,
        Ta: float | None = None,
        Cr: float | None = None,
        Mo: float | None = None,
        W: float | None = None,
        Mn: float | None = None,
        Ru: float | None = None,
        Co: float | None = None,
        Ni: float | None = None,
        Cu: float | None = None,
        Zn: float | None = None,
        B: float | None = None,
        Al: float | None = None,
        Si: float | None = None,
        N: float | None = None,
        P: float | None = None,
        O: float | None = None,
        S: float | None = None,
        Ar: float | None = None,
        Ce: float | None = None,
        # TCNi12 extra elements,
        Hf: float | None = None,
        Re: float | None = None,
        Pd: float | None = None,
        Pt: float | None = None,
        # TCAl9 extra elements
        Li: float | None = None,
        Na: float | None = None,
        K: float | None = None,
        Be: float | None = None,
        Sr: float | None = None,
        Ba: float | None = None,
        Sc: float | None = None,
        Ga: float | None = None,
        Ge: float | None = None,
        Ag: float | None = None,
        In: float | None = None,
        Cd: float | None = None,
        Sn: float | None = None,
        Sb: float | None = None,
        Te: float | None = None,
        Se: float | None = None,
        Pb: float | None = None,
        Bi: float | None = None,
        La: float | None = None,
        Pr: float | None = None,
        Nd: float | None = None,
        Er: float | None = None,
        # TCHEA7
        Ir: float | None = None,
    ) -> ToolSuccess[Composition] | ToolError:
        """
        Creates a configuration file for material properties.
        """

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace_name)

            # Only include arguments that are not None
            values = {
                k: v
                for k, v in locals().items()
                if v is not None and k not in ["workspace_name"]
            }
            composition = Composition(**values)
            composition_path = workspace_path / "compositions" / f"{name}.json"
            composition.save(composition_path)

            return tool_success(composition)

        except Exception as e:
            return tool_error(
                "Failed to create composition schema",
                "SCHEMA_COMPOSITION_FAILED",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = schema_composition

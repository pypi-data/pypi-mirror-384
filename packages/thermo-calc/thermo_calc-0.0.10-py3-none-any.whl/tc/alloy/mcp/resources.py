from mcp.server import FastMCP


def register_alloy_resources(app: FastMCP):
    from tc.alloy.types import Alloy
    from tc.schema import Composition

    @app.resource("alloy://")
    def alloys() -> list[str] | None:
        from tc.alloy.known_alloy import get_known_alloy_names

        return get_known_alloy_names()

    @app.resource("alloy://{name}/composition")
    def alloy_composition(name: Alloy) -> Composition | None:
        from tc.alloy.known_alloy import get_known_alloy_composition

        return get_known_alloy_composition(name)

    _ = (alloys, alloy_composition)

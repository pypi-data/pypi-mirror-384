import typer

from rich import print as rprint

from wa.cli.options import WorkspaceOption


def register_property_diagram_calculate(app: typer.Typer):
    from tc.schema.composition import Composition
    from tc.property_diagram.defaults import TEMPERATURE_MAX, TEMPERATURE_MIN

    @app.command(name="calculate")
    def property_diagram_calculate(
        composition_filename: str,
        temperature_min: float = TEMPERATURE_MIN,
        temperature_max: float = TEMPERATURE_MAX,
        workspace: WorkspaceOption = None,
    ) -> None:
        """List known alloy composition."""
        from tc.property_diagram.calculate_property_diagram import (
            calculate_property_diagram,
        )
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        composition_path = workspace_path / "compositions" / composition_filename
        composition = Composition.load(composition_path)
        property_diagram_result_folder_path = (
            workspace_path / "property_diagrams" / composition.name
        )
        property_diagram_result_folder_path.mkdir(parents=True, exist_ok=True)

        try:
            result_path = property_diagram_result_folder_path / "result"
            calculate_property_diagram(
                composition=composition,
                temperature_min=temperature_min,
                temperature_max=temperature_max,
                save_path=result_path,
            )

            rprint(
                f"✅ [bold green]Property diagram object saved successfully[/bold green] → {result_path}"
            )

        except Exception as e:
            rprint("⚠️  [yellow]Unable to calculate property diagram[/yellow]")
            rprint(f"[yellow]Encountered Error: {e}[/yellow]")
            _ = typer.Exit()

    _ = property_diagram_calculate

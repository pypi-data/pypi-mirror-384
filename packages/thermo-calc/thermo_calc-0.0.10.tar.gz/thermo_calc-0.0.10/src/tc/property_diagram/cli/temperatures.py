import typer

from rich import print as rprint

from wa.cli.options import WorkspaceOption


def register_compute_temperatures(app: typer.Typer):

    @app.command(name="compute-temperatures")
    def compute_temperatures(
        property_diagram_name: str,
        workspace: WorkspaceOption = None,
    ) -> None:
        """List known alloy composition."""
        from tc.property_diagram.temperatures import compute_temperatures

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

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
            rprint(
                f"✅ [bold green]Phase transformation temperatures saved successfully[/bold green] → {phase_transformation_temperatures_path}"
            )

        except Exception as e:
            rprint("⚠️  [yellow]Unable to determine phase transformation[/yellow]")
            rprint(f"[yellow]Encountered Error: {e}[/yellow]")
            _ = typer.Exit()

    _ = compute_temperatures

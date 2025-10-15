import importlib.metadata
import typer

from rich import print as rprint


def register_version(app: typer.Typer):
    @app.command()
    def version() -> None:
        """Show the installed version of `thermo-calc` package."""
        try:
            version = importlib.metadata.version("thermo-calc")
            rprint(f"✅ thermo-calc version {version}")
        except importlib.metadata.PackageNotFoundError:
            rprint(
                "⚠️  [yellow]thermo-calc version unknown (package not installed)[/yellow]"
            )
            raise typer.Exit()

    return version

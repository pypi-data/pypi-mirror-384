import typer

from rich import print as rprint


def print_list(name: str, values: list[str] | None = None):
    rprint(f"\n  {name}:")
    if values is None:
        rprint(f"  ⚠️  [yellow]No {name} found.[/yellow]")
    else:
        for index, value in enumerate(values):
            rprint(f"  {index + 1}. [cyan]{value}[/cyan]")


def register_alloy_list(app: typer.Typer):
    @app.command(name="list")
    def alloy_list() -> None:
        """List known alloys."""
        from tc.alloy.known_alloy import get_known_alloy_names

        try:
            names = get_known_alloy_names()
            print_list("Known Alloys", names)
        except:
            rprint("⚠️  [yellow]Unable to list known alloys[/yellow]")
            _ = typer.Exit()

    _ = app.command(name="ls")(alloy_list)

    _ = alloy_list

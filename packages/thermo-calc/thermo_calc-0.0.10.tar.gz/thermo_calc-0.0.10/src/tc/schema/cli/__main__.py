import typer

app = typer.Typer(
    name="schema",
    help="Commonly used data schemas within package.",
    add_completion=False,
    no_args_is_help=True,
)

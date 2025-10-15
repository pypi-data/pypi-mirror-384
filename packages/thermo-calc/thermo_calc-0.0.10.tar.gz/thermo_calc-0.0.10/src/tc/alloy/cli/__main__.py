import typer

app = typer.Typer(
    name="Alloy",
    help="Generate or retrieve alloy using TC-Python",
    add_completion=False,
    no_args_is_help=True,
)

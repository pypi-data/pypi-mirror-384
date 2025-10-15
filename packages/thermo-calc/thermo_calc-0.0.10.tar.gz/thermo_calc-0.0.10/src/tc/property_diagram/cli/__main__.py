import typer

app = typer.Typer(
    name="Property Diagram",
    help="Utilize TC-Python to generate property diagram",
    add_completion=False,
    no_args_is_help=True,
)

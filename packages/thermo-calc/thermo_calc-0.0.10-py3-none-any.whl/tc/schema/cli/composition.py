import typer


def register_schema_composition(app: typer.Typer):
    import inspect

    from tc.schema.composition import Composition

    def schema_composition(**kwargs: float | None):
        """Create file for composition."""
        try:
            composition = Composition(**kwargs)
            print(composition.model_dump_json(indent=2))
        except Exception as e:
            typer.secho(f"⚠️ Unable to create composition: {e}", fg=typer.colors.YELLOW)
            raise typer.Exit(code=1)

    # Dynamically build parameters from Composition fields
    params = []
    for field, model_field in Composition.model_fields.items():
        default = model_field.default
        annotation = float | None
        option = inspect.Parameter(
            field,
            inspect.Parameter.KEYWORD_ONLY,
            default=typer.Option(default, help=f"{field} composition fraction"),
            annotation=annotation,
        )
        params.append(option)

    # Assign a new signature to schema_composition
    schema_composition.__signature__ = inspect.Signature(
        parameters=params,
        return_annotation=None,
    )

    app.command("composition")(schema_composition)
    return schema_composition

import asyncio
from typing import Annotated

from chorey.utils import MissingFeatureError, import_pipeline, parse_cli_input

try:
    import typer
except ImportError:
    raise MissingFeatureError("cli")


app = typer.Typer(
    name="chorey",
    help="A CLI tool to run and visualize Chorey pipelines defined in Python modules.",
)


@app.command(
    short_help="Run a Chorey pipeline defined in a Python module.",
)
def run(
    pipeline_path: str = typer.Argument(
        ...,
        help="Path to the pipeline module, e.g., 'my_pipeline.py' or 'my_module:my_pipeline'",
    ),
    input: Annotated[
        str | None,
        typer.Option(
            "--input",
            "-i",
            help="Input value to feed into the pipeline. Can be primitive or JSON-encoded.",
        ),
    ] = None,
):
    pipeline = import_pipeline(pipeline_path)
    first_input_type = pipeline.first_input_type
    parsed_input = parse_cli_input(input, first_input_type)

    result = asyncio.run(pipeline.feed(parsed_input))
    print(result)


@app.command(
    short_help="Generate a Mermaid diagram of the pipeline structure.",
)
def visualize(
    pipeline_path: str = typer.Argument(
        ...,
        help="Path to the pipeline module, e.g., 'my_pipeline.py' or 'my_module:my_pipeline'",
    ),
):
    from chorey import mermaid

    pipeline = import_pipeline(pipeline_path)
    print(mermaid(pipeline))


if __name__ == "__main__":
    app()

"""Console script for shoestring_assembler."""

import shoestring_assembler
from shoestring_assembler.model.recipe import Recipe
from shoestring_assembler.display import Display
from shoestring_assembler.interface.signals import Action

import typer
from typing_extensions import Annotated
import os
import sys
import asyncio

typer_app = typer.Typer(name="Shoestring Assembler", no_args_is_help=True)

@typer_app.command()
def download(
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show extra logs.")
    ] = False,
):
    """
    Download a new solution 
    """
    execute(Action.DOWNLOAD, verbose=verbose)


@typer_app.command()
def update(
    version: Annotated[
        str, typer.Argument(help="Update to this version. (optional)")
    ] = "",
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show extra logs.")
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes", "-y", help="Automatically download and assemble the latest version"
        ),
    ] = False,
    recipe_location: Annotated[
        str, typer.Argument(help="Path to recipe file")
    ] = "./recipe.toml",
):
    """
    Updates the solution to the specified version. If a version is not specified - it lists the available versions that you can choose from.
    """
    execute(
        Action.UPDATE,
        version=version,
        no_prompt=yes,
        recipe_location=recipe_location,
        verbose=verbose,
    )


@typer_app.command()
def assemble(
    recipe: Annotated[
        str, typer.Argument(help="Path to recipe file")
    ] = "./recipe.toml",
    download: bool = True,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show extra logs.")
    ] = False,
):
    """
    Assembles the solution using the provided recipe
    """
    execute(
        Action.ASSEMBLE,
        recipe_location=recipe,
        verbose=verbose,
        download=download,
    )


@typer_app.command()
def reconfigure(
    recipe_location: Annotated[
        str, typer.Argument(help="Path to recipe file")
    ] = "./recipe.toml",
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Show extra logs.")
    ] = False,
):
    """
    Generates configuration files based on user input.
    """
    execute(Action.RECONFIGURE, recipe_location=recipe_location, verbose=verbose)


@typer_app.command()
def build():
    """
    Builds the solution's docker images
    """
    execute(Action.BUILD)


@typer_app.command()
def setup():
    """
    Runs setup scripts for containers that have them
    """
    execute(Action.SETUP)


@typer_app.command()
def start():
    """
    Starts the solution
    """
    execute(Action.START)


@typer_app.command()
def stop():
    """
    Stops the solution
    """
    execute(Action.STOP)


@typer_app.command()
def restart():
    """
    Stops, rebuilds, and starts the solution
    """
    execute(Action.RESTART)


@typer_app.command()
def check_recipe(
    recipe: Annotated[
        str, typer.Argument(help="Path to recipe file")
    ] = "./recipe.toml",
):
    """
    Validates the provided recipe file
    """
    Display.print_top_header("Checking Recipe")

    loop = asyncio.get_event_loop()
    check_task = loop.create_task(Recipe.load(recipe))
    try:
        loop.run_until_complete(check_task)
        Display.print_complete("Recipe is valid")
        Display.print_top_header("Finished")
    except asyncio.CancelledError:
        Display.print_error("Failed")


@typer_app.command()
def logs(service: Annotated[str, typer.Option(help="Service to log")] = None):
    """
    Shows the logs for the solution or a specific service if specified
    """
    from shoestring_assembler.engine.action.docker import Docker
    from shoestring_assembler.model.solution import SolutionModel

    solution_model = SolutionModel()
    Docker.logs(solution_model, service)


@typer_app.command()
def app():
    """
    Runs the interactive CLI application
    """
    from shoestring_assembler.view.cli_app import SolutionAssemblerApp

    app = SolutionAssemblerApp()
    app.run()


@typer_app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool, typer.Option("--version", "-v", help="Assembler version")
    ] = False,
):
    if version:
        Display.print_log(
            f"Shoestring Assembler version {shoestring_assembler.__version__}"
        )
    else:
        pass


from shoestring_assembler.view.plain_cli import PlainCLI


def execute(action, *, recipe_location=None, verbose=False, **kwargs):
    if verbose:
        Display.log_level = 5

    ui = PlainCLI(action)
    loop = asyncio.get_event_loop()
    ui_task = loop.create_task(ui.run())
    try:
        loop.run_until_complete(ui_task)
    except asyncio.CancelledError:
        Display.print_error("Closing")


def app():
    try:
        if os.geteuid() == 0:
            Display.print_error(
                "To try prevent you from accidentally breaking things, this program won't run with sudo or as root! \nRun it again without sudo or change to a non-root user."
            )
            sys.exit(255)
        typer_app()
    finally:
        Display.finalise_log()


if __name__ == "__main__":
    app()

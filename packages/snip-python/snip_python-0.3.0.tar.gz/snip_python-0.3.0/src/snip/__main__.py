"""Cli entry point.

Used for both the python -m snip-lab and as package script i.e. snip.

"""

from logging import DEBUG, INFO

import typer

from .logger import log
from .snippets.__main__ import snippet_app
from .token.__main__ import token_app

app = typer.Typer(
    rich_markup_mode="rich",
    help="Command line tool for [bold italic]snip[/bold italic] - our digital lab book.",
)

# Add subcommands
app.add_typer(token_app)
app.add_typer(snippet_app)


# Add global verbose option
@app.callback()
def select_verbose(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output."),
):
    if verbose:
        log_level = DEBUG
    else:
        log_level = INFO

    log.setLevel(log_level)
    log.debug("Verbose output.")


if __name__ == "__main__":  # pragma: no cover
    app()

from typing import Optional, Union, cast

import typer
from keyring import get_keyring
from keyring.backend import KeyringBackend, get_all_keyring
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated, Literal

from snip.token.token import AccountToken, Token

from ..logger import log
from . import BookToken
from .storage import get_all_tokens
from .storage import keyring_store as keyring_store

token_app = typer.Typer(
    name="token",
    help="Manage your tokens for authentication with a snip instance.",
)

selected_keyring: Optional[KeyringBackend] = None


def parse_keyring(value: Union[str, KeyringBackend] = "default") -> KeyringBackend:
    if isinstance(value, KeyringBackend):
        log.debug(f"No keyring selected. Using default keyring {value.name}")
        return value

    if value == "default":
        return get_keyring()

    all_backends = get_all_keyring()
    keyring = None
    for backend in all_backends:
        if value in backend.name.replace(" ", "."):
            keyring = backend

    if keyring is None:
        raise typer.BadParameter("Keyring not found.")

    return keyring


def autocomplete_keyring(incomplete: str):
    all_backends = get_all_keyring()
    return [
        backend.name.replace(" ", ".")
        for backend in all_backends
        if incomplete in backend.name.replace(" ", ".")
    ]


@token_app.callback()
def select_keyring(
    kr: Optional[KeyringBackend] = typer.Option(
        None,
        "--keyring",
        "-k",
        help="Select a keyring backend.",
        parser=parse_keyring,
        autocompletion=autocomplete_keyring,
    ),
):
    global selected_keyring
    if kr is not None:
        selected_keyring = kr
    else:
        selected_keyring = get_keyring()


@token_app.command("list")
def list():
    """List all available tokens."""
    if selected_keyring is None:
        raise typer.BadParameter("No keyring selected.")

    # From keyring
    tokens, sources = get_all_tokens(selected_keyring)

    if len(tokens) == 0:
        log.warning(
            "No tokens found! Add a token with 'snip` token add' or add an '.sniprc' file with tokens."
        )
        return

    console = Console()
    table = Table(show_edge=False)
    table.add_column("Type", style="bold magenta")
    table.add_column("Name", style="bold cyan")
    table.add_column("Book ID", style="cyan")
    table.add_column("Deployment", style="cyan")
    table.add_column("Token", style="cyan")
    table.add_column("Source", style="cyan")

    for token, source in zip(tokens, sources):
        table.add_row(
            token.type,
            token.name,
            str(token.book_id) if isinstance(token, BookToken) else "-",
            token.deployment_url,
            token.token[:4] + "..." + token.token[-4:],
            str(source),
        )

    console.print(table)


def valid_name(name: str, kr: KeyringBackend) -> str:
    if name is None or name == "":
        raise typer.BadParameter("Name cannot be empty.")
    if " " in name:
        raise typer.BadParameter("Name cannot contain spaces.")
    if keyring_store.token_exists(name, kr):
        raise typer.BadParameter("Token with this name already exists!")
    return name


@token_app.command()
def add(
    token: Annotated[str, typer.Argument(help="Token string to add to the keyring.")],
    name: Annotated[
        Optional[str],
        typer.Option(
            help="The name of the token, should be unique. If not provided, it will be prompted for.",
        ),
    ] = None,
    type: Annotated[
        Literal["book", "account"],
        typer.Option(
            case_sensitive=False,
            help="The type of the token. Currently only 'book' and 'account' are supported.",
        ),
    ] = "book",
    book_id: Annotated[
        Optional[int],
        typer.Option(
            help="The book ID for the token. If not provided, it will be prompted for.",
        ),
    ] = None,
    deployment_url: Annotated[
        str, typer.Option(help="The deployment URL i.e. the URL of the snip instance.")
    ] = BookToken.deployment_url,
):
    """Add a snip token your keyring storage."""
    if selected_keyring is None:
        raise typer.BadParameter("No keyring selected.")

    # Check promptvalues
    if name is None:
        name = typer.prompt(
            "Name of the token, should be unique (e.g. MyTokenForBook1)",
            value_proc=lambda x: valid_name(x, cast(KeyringBackend, selected_keyring)),
        )

    t: Token
    if type == "book":
        log.debug("Adding book token.")
        if book_id is None:
            book_id = typer.prompt(
                "Book ID for the token (use --type to add account token)", type=int
            )
        if book_id is None:
            raise typer.BadParameter("Book ID cannot be None.")

        t = BookToken.from_unsafe(
            str(name),
            token,
            book_id,
            deployment_url,
        )

    elif type == "account":
        log.debug("Adding account token.")

        t = AccountToken.from_unsafe(
            str(name),
            token,
            deployment_url,
        )

    # Save token
    keyring_store.save_token(t, selected_keyring)
    log.info(
        f"Saved token '{t}' to keyring '{selected_keyring.name.replace(' ', '.')}'!"
    )


def autocomplete_token_names(incomplete: str):
    kr = get_keyring()
    if kr is None:
        raise typer.BadParameter("No keyring selected.")

    return [
        token.name
        for token in keyring_store.get_all_tokens(kr)
        if incomplete in token.name
    ]


@token_app.command()
def remove(
    name: Annotated[
        str,
        typer.Argument(
            help="The name of the token to remove.",
            autocompletion=autocomplete_token_names,
        ),
    ],
):
    """Remove a token from your keyring storage."""
    if selected_keyring is None:
        raise typer.BadParameter("No keyring selected.")

    if not keyring_store.token_exists(name, selected_keyring):
        raise typer.BadParameter("Token not found.")

    keyring_store.remove_token(name, selected_keyring)
    log.debug(f"Removed token '{name}' from keyring '{selected_keyring.name}'!")

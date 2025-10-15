import json
import os
import tempfile
from typing import Annotated, Optional, TypedDict, cast

import jsonschema
import typer

from ..api import DEFAULT_DEPLOYMENT_URL
from ..api.exceptions import AuthenticationException
from ..api.schemas import get_schema
from ..api.snippets import get_snip_preview, upload_snip
from ..logger import log
from ..token import BookToken
from ..token.storage import get_tokens_by_book_and_deployment

snippet_app = typer.Typer(
    name="snippet",
    help="Upload or validate snippets.",
)


TokenTyper = Annotated[
    Optional[str],
    typer.Option(
        "--token",
        "-t",
        help="The token to use if none is give, the token is read from the keyring or files and is automatically matched top the given snippet.",
    ),
]

DeploymentTyper = Annotated[
    Optional[str],
    typer.Option(
        "--deployment",
        "-d",
        help="The deployment URL i.e. the URL of the snip instance.",
    ),
]

FileTyper = Annotated[
    typer.FileText,
    typer.Argument(
        help="The file json file upload.",
    ),
]

ValidateTyper = Annotated[
    bool,
    typer.Option(
        "--validate",
        "-v",
        help="Validate the snippet before uploading it.",
    ),
]


@snippet_app.command()
def upload(
    file: FileTyper,
    validate: ValidateTyper = True,
    token: TokenTyper = None,
    deployment_url: DeploymentTyper = DEFAULT_DEPLOYMENT_URL,
):
    """Upload a snippet to a snip instance."""
    # 1. Read the json file
    json_snippet = json.loads(file.read())

    # 2. Validate the snippet
    # Check if the snippet has a type
    json_snippet = _initialCheck(json_snippet)
    if validate:
        _validate(json_snippet, deployment_url)

    # 3. Get token
    if token is None:
        token_p = _get_token(json_snippet["book_id"], deployment_url)
    else:
        token_p = BookToken.from_unsafe(
            "temp_token", json_snippet["book_id"], token, deployment_url
        )

    # 4. Upload the snippet
    log.debug(f"Uploading snippet with token: {token_p}")
    upload_snip(cast(dict, json_snippet), token_p)


@snippet_app.command()
def validate(
    file: FileTyper,
    deployment_url: DeploymentTyper = DEFAULT_DEPLOYMENT_URL,
):
    """Validate a snippet."""
    # 1. Read the json file
    json_snippet = json.loads(file.read())

    # 2. Validate the snippet
    # Check if the snippet has a type
    json_snippet = _initialCheck(json_snippet)
    valid = _validate(json_snippet, deployment_url)

    if valid:
        log.info("Snippet is valid.")
        return
    else:
        raise typer.Exit(code=1)


@snippet_app.command()
def preview(
    file: FileTyper,
    validate: ValidateTyper = True,
    token: TokenTyper = None,
    deployment_url: DeploymentTyper = DEFAULT_DEPLOYMENT_URL,
):
    """Preview a snippet."""
    # 1. Read the json file
    json_snippet = json.loads(file.read())

    # 2. Check if the snippet has a type
    json_snippet = _initialCheck(json_snippet)
    if validate:
        _validate(json_snippet, deployment_url)

    # 3. Get token
    if token is None:
        token_p = _get_token(json_snippet["book_id"], deployment_url)
    else:
        token_p = BookToken.from_unsafe(
            "temp_token",
            json_snippet["book_id"],
            token,
            deployment_url=deployment_url,
        )

    img = get_snip_preview(cast(dict, json_snippet), token_p)

    # Save the image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_filename = temp_file.name
        img.save(temp_filename)

    os.system(f"start {temp_filename}" if os.name == "nt" else f"open {temp_filename}")

    return typer.Exit(code=0)


class __CheckedDict(TypedDict):
    book_id: int
    type: str


def _initialCheck(dict: dict):
    """Check if the dict has the required fields.

    Parameters
    ----------
    dict : dict
        The dict to check.

    Returns
    -------
    CheckedDict
        The checked dict.
    """
    if "book_id" not in dict:
        raise typer.BadParameter("Data does not have a `book_id` field.")
    if "type" not in dict:
        raise typer.BadParameter("Data does not have a `type` field.")
    return cast(__CheckedDict, dict)


def _validate(dict: __CheckedDict, deployment: Optional[str] = DEFAULT_DEPLOYMENT_URL):
    """Validate the data.

    Automatically gets the type
    and gets the schema from the deployment.

    Parameters
    ----------
    dict : dict
        The data to validate
    deployment : str, optional
        The deployment URL to get the schema from.

    Returns
    -------
    bool
        Whether the data is valid or if the validation failed.

    Raises
    ------
    jsonschema.ValidationError
        If the data does not match the schema.
    jsonschema.SchemaError
        If the schema is invalid.
    """
    schema = None
    try:
        schema = get_schema(dict["type"], deployment=deployment)
    except Exception as e:
        log.warning(f"Error getting schema: {e}")

    if schema is None:
        log.warning("No schema found. Skipping validation.")
    else:
        # Check if the schema is valid
        jsonschema.validate(dict, schema=schema)
        return True

    return False


def _get_token(
    book_id: int | str,
    deployment_url: Optional[str] = DEFAULT_DEPLOYMENT_URL,
):
    tokens, sources = get_tokens_by_book_and_deployment(book_id, deployment_url)

    if len(tokens) == 0:
        raise AuthenticationException(
            "No token provided and no token found for this snip using its book_id. Please provide a token manually, add one in an .sniprc file or use your keyring."
        )

    if len(tokens) > 1:
        log.info(f"Multiple tokens found. Using {tokens[0].name} from {sources[0]}")

    return tokens[0]

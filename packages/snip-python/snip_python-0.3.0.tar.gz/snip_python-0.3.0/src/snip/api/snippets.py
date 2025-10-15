"""Interface with snippet related endpoints.

Allows to generate previews, test snippets and upload snippets to a deployment.
"""

import io
from functools import lru_cache

import requests
from PIL import Image

from ..token import BookToken, Token
from . import DEFAULT_DEPLOYMENT_URL
from .request import request, request_image


def get_snip_preview(dict: dict, token: Token, **kwargs) -> Image.Image:
    """Generate a preview image for the given snippet as dict /json.

    This method only checks the validity of the dict on the server side
    and returns the preview image as a PIL Image object if it is valid.

    Parameters
    ----------
    dict : dict
        The snippet as a dictionary.
    deployment : str, optional
        The deployment to generate the preview for.
        If None, the default deployment is used.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.post function.

    Returns
    -------
    Image.Image
        The preview image as a PIL Image object.
    """
    return request_image(
        method="POST",
        url=f"{token.deployment_url}/render/snip",
        token=token,
        json=dict,
        **kwargs,
    )


def upload_snip(snippet: dict, token: Token, **kwargs) -> dict:
    """Upload a snippet given a token.

    If the book_id of the snippet and taken first from the token
    do not match, a ValueError is raised.

    Parameters
    ----------
    snippet : dict
        The snippet to upload.
    token : Token
        The token to use for the upload.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.post function.
    """
    # Update book id if not set
    if (
        "book_id" not in snippet
        or snippet["book_id"] is None
        or snippet["book_id"] <= 0
    ):
        if isinstance(token, BookToken):
            snippet["book_id"] = token.book_id

    if "book_id" not in snippet or snippet["book_id"] is None:
        raise ValueError("Snippet book_id is required for upload!")

    if isinstance(token, BookToken) and snippet["book_id"] != token.book_id:
        raise ValueError("Snippet book_id does not match token book_id!")

    if "data" in snippet and "snip" in snippet["data"]:
        snippet["data"]["snip"]["book_id"] = snippet["book_id"]

    if "type" not in snippet:
        raise ValueError("Snippet `type` is required for upload!")

    data = request(
        method="POST",
        url=f"{token.deployment_url}/api/books/{snippet['book_id']}/upload",
        token=token,
        json=snippet,
        **kwargs,
    )

    if data is None:
        raise ValueError("No data returned from the API.")
    if not isinstance(data, dict):
        raise ValueError("Invalid data returned from the API.")
    return data


@lru_cache
def get_font(font: str, **kwargs):
    """Get a PIL ImageFont object for the given font and size.

    Parameters
    ----------
    font : str
        The font to use.
    size : int
        The size of the font.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.get function.

    Returns
    -------
    ImageFont
        The PIL ImageFont object.
    """
    font = _parse_font(font)

    res = requests.request(
        method="GET",
        url=f"{DEFAULT_DEPLOYMENT_URL}/fonts/{font}",
        allow_redirects=True,
        stream=True,
        **kwargs,
    )

    return io.BytesIO(res.content)  # type: ignore


def _parse_font(font: str) -> str:
    """Parse the font name to match the server side font name.

    Parameters
    ----------
    font : str
        The font name to parse.

    Returns
    -------
    str
        The parsed font name which matches the server side font name.
    """
    # A bit of font matching
    if "caveat" in font.lower():
        font = "caveat.ttf"

    if "plex" in font.lower() and "mono" in font.lower():
        font = "IBM_Plex_Mono.ttf"

    if "arial" in font.lower():
        font = "arial.ttf"

    if "courier" in font.lower() and "new" in font.lower():
        font = "courier_new.ttf"

    return font

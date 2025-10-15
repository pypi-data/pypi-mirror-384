"""Make requests to the Snips API."""

import io
from typing import Optional, Union

import requests
from PIL import Image

from ..token import Token
from . import ADDITIONAL_REQUEST_ARGS
from .exceptions import AuthenticationException, BadRequestException


def request(
    method: str, url: str, token: Optional[Token] = None, **kwargs
) -> Union[dict, list, Image.Image, None]:
    """Make a request to the given URL with the given method and authentication token.

    Parameters
    ----------
    method : str
        The HTTP method to use for the request.
    url : str
        The URL to make the request to.
    token : Token
        The authentication token to use for the request.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.request function.

    Returns
    -------
    ParseResponse
        The parsed response from the request.

    Raises
    ------
    and see parse_response

    """
    kwargs.setdefault("headers", {})
    if token is not None:
        auth_header = {"Authorization": f"Bearer {token.token}"}
        kwargs["headers"].update(auth_header)
    kwargs.update(ADDITIONAL_REQUEST_ARGS)

    res = requests.request(method, url, **kwargs)

    return parse_response(res, token)


def request_image(
    method: str, url: str, token: Optional[Token] = None, **kwargs
) -> Image.Image:
    """Fetch an image from the given URL and returns it as a PIL Image object.

    Parameters
    ----------
    method : str
        The HTTP method to use for the request.
    url : str
        The URL of the image to fetch.
    token : Optional[Token]
        The authentication token to use for the request.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.requests function.

    Returns
    -------
    Image.Image
        The fetched image as a PIL Image object.

    """
    data = request(method, url, token=token, stream=True, **kwargs)

    if data is None:
        raise ValueError("No data returned from the API.")
    if not isinstance(data, Image.Image):
        raise ValueError("Invalid data returned from the API.")

    return data


def parse_response(
    response: requests.Response, token: Optional[Token] = None
) -> Union[dict, list, Image.Image, None]:
    """Parse a response from a request.

    Parameters
    ----------
    response : requests.Response
        The response object to parse.
    token : Optional[Token]
        The authentication token used for the request. For better error messages.

    Returns
    -------
    dict[str, Optional[str]]
        The parsed response.

    Raises
    ------
    AuthenticationException
        If the request was not successful due to an authentication problem.
    BadRequestException
        If the request was not successful due to a bad request.
    HTTPError
        If the request was not successful due to a server error or other problem.
    """
    # Check different status codes
    if response.status_code == 400:
        # Try to parse json as our api returns json error messages
        message = "Bad request"
        details = None
        try:
            data = response.json()
        except ValueError:
            data = {}

        if isinstance(data, dict):
            message = data.get("message", "Bad request")
            details = data.get("details", None)
        raise BadRequestException(message, details)

    if response.status_code == 401:
        try:
            data = response.json()
        except ValueError:
            data = {}
        raise AuthenticationException(
            data.get("message", "Authentication failed!"),
            details=data.get("details", None),
        )
    if response.status_code == 403:
        try:
            data = response.json()
        except ValueError:
            data = {}
        raise AuthenticationException(
            data.get("message", "You do not have permission to access this resource!"),
            details=data.get("details", None),
        )

    response.raise_for_status()

    # Parse the response
    data = None
    if "application/json" in response.headers.get("content-type", ""):
        data = response.json()
    if response.headers.get("content-type") == "image/png":
        data = Image.open(io.BytesIO(response.content))

    return data

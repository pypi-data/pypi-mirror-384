from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, TypedDict

if TYPE_CHECKING:  # pragma: no cover
    from ..token import Token


class TokenMetadata(TypedDict):
    """Metadata of a token.

    The server can provide additional information about a token which allows
    the user to better understand the purpose and validity of the token.
    """

    # Optional expiration date, if none the token is valid indefinitely
    expires_at: Optional[datetime.datetime]
    # Optional description of the token
    description: Optional[str]
    # Users email address who created the token
    created_by: str
    # When the metadata was retrieved
    retrieved_at: datetime.datetime


def get_metadata(token: Token) -> TokenMetadata:
    """Get the metadata of a token.

    This performs a request to the deployment defined in the token
    to retrieve the metadata of the token.

    Parameters
    ----------
    token : Token
        The token to retrieve the metadata from.

    Returns
    -------
    TokenMetadata
        The metadata of the token.

    Raises
    ------
    AuthenticationException
        If the token is invalid.
    """
    raise NotImplementedError("This endpoint is currently broken.")

    """
    if data is None:
        raise ValueError("No data returned from the API.")

    if not isinstance(data, dict):
        raise ValueError("Invalid data returned from the API.")

    expires_at = data.get("expires_at")
    expires_at = datetime.datetime.fromisoformat(expires_at) if expires_at else None

    return TokenMetadata(
        expires_at=expires_at,
        description=data["description"],
        created_by=data["created_by"],
        retrieved_at=datetime.datetime.now(),
    )
    """

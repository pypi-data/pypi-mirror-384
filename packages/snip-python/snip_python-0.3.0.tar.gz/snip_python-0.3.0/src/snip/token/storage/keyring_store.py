"""Functionalities to save and retrieve tokens from a keyring.

A token always consists of a `name`, a `book_id` and a `token string`. The name is a user defined string to identify the token and should be unique.

We abuse the standard keyring functionalities a bit to store key value pairs. We use a global prefix in combination with the name to store the key value pairs for each token.

.. code-block:: python

    kr.set_password(SNIP_KR_IDENTIFIER, f"{name.as_hex}:book_id", book_id)
    kr.set_password(SNIP_KR_IDENTIFIER, f"{name.as_hex}:token", token_str)

As we also want to retrieve all tokens from the keyring we need to store an index of all tokens in the keyring.

.. code-block:: python

    kr.set_password(SNIP_KR_IDENTIFIER, f"index", f"{name.as_hex},{name2.as_hex},...")
"""

from typing import Optional

from keyring.backend import KeyringBackend

from ...logger import log
from ..token import AccountToken, BookToken, Token

# An identifier for all the key value pairs in the keyring
SNIP_KR_IDENTIFIER = "snip_lab:v1"


def get_all_tokens(kr: KeyringBackend) -> list[Token]:
    """Get all available tokens from a keyring backend.

    Abstracts the parsing of the key value pairs from
    the keyring backend and returns valid tokens.

    Parameters
    ----------
    kr : KeyringBackend
        The keyring backend to retrieve the tokens from.

    Returns
    -------
    list[Token]
        A list of all valid found in the keyring.
    """
    # Get the index of all tokens
    hex_names = _get_index(kr)

    tokens: list[Token] = []
    for hn in hex_names:
        token = _get_token(hn, kr)
        if token is not None:
            tokens.append(token)
        else:
            log.warning(
                f"Token {__decode_name(hn)} ({hn}) is invalid. Try to delete or recreate it to fix the issue."
            )

    return tokens


def get_token(name: str, kr: KeyringBackend) -> Optional[Token]:
    """Get a token from the keyring storage.

    Parameters
    ----------
    name : str
        The name of the token.
    kr : KeyringBackend
        The keyring backend to retrieve the token from.

    Returns
    -------
    Token | None
        The token object or None if not found.
    """
    return _get_token(__encode_name(name), kr)


def _get_token(hex_name: str, kr: KeyringBackend) -> Optional[Token]:
    """Get a saved token from the keyring storage.

    Parameters
    ----------
    hex_name : str
        The hex name of the token.
    kr : KeyringBackend
        The keyring backend to retrieve the token from.

    Returns
    -------
    Token | None
        The token object or None if not found.
    """
    token_type = kr.get_password(SNIP_KR_IDENTIFIER, f"{hex_name}:type")
    token = kr.get_password(SNIP_KR_IDENTIFIER, f"{hex_name}:token")

    # Optional deployment url and book id
    book_id = kr.get_password(SNIP_KR_IDENTIFIER, f"{hex_name}:book_id")
    dep = kr.get_password(SNIP_KR_IDENTIFIER, f"{hex_name}:deployment")

    if token is None:
        log.debug(f"Token {__decode_name(hex_name)} not found.")
        return None

    if token_type == "account":
        return AccountToken.from_unsafe(
            name=__decode_name(hex_name),
            token=token,
            deployment_url=dep,
        )
    else:
        log.debug(f"Token {__decode_name(hex_name)} ({hex_name}) is of type 'book'.")

        if book_id is None:
            log.warning(
                f"Token {__decode_name(hex_name)} ({hex_name}) is missing book_id."
            )
            return None

        return BookToken.from_unsafe(
            name=__decode_name(hex_name),
            book_id=book_id,
            token=token,
            deployment_url=dep,
        )


def save_token(token: Token, kr: KeyringBackend, overwrite: bool = False):
    """Save a token in the keyring storage.

    Parameters
    ----------
    token : Token
        The token object to save.
    kr : KeyringBackend
        The keyring backend to save the token to.
    """
    # Get index
    index = _get_index(kr)
    hex_name = __encode_name(token.name)

    # Check if token already exists
    if not overwrite and hex_name in index:
        raise ValueError(f"Token with name {token.name} already exists.")

    # Insert token
    kr.set_password(SNIP_KR_IDENTIFIER, f"{hex_name}:type", str(token.type))
    if hasattr(token, "book_id"):
        assert isinstance(token, BookToken), (
            "token must be a BookToken if it has a book_id"
        )
        kr.set_password(SNIP_KR_IDENTIFIER, f"{hex_name}:book_id", str(token.book_id))
    kr.set_password(SNIP_KR_IDENTIFIER, f"{hex_name}:token", token.token)
    if token.deployment_url != BookToken.deployment_url:
        kr.set_password(
            SNIP_KR_IDENTIFIER, f"{hex_name}:deployment", token.deployment_url
        )

    # Update index
    index.append(hex_name)
    _set_index(index, kr)


def token_exists(name: str, kr: KeyringBackend) -> bool:
    """Check if a token exists in the keyring storage.

    Parameters
    ----------
    name : str
        The name of the token to check.
    kr : KeyringBackend
        The keyring backend to check the token in.

    Returns
    -------
    bool
        True if the token exists, False otherwise.
    """
    return __encode_name(name) in _get_index(kr)


def remove_token(name: str, kr: KeyringBackend):
    """Remove a token from the keyring storage.

    Parameters
    ----------
    name : str
        The name of the token to remove.
    kr : KeyringBackend
        The keyring backend to remove the token from.
    """
    _remove_token(__encode_name(name), kr)


def _remove_token(hex_name: str, kr: KeyringBackend):
    """Remove a token from the keyring storage.

    Parameters
    ----------
    hex_name : str
        The hex name of the token to remove.
    kr : KeyringBackend
        The keyring backend to remove the token from.
    """
    # Get index
    index = _get_index(kr)

    # Check if token exists
    if hex_name not in index:
        raise ValueError(
            f"Token with name {__decode_name(hex_name)} ({hex_name}) does not exist."
        )

    # Remove token
    kr.delete_password(SNIP_KR_IDENTIFIER, f"{hex_name}:book_id")
    kr.delete_password(SNIP_KR_IDENTIFIER, f"{hex_name}:token")
    kr.delete_password(SNIP_KR_IDENTIFIER, f"{hex_name}:deployment")

    # Update index
    index.remove(hex_name)
    _set_index(index, kr)


def _get_index(kr: KeyringBackend) -> list[str]:
    """Get the index of all tokens from the keyring.

    Parameters
    ----------
    kr : KeyringBackend
        The keyring backend to retrieve the index from.

    Returns
    -------
    list[str]
        A list of all token names in hex.
    """
    index = kr.get_password(SNIP_KR_IDENTIFIER, "index")
    if index is None:
        return []

    names = index.split(",")

    # Filter all empty strings
    return [name for name in names if name != ""]


def _set_index(index: list[str], kr: KeyringBackend):
    """Set the index of all tokens in the keyring.

    Parameters
    ----------
    index : list[str]
        A list of all token names in hex.
    kr : KeyringBackend
        The keyring backend to set the index to.
    """
    kr.set_password(SNIP_KR_IDENTIFIER, "index", ",".join(index))


def __decode_name(name: str) -> str:
    """Decode a hex string as to utf-8 string."""
    return bytes.fromhex(name).decode("utf-8")


def __encode_name(name: str) -> str:
    """Encode a utf-8 string to hex."""
    return name.encode("utf-8").hex()

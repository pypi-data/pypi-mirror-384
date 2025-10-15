"""Token storage module.

This module provides different solutions for tokens.
"""

from typing import Iterable, Optional

from keyring import get_keyring

from ...api import DEFAULT_DEPLOYMENT_URL
from ..token import BookToken, Token
from . import file_store as file_store
from . import keyring_store as keyring_store


def get_all_tokens(
    keyring: Optional[keyring_store.KeyringBackend] = None,
    files: Optional[file_store.Files] = None,
) -> tuple[list[Token], Iterable[file_store.File]]:
    """
    Get all tokens from all sources.

    Parameters
    ----------
    keyring : KeyringBackend, optional
        The keyring to use. Supply to override the default keyring. Defaults to None.
    files : Files, optional
        The files to read the tokens from. Supply to override the default files. Defaults to None.

    Returns
    -------
    tokens, sources : (List[Token], List[str])
        List of all tokens and their sources.
    """
    tokens: list[Token] = []

    if keyring is None:
        keyring = get_keyring()

    # Get tokens from keyring
    tokens += keyring_store.get_all_tokens(keyring)
    sources: list[file_store.File] = ["keyring"] * len(tokens)

    # Get tokens from file
    tokens_from_file, sources_from_file = file_store.get_all_tokens(files)
    tokens += tokens_from_file
    sources += sources_from_file

    return tokens, sources


def get_tokens_by_book_and_deployment(
    book_id: str | int,
    deployment_url: Optional[str],
    keyring: Optional[keyring_store.KeyringBackend] = None,
    files: Optional[file_store.Files] = None,
) -> tuple[list[BookToken], list[file_store.File]]:
    """
    Get all tokens for a specific book_id and deployment_url.

    Parameters
    ----------
    book_id : str
        The book_id to get the tokens for.
    deployment_url : str, optional
        The deployment_url to get the tokens for.
    keyring : KeyringBackend, optional
        The keyring to use. Defaults to None.
    files : Files, optional
        The files to read the tokens from. Defaults to None.

    Returns
    -------
    tokens, sources : (List[Token], List[str])
        List of all tokens and their sources.
    """
    if deployment_url is None:
        deployment_url = DEFAULT_DEPLOYMENT_URL

    tokens, sources = get_all_tokens(keyring=keyring, files=files)

    found_tokens = []
    found_sources = []
    for token, source in zip(tokens, sources):
        if not isinstance(token, BookToken):
            continue
        if token.book_id == int(book_id) and token.deployment_url == deployment_url:
            found_tokens.append(token)
            found_sources.append(source)

    return found_tokens, found_sources


def get_token_by_deployment(
    deployment_url: Optional[str],
    keyring: Optional[keyring_store.KeyringBackend] = None,
    files: Optional[file_store.Files] = None,
) -> tuple[list[Token], list[file_store.File]]:
    """
    Get the token for a specific deployment_url.

    Parameters
    ----------
    deployment_url : str
        The deployment_url to get the token for.
    keyring : KeyringBackend, optional
        The keyring to use. Defaults to None.
    files : Files, optional
        The files to read the tokens from. Defaults to None.

    Returns
    -------
    tokens, sources : (List[Token], List[str])
            List of all tokens and their sources.
    """
    if deployment_url is None:
        deployment_url = DEFAULT_DEPLOYMENT_URL

    tokens, sources = get_all_tokens(keyring=keyring, files=files)

    found_tokens: list[Token] = []
    found_sources = []
    for token, source in zip(tokens, sources):
        if token.deployment_url == deployment_url:
            found_tokens.append(token)
            found_sources.append(source)

    return found_tokens, found_sources


__all__ = [
    "file_store",
    "keyring_store",
    "get_all_tokens",
    "get_tokens_by_book_and_deployment",
]

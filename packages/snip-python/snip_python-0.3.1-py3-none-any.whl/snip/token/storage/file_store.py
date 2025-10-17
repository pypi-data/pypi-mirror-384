"""Functionalities to save and retrieve tokens from ini files.

We implement a simple configparser to read ini files
and parse contained tokens. The typical format of the ini file is:

.. code-block:: ini

    [any_unique_section_name]
    deployment = https://snip.roentgen.physik.uni-goettingen.de/
    book_id = 123
    token = token

Section names can be arbitrary, but should be unique and are parsed as the token name.

We parse the tokens from multiple files sequentially to keep usable error messages and point out the file that is causing the issue. If no files are given we use the default locations:

- local: `[cwd]/.sniprc`
- user: `~/.sniprc`
- global: `/etc/snip/.sniprc`
- environment variable: `SNIPRC`
"""

import os
from collections import defaultdict
from configparser import ConfigParser
from typing import Optional, Sequence, Union

from ...logger import log
from ..token import AccountToken, BookToken, Token

File = Union[str, os.PathLike]
Files = Union[File, Sequence[File]]


def get_all_tokens(
    files: Optional[Files] = None,
) -> tuple[
    list[Token],
    list[File],
]:
    """Get all available tokens from a file or list of files.

    Allows to read tokens from multiple files using the python
    builtin configparser.

    Parameters
    ----------
    files : str | os.PathLike | Sequence[str] | Sequence[os.PathLike] | None
        The file or list of files to read the tokens from. Defaults to all default locations.

    Returns
    -------
    Sequence[Token], Sequence[File]
        The list of tokens and the list of files they were read from.

    """
    files = __parse_files(files)

    # Even tho we could read multiple files at once we do it sequentially
    # to keep usable error messages and point out the file that is causing the issue
    tokens: list[Token] = []
    sources: list[File] = []
    for file in files:
        conf = ConfigParser()
        log.debug(f"Reading tokens from file '{file}' if exists.")
        conf.read(file)

        for section in conf.sections():
            token: Token | None = None

            if not conf.has_option(section, "token"):
                log.warning(
                    f"Section '{section}' in file '{file}' does not contain a token. Skipping."
                )
                continue

            token_type = conf.get(section, "type", fallback="book")
            token_str = conf.get(section, "token")
            deployment_url = conf.get(
                section, "deployment", fallback=Token.deployment_url
            )

            if token_type == "account":
                token = AccountToken.from_unsafe(
                    name=section,
                    token=token_str,
                    deployment_url=deployment_url,
                )
                sources.append(file)
            else:
                if not conf.has_option(section, "book_id"):
                    log.warning(
                        f"Section '{section}' in file '{file}' does not contain a book_id. Skipping."
                    )
                    continue
                book_id = conf.get(section, "book_id")
                token = BookToken.from_unsafe(
                    name=section,
                    token=token_str,
                    book_id=book_id,
                    deployment_url=deployment_url,
                )
                sources.append(file)

            tokens.append(token)

    # Warn on duplicate tokens names
    names = [t.name for t in tokens]
    duplicates = __duplicates_value_index(names)

    if len(duplicates) > 0:
        for name, idxs in duplicates.items():
            files = [sources[i] for i in idxs]
            log.warning(
                f"Duplicate token names! This can lead to unexpected behavior! Found {len(idxs)} duplicates. Duplicate name '{name}' found in files {files}."
            )

    return tokens, sources


def get_token(
    name: str,
    files: Optional[Files] = None,
) -> Optional[Token]:
    """Get a token from a file or list of files given its name.

    Parameters
    ----------
    name : str
        The name of the token.
    files : str | os.PathLike | Sequence[str] | Sequence[os.PathLike]
        The file or list of files to read the token from. Defaults to all default locations.

    """
    tokens, sources = get_all_tokens(files)
    for token, source in zip(tokens, sources):
        if token.name == name:
            log.debug(f"Found token '{name}' in file '{source}'.")
            return token
    return None


def token_exists(
    name: str,
    files: Optional[Files] = None,
) -> bool:
    """Check if a token with a given name exists in a file or list of files.

    Parameters
    ----------
    name : str
        The name of the token.
    files : str | os.PathLike | Sequence[str] | Sequence[os.PathLike]
        The file or list of files to read the token from. Defaults to all default locations.

    """
    return get_token(name, files) is not None


def __parse_files(
    files: Optional[Files] = None,
) -> Sequence[File]:
    """Parse the files and adds the default locations if None is given.

    - local: .sniprc
    - user: ~/.sniprc
    - global: /etc/snip/.sniprc
    - environment variable: SNIPRC

    """
    if files is None:
        files = [
            ".sniprc",
            "~/.sniprc",
            "/etc/snip/.sniprc",
        ]
        env = os.getenv("SNIPRC")
        if env is not None:
            files.append(env)

    if not isinstance(files, Sequence):
        files = [files]

    files = [os.path.expanduser(f) for f in files]

    # Absolute paths
    files = [os.path.abspath(f) for f in files]

    return files


def __duplicates_value_index(lst: list) -> dict:
    """Find duplicates in a list including indexes."""
    D: dict = defaultdict(list)
    for i, item in enumerate(lst):
        D[item].append(i)
    D = {k: v for k, v in D.items() if len(v) > 1}
    return D

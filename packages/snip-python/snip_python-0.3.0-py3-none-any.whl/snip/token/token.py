"""Token module hold implementation for token objects.

We implement a token class to hold all information about an access token.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union

from ..api import DEFAULT_DEPLOYMENT_URL


@dataclass(kw_only=True)
class Token(ABC):
    """Base token class. Not to be used directly."""

    name: str
    token: str
    deployment_url: str = DEFAULT_DEPLOYMENT_URL

    @property
    @abstractmethod
    def type(self) -> str:
        """Return the type of the token."""
        pass


@dataclass(kw_only=True)
class BookToken(Token):
    """Book tokens are only valid for book based access."""

    book_id: int

    @classmethod
    def from_unsafe(
        cls,
        name: str,
        token: str,
        book_id: Union[str, int],
        deployment_url: Optional[str] = None,
    ) -> BookToken:
        """Create a token object from unsafe input. I.e. optional deployment_url."""
        if deployment_url is None:
            deployment_url = DEFAULT_DEPLOYMENT_URL

        if isinstance(book_id, str):
            book_id = int(book_id)

        return cls(
            name=name,
            token=token,
            deployment_url=deployment_url,
            book_id=book_id,
        )

    @property
    def type(self) -> str:
        """Return the type of the token."""
        return "book"

    def __repr__(self):
        """Return a string representation of the token."""
        return f"BookToken(name={self.name}, book_id={self.book_id}, deployment_url={self.deployment_url})"


@dataclass(kw_only=True)
class AccountToken(Token):
    """Account tokens are valid for account based access, i.e. not tied to a specific book."""

    @classmethod
    def from_unsafe(
        cls,
        name: str,
        token: str,
        deployment_url: Optional[str] = None,
    ) -> AccountToken:
        """Create a token object from unsafe input. I.e. optional deployment_url."""
        if deployment_url is None:
            deployment_url = DEFAULT_DEPLOYMENT_URL

        return cls(name=name, token=token, deployment_url=deployment_url)

    @property
    def type(self) -> str:
        """Return the type of the token."""
        return "account"

    def __repr__(self):
        """Return a string representation of the token."""
        return f"AccountToken(name={self.name}, deployment_url={self.deployment_url})"

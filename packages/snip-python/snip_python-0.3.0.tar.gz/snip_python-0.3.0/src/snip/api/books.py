"""Books API wrapper.

This module provides functions to interact with the books endpoints of the Snip API.


As reference see also the [official API documentation](https://snip.roentgen.physik.uni-goettingen.de/apidocs/books).
"""

from datetime import datetime
from typing import Literal, Optional, TypedDict

from snip.token import AccountToken, BookToken

from .request import request


class BookTypedDict(TypedDict):
    """Book entity with all its properties."""

    id: int
    title: str
    comment: Optional[str]
    created: datetime
    finished: Optional[datetime]
    last_updated: datetime
    cover_page_id: Optional[int]
    owner_id: int
    owner_name: str
    owner_type: str
    default_background_type_id: int
    background_type_name: str
    background_type_description: str
    num_pages: int


def get_books(token: AccountToken) -> list[BookTypedDict]:
    """Retrieve all books the user has access to."""
    deployment_url = token.deployment_url
    res: dict = request("GET", f"{deployment_url}/api/books", token=token)  # type: ignore

    if not isinstance(res, dict) and not "books" in res:
        raise ValueError("Invalid response from the API.")

    for book in res["books"]:
        if "created" in book and isinstance(book["created"], str):
            book["created"] = datetime.fromisoformat(book["created"])
        if "finished" in book and isinstance(book["finished"], str):
            book["finished"] = datetime.fromisoformat(book["finished"])
        if "last_updated" in book and isinstance(book["last_updated"], str):
            book["last_updated"] = datetime.fromisoformat(book["last_updated"])

    return [BookTypedDict(**book) for book in res["books"]]  # type: ignore[typeddict-item]


def get_book(token: AccountToken | BookToken, book_id: int) -> BookTypedDict:
    """Retrieve a specific book by its ID."""
    deployment_url = token.deployment_url
    res: BookTypedDict = request(
        "GET", f"{deployment_url}/api/books/{book_id}", token=token
    )  # type: ignore

    if not isinstance(res, dict):
        raise ValueError("Invalid response from the API.")

    if "created" in res and isinstance(res["created"], str):
        res["created"] = datetime.fromisoformat(res["created"])
    if "finished" in res and isinstance(res["finished"], str):
        res["finished"] = datetime.fromisoformat(res["finished"])
    if "last_updated" in res and isinstance(res["last_updated"], str):
        res["last_updated"] = datetime.fromisoformat(res["last_updated"])

    return BookTypedDict(**res)


def create_book(
    token: AccountToken, title: str, comment: Optional[str] = None
) -> BookTypedDict:
    """Create a new book."""
    deployment_url = token.deployment_url
    payload = {"title": title}
    if comment:
        payload["comment"] = comment

    res: BookTypedDict = request(
        "POST",
        f"{deployment_url}/api/books",
        token=token,
        json=payload,  # type: ignore
    )

    if not isinstance(res, dict):
        raise ValueError("Invalid response from the API.")

    if "created" in res and isinstance(res["created"], str):
        res["created"] = datetime.fromisoformat(res["created"])
    if "finished" in res and isinstance(res["finished"], str):
        res["finished"] = datetime.fromisoformat(res["finished"])
    if "last_updated" in res and isinstance(res["last_updated"], str):
        res["last_updated"] = datetime.fromisoformat(res["last_updated"])

    return BookTypedDict(**res)


class BasePermissionTypedDict(TypedDict):
    """Base permission structure with common fields for all permission types."""

    pRead: bool
    pWrite: bool
    pDelete: bool
    pACL: bool
    id: int
    owner: bool


class UserPermissionTypedDict(BasePermissionTypedDict):
    """User-specific permission structure."""

    type: Literal["user"]
    email: str
    self: bool


class GroupPermissionTypedDict(BasePermissionTypedDict):
    """Group-specific permission structure."""

    type: Literal["group"]
    name: str


def get_collaborators(
    token: AccountToken | BookToken, book_id: int
) -> list[UserPermissionTypedDict | GroupPermissionTypedDict]:
    """Retrieve all collaborators for a specific book by its ID."""
    deployment_url = token.deployment_url
    res: dict = request(
        "GET",
        f"{deployment_url}/api/books/{book_id}/collaborators",
        token=token,  # type: ignore
    )

    if not isinstance(res, dict) and not "collaborators" in res:
        raise ValueError("Invalid response from the API.")

    collaborators: list[UserPermissionTypedDict | GroupPermissionTypedDict] = []
    for collaborator in res["collaborators"]:
        if collaborator["type"] == "user":
            collaborators.append(UserPermissionTypedDict(**collaborator))  # type: ignore[typeddict-item]
        elif collaborator["type"] == "group":
            collaborators.append(GroupPermissionTypedDict(**collaborator))  # type: ignore[typeddict-item]
        else:
            raise ValueError(f"Unknown collaborator type: {collaborator['type']}")

    return collaborators


def update_collaborator(
    token: AccountToken | BookToken,
    book_id: int,
    collaborator: UserPermissionTypedDict | GroupPermissionTypedDict,
) -> None:
    """Update the collaborators for a specific book by its ID.

    This may also be used to add new collaborators.
    """
    deployment_url = token.deployment_url
    payload = {
        "id": collaborator["id"],
        "type": collaborator["type"],
        "pRead": collaborator["pRead"],
        "pWrite": collaborator["pWrite"],
        "pDelete": collaborator["pDelete"],
        "pACL": collaborator["pACL"],
    }

    res: dict = request(
        "POST",
        f"{deployment_url}/api/books/{book_id}/collaborators",
        token=token,
        json=payload,  # type: ignore
    )
    if res != True:
        raise ValueError("Failed to update collaborator.", res)


def remove_collaborator(
    token: AccountToken | BookToken,
    book_id: int,
    collaborator_id: int,
    collaborator_type: Literal["user", "group", "invite"] = "user",
) -> None:
    """Remove a collaborator from a specific book by its ID."""
    deployment_url = token.deployment_url

    res = request(
        "DELETE",
        f"{deployment_url}/api/books/{book_id}/collaborators",
        token=token,
        json={"id": collaborator_id, "type": collaborator_type},
    )
    if res != True:
        raise ValueError("Failed to remove collaborator.", res)


def invite_collaborator(
    token: AccountToken | BookToken,
    book_id: int,
    email: str,
) -> dict:
    """Invite a new collaborator to a specific book by its ID."""
    deployment_url = token.deployment_url
    payload = {
        "email": email,
    }

    res: dict = request(
        "POST",
        f"{deployment_url}/api/books/{book_id}/collaborators/invite",
        token=token,
        json=payload,
    )  # type: ignore
    return res

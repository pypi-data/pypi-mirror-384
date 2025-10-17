"""Account API wrapper.

This module provides functions to interact with the account endpoints of the Snip API.

As reference see also the [official API documentation](https://snip.roentgen.physik.uni-goettingen.de/apidocs/account).
"""

from datetime import datetime
from typing import Literal, TypedDict

from snip.token import AccountToken

from .request import request


class GroupMember(TypedDict):
    """Type definition for a group member."""

    user_id: int
    group_id: int
    role: Literal["owner", "moderator", "member"]
    joined_at: datetime
    primary_credential_id: int
    emails: list[str]
    emails_verified: list[bool]
    credential_ids: list[int]
    credential_types: list[str]
    group_name: str
    group_description: str
    self: bool


class Group(TypedDict):
    """Type definition for a group."""

    id: int
    name: str
    description: str
    created: datetime
    last_updated: datetime
    members: list[GroupMember]


def _parse_group(group: dict) -> Group:
    """Parse a group dictionary into a Group TypedDict."""
    if "created" in group and isinstance(group["created"], str):
        group["created"] = datetime.fromisoformat(group["created"])
    if "last_updated" in group and isinstance(group["last_updated"], str):
        group["last_updated"] = datetime.fromisoformat(group["last_updated"])
    for member in group.get("members", []):
        if "joined_at" in member and isinstance(member["joined_at"], str):
            member["joined_at"] = datetime.fromisoformat(member["joined_at"])
    return Group(**group)  # type: ignore[typeddict-item]


def get_groups(token: AccountToken) -> list[Group]:
    """Retrieve all groups the user is a member of."""
    deployment_url = token.deployment_url
    res: list[dict] = request(
        "GET", f"{deployment_url}/api/account/groups", token=token
    )  # type: ignore

    return [_parse_group(group) for group in res]


def create_group(token: AccountToken, name: str) -> Group:
    """Create a new group."""
    deployment_url = token.deployment_url
    res: dict = request(
        "POST",
        f"{deployment_url}/api/account/groups",
        token=token,
        json={"name": name},
    )  # type: ignore

    return _parse_group(res)


def get_group(token: AccountToken, group_id: int) -> Group:
    """Retrieve a specific group by its ID."""
    deployment_url = token.deployment_url
    res: dict = request(
        "GET", f"{deployment_url}/api/account/groups/{group_id}", token=token
    )  # type: ignore

    return _parse_group(res)


def delete_group(token: AccountToken, group_id: int) -> None:
    """Delete a specific group by its name."""
    deployment_url = token.deployment_url
    request("DELETE", f"{deployment_url}/api/account/groups/{group_id}", token=token)  # type: ignore


class MemberRoleUpdate(TypedDict):
    """Type definition for updating member roles."""

    user_id: int
    role: Literal["moderator", "member"]


def modify_group(
    token: AccountToken,
    group_id: int,
    name: str | None = None,
    description: str | None = None,
    update_member_roles: list[MemberRoleUpdate] | None = None,
    remove_members: list[int] | None = None,
    transfer_ownership: int | None = None,
) -> Group:
    """Modify a specific group by its ID.

    Args:
        token: Authentication token
        group_id: ID of the group to modify
        name: New group name (3-255 characters)
        description: New group description
        update_member_roles: List of user_id and role updates
        remove_members: List of user IDs to remove from group
        transfer_ownership: User ID to transfer group ownership to
    """
    deployment_url = token.deployment_url
    payload: dict = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if update_member_roles is not None:
        payload["update_member_roles"] = update_member_roles
    if remove_members is not None:
        payload["remove_members"] = remove_members
    if transfer_ownership is not None:
        payload["transfer_ownership"] = transfer_ownership

    request(
        "PATCH",
        f"{deployment_url}/api/account/groups/{group_id}",
        token=token,
        json=payload,
    )  # type: ignore

    return get_group(token, group_id)


def leave_group(token: AccountToken, group_id: int) -> None:
    """Leave a specific group by its ID."""
    deployment_url = token.deployment_url
    request(
        "POST",
        f"{deployment_url}/api/account/groups/{group_id}/leave",
        token=token,
    )  # type: ignore

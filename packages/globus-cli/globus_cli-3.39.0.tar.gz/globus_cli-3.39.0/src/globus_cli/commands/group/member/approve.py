import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import Field, display

from .._common import group_id_arg

APPROVED_USER_FIELDS = [
    Field("Group ID", "group_id"),
    Field("Approved User ID", "identity_id"),
    Field("Approved User Username", "username"),
]


@command("approve", short_help="Approve a member to join a group.")
@group_id_arg
@click.argument("user", type=IdentityType())
@LoginManager.requires_login("groups")
def member_approve(
    login_manager: LoginManager, *, group_id: uuid.UUID, user: ParsedIdentity
) -> None:
    """
    Approve a pending member to join a group, changing their status from 'invited'
    to 'active'.

    The USER argument may be an identity ID or username (whereas the group must be
    specified with an ID).
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()
    identity_id = auth_client.maybe_lookup_identity_id(user.value)
    if not identity_id:
        raise click.UsageError(f"Couldn't determine identity from user value: {user}")
    actions = {"approve": [{"identity_id": identity_id}]}
    response = groups_client.batch_membership_action(group_id, actions)
    if not response.get("approve", None):
        try:
            raise ValueError(response["errors"]["approve"][0]["detail"])
        except (IndexError, KeyError):
            raise ValueError("Could not approve the user to join the group")
    display(
        response,
        text_mode=display.RECORD,
        fields=APPROVED_USER_FIELDS,
        response_key=lambda data: data["approve"][0],
    )

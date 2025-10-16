from __future__ import annotations

import uuid

import click

from globus_cli.commands.collection._common import (
    filter_fields,
    standard_collection_fields,
)
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import Field, display, formatters

PRIVATE_FIELDS: list[Field] = [
    Field("Root Path", "root_path"),
    Field("Default Directory", "default_directory"),
    Field(
        "Sharing Path Restrictions",
        "sharing_restrict_paths",
        formatter=formatters.SortedJson,
    ),
    Field("Sharing Allowed Users", "sharing_users_allow"),
    Field("Sharing Denied Users", "sharing_users_deny"),
    Field("Sharing Allowed POSIX Groups", "policies.sharing_groups_allow"),
    Field("Sharing Denied POSIX Groups", "policies.sharing_groups_deny"),
]


@command("show", short_help="Show a Collection definition.")
@collection_id_arg
@click.option(
    "--include-private-policies",
    is_flag=True,
    help=(
        "Include private policies. Requires administrator role on the endpoint. "
        "Some policy data may only be visible in `--format JSON` output"
    ),
)
@LoginManager.requires_login("auth", "transfer")
def collection_show(
    login_manager: LoginManager,
    *,
    include_private_policies: bool,
    collection_id: uuid.UUID,
) -> None:
    """Display a Mapped or Guest Collection."""
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    query_params = {}
    fields: list[Field] = standard_collection_fields(login_manager.get_auth_client())

    if include_private_policies:
        query_params["include"] = "private_policies"
        fields += PRIVATE_FIELDS

    res = gcs_client.get_collection(collection_id, query_params=query_params)

    # walk the list of all known fields and reduce the rendering to only look
    # for fields which are actually present
    real_fields = filter_fields(fields, res)

    display(
        res,
        text_mode=display.RECORD,
        fields=real_fields,
    )

from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, display

from ._common import AclPrincipalFormatter


@command(
    "show",
    short_help="Display an access control rule.",
    adoc_examples="""[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ rule_id=1ddeddda-1ae8-11e7-bbe4-22000b9a448b
$ globus endpoint permission show $ep_id $rule_id
----
""",
)
@endpoint_id_arg
@click.argument("rule_id")
@LoginManager.requires_login("auth", "transfer")
def show_command(
    login_manager: LoginManager, *, endpoint_id: uuid.UUID, rule_id: str
) -> None:
    """
    Show detailed information about a single access control rule on an endpoint.
    """
    transfer_client = login_manager.get_transfer_client()
    auth_client = login_manager.get_auth_client()

    rule = transfer_client.get_endpoint_acl_rule(endpoint_id, rule_id)
    display(
        rule,
        text_mode=display.RECORD,
        fields=[
            Field("Rule ID", "id"),
            Field("Permissions", "permissions"),
            Field(
                "Shared With",
                "@",
                formatter=AclPrincipalFormatter(auth_client=auth_client),
            ),
            Field("Path", "path"),
            Field("Expiration Date", "expiration_date"),
        ],
    )

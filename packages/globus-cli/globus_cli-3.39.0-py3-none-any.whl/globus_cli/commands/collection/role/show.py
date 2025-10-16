import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import Field, display
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


@command("show")
@collection_id_arg
@click.argument("ROLE_ID", type=click.UUID)
@LoginManager.requires_login("transfer")
def show_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    role_id: uuid.UUID,
) -> None:
    """Describe a particular role on a Collection."""
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    auth_client = login_manager.get_auth_client()

    res = gcs_client.get_role(role_id)

    display(
        res,
        text_mode=display.RECORD,
        fields=[
            Field("ID", "id"),
            Field("Role", "role"),
            Field(
                "Principal", "principal", formatter=PrincipalURNFormatter(auth_client)
            ),
        ],
    )

from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, flow_id_arg
from globus_cli.termio import Field, display, formatters


@command("delete")
@flow_id_arg
@LoginManager.requires_login("flows")
def delete_command(login_manager: LoginManager, *, flow_id: uuid.UUID) -> None:
    """
    Delete a flow.
    """
    flows_client = login_manager.get_flows_client()

    fields = [
        Field("Deleted", "DELETED", formatter=formatters.Bool),
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field(
            "Owner",
            "flow_owner",
            formatter=formatters.auth.PrincipalURNFormatter(
                login_manager.get_auth_client()
            ),
        ),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
    ]

    res = flows_client.delete_flow(flow_id)
    display(res, fields=fields, text_mode=display.RECORD)

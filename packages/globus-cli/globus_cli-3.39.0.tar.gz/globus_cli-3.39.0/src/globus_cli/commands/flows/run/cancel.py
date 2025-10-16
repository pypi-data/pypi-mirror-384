from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, display, formatters


@command("cancel")
@run_id_arg
@LoginManager.requires_login("flows")
def cancel_command(login_manager: LoginManager, *, run_id: uuid.UUID) -> None:
    """
    Cancel a run.
    """

    flows_client = login_manager.get_flows_client()

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        Field("Run ID", "run_id"),
        Field("Run Label", "label"),
        Field("Started At", "start_time", formatter=formatters.Date),
        Field("Completed At", "completion_time", formatter=formatters.Date),
        Field("Status", "status"),
    ]

    res = flows_client.cancel_run(run_id)
    display(res, fields=fields, text_mode=display.RECORD)

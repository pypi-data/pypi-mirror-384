from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import TIMER_FORMAT_FIELDS


@command("list", short_help="List your timers.")
@LoginManager.requires_login("timers")
def list_command(login_manager: LoginManager) -> None:
    """
    List your timers.
    """
    timer_client = login_manager.get_timer_client()
    response = timer_client.list_jobs(query_params={"order": "submitted_at asc"})
    display(response["jobs"], text_mode=display.RECORD_LIST, fields=TIMER_FORMAT_FIELDS)

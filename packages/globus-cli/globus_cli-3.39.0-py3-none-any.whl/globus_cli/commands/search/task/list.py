import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display

from .._common import index_id_arg

TASK_FIELDS = [
    Field("State", "state"),
    Field("Task ID", "task_id"),
    Field("Creation Date", "creation_date"),
    Field("Completion Date", "completion_date"),
]


@command("list", short_help="List recent tasks for an index.")
@index_id_arg
@LoginManager.requires_login("search")
def list_command(login_manager: LoginManager, *, index_id: uuid.UUID) -> None:
    """List the 1000 most recent tasks for an index."""
    search_client = login_manager.get_search_client()
    display(
        search_client.get_task_list(index_id),
        fields=TASK_FIELDS,
        text_mode=display.TABLE,
        response_key="tasks",
    )

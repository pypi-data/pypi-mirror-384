import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, ParsedJSONData, command
from globus_cli.termio import Field, display

from ._common import index_id_arg


@command("ingest", short_help="Ingest a document into Globus Search.")
@index_id_arg
@click.argument("DOCUMENT", type=JSONStringOrFile())
@LoginManager.requires_login("search")
def ingest_command(
    login_manager: LoginManager, *, index_id: uuid.UUID, document: ParsedJSONData
) -> None:
    """
    Submit a Globus Search 'GIngest' document, to be indexed in a Globus Search index.
    You must have 'owner', 'admin', or 'writer' permissions on that index.

    The document can be provided either as a filename, or via stdin. To use stdin, pass
    a single hyphen for the document name, as in

    \b
        globus search ingest $INDEX_ID -

    The document can be a complete GIngest document, a GMetaList, or a GMetaEntry.
    The datatype is taken from the `@datatype` field, with a default of `GIngest`.

    On success, the response will contain a task ID, which can be used to monitor the
    ingest task.
    """
    search_client = login_manager.get_search_client()
    if not isinstance(document.data, dict):
        raise click.UsageError("Ingest document must be a JSON object")
    doc = document.data

    datatype = doc.get("@datatype", "GIngest")
    if datatype not in ("GIngest", "GMetaList", "GMetaEntry"):
        raise click.UsageError(f"Unsupported datatype: '{datatype}'")

    # if the document is not a GIngest doc, wrap it in one for submission to the API
    if datatype != "GIngest":
        doc = {"@datatype": "GIngest", "ingest_type": datatype, "ingest_data": doc}

    display(
        search_client.ingest(index_id, doc),
        text_mode=display.RECORD,
        fields=[Field("Task ID", "task_id"), Field("Acknowledged", "acknowledged")],
    )

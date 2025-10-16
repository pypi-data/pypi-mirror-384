from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    CommaDelimitedList,
    JSONStringOrFile,
    ParsedJSONData,
    command,
    mutex_option_group,
)
from globus_cli.termio import display, outformat_is_text, print_command_hint
from globus_cli.types import JsonValue

from ._common import index_id_arg


# a callback for output printing
# used to get non-table formatted list output
def _print_subjects(data: dict[str, JsonValue]) -> None:
    for item in t.cast("list[dict[str, JsonValue]]", data["gmeta"]):
        click.echo(item["subject"])


@command("query", short_help="Perform a search.")
@click.option("-q", help="The query-string to use to search the index.")
@click.option(
    "--query-document",
    type=JSONStringOrFile(),
    help=(
        "A complete query document to use to search the index. Use the special `-` "
        "value to read from stdin instead of a file."
    ),
)
@click.option("--limit", type=int, help="Limit the number of results to return")
@click.option(
    "--advanced",
    is_flag=True,
    help="Perform the search using the advanced query syntax",
)
@click.option(
    "--bypass-visible-to",
    is_flag=True,
    help=(
        "Bypass the visible_to restriction on searches. "
        "This option is only available to the admins of an index"
    ),
)
@click.option(
    "--filter-principal-sets",
    type=CommaDelimitedList(),
    help=(
        "A principal-sets filter to apply to the results, allowing filtering by "
        "predefined sets of identities or groups. Supplied as a comma-delimited list."
    ),
)
@index_id_arg
@mutex_option_group("-q", "--query-document")
@LoginManager.requires_login("search")
def query_command(
    login_manager: LoginManager,
    *,
    index_id: uuid.UUID,
    q: str | None,
    query_document: ParsedJSONData | None,
    limit: int | None,
    advanced: bool,
    bypass_visible_to: bool,
    filter_principal_sets: list[str] | None,
) -> None:
    """
    Query a Globus Search index by ID using either a simple query string, or a complex
    query document. At least one of `-q` or `--query-document` must be provided.

    If a query document and command-line options are provided, the options used will
    override any options which were present on the query document.
    """
    if outformat_is_text():
        print_command_hint(
            "Text output for queries only shows the 'subject' which identifies each "
            "document.\n"
            "For more complete output, use `--format JSON`"
        )

    search_client = login_manager.get_search_client()

    if q:
        query_params: dict[str, t.Any] = {}
        if filter_principal_sets:
            query_params["filter_principal_sets"] = ",".join(filter_principal_sets)
        if bypass_visible_to:
            query_params["bypass_visible_to"] = bypass_visible_to

        data = search_client.search(
            index_id,
            q,
            advanced=advanced,
            limit=limit if limit is not None else 10,
            query_params=query_params,
        )
    elif query_document:
        if not isinstance(query_document.data, dict):
            raise click.UsageError("--query-document must be a JSON object")
        doc = query_document.data

        if limit is not None:
            doc["limit"] = limit
        if advanced:
            doc["advanced"] = advanced
        if bypass_visible_to:
            doc["bypass_visible_to"] = bypass_visible_to
        if filter_principal_sets is not None:
            # because list is invariant, it needs a widening cast here
            doc["filter_principal_sets"] = t.cast(
                t.List[JsonValue], filter_principal_sets
            )

        data = search_client.post_search(index_id, doc)
    else:
        raise click.UsageError("Either '-q' or '--query-document' must be provided")

    display(data, text_mode=_print_subjects)

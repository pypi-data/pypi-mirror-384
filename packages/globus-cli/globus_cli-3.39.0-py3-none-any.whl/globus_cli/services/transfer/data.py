from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli.constants import ExplicitNullType
from globus_cli.parsing import TaskPath, mutex_option_group
from globus_cli.types import JsonValue
from globus_cli.utils import shlex_process_stream


def add_batch_to_transfer_data(
    source_base_path: str | None,
    dest_base_path: str | None,
    checksum_algorithm: str | None,
    transfer_data: globus_sdk.TransferData,
    batch: t.TextIO,
) -> None:
    @click.command()
    @click.option("--external-checksum")
    @click.option("--recursive/--no-recursive", "-r", default=None, is_flag=True)
    @click.argument("source_path", type=TaskPath(base_dir=source_base_path))
    @click.argument("dest_path", type=TaskPath(base_dir=dest_base_path))
    @mutex_option_group("--recursive", "--external-checksum")
    def process_batch_line(
        dest_path: TaskPath,
        source_path: TaskPath,
        recursive: bool | None,
        external_checksum: str | None,
    ) -> None:
        """
        Parse a line of batch input and turn it into a transfer submission
        item.
        """
        transfer_data.add_item(
            str(source_path),
            str(dest_path),
            external_checksum=external_checksum,
            checksum_algorithm=checksum_algorithm,
            recursive=recursive,
        )

    shlex_process_stream(process_batch_line, batch, "--batch")


def display_name_or_cname(
    ep_doc: dict[str, JsonValue] | globus_sdk.GlobusHTTPResponse,
) -> str:
    return str(ep_doc["display_name"] or ep_doc["canonical_name"])


def iterable_response_to_dict(iterator: t.Iterable[t.Any]) -> dict[str, list[t.Any]]:
    output_dict: dict[str, list[t.Any]] = {"DATA": []}
    for item in iterator:
        dat = item
        try:
            dat = item.data
        except AttributeError:
            pass
        output_dict["DATA"].append(dat)
    return output_dict


def assemble_generic_doc(datatype: str, **kwargs: t.Any) -> dict[str, t.Any]:
    return ExplicitNullType.nullify_dict({"DATA_TYPE": datatype, **kwargs})

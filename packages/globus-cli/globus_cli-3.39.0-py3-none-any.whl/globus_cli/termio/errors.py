from __future__ import annotations

import json

import click

from .context import outformat_is_json


class PrintableErrorField:
    """
    A glorified tuple with a kwarg in its constructor.
    Coerces name and value fields to unicode for output consistency
    """

    TEXT_PREFIX = "Globus CLI Error:"

    def __init__(
        self, name: str, value: str | int | None, multiline: bool = False
    ) -> None:
        self.multiline = multiline
        self.name = str(name)
        self.raw_value = str(value)
        self.value = self._format_value(self.raw_value)

    @property
    def _text_prefix_len(self) -> int:
        return len(self.TEXT_PREFIX)

    def _format_value(self, val: str) -> str:
        """
        formats a value to be good for textmode printing
        val must be unicode
        """
        name = self.name + ":"
        if not self.multiline or "\n" not in val:
            val = f"{name.ljust(self._text_prefix_len)} {val}"
        else:
            spacer = "\n" + " " * (self._text_prefix_len + 1)
            val = "{}{}{}".format(name, spacer, spacer.join(val.split("\n")))

        return val


def write_error_info(error_name: str, fields: list[PrintableErrorField]) -> None:
    if outformat_is_json():
        # dictify joined tuple lists and dump to json string
        message = click.style(
            json.dumps(
                dict(
                    [("error_name", error_name)]
                    + [(f.name, f.raw_value) for f in fields]
                ),
                indent=2,
                separators=(",", ": "),
                sort_keys=True,
            ),
            fg="yellow",
        )
    else:
        message = "A{} {} Occurred.\n{}".format(
            "n" if error_name[0] in "aeiouAEIOU" else "",
            click.style(error_name, bold=True, fg="red"),
            click.style("\n".join(f.value for f in fields), fg="yellow"),
        )
        message = f"{PrintableErrorField.TEXT_PREFIX} {message}"

    click.echo(message, err=True)

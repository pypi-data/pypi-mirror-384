"""
Internal types for type annotations
"""

from __future__ import annotations

import sys
import typing as t

import click

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if t.TYPE_CHECKING:
    import globus_sdk


AnyCallable: TypeAlias = t.Callable[..., t.Any]
AnyCommand: TypeAlias = t.Union[click.Command, AnyCallable]


ClickContextTree: TypeAlias = t.Tuple[
    click.Context, t.List[click.Context], t.List["ClickContextTree"]
]


DATA_CONTAINER_T: TypeAlias = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
]

JsonValue: TypeAlias = t.Union[
    int, float, str, bool, None, t.List["JsonValue"], t.Dict[str, "JsonValue"]
]


ServiceNameLiteral: TypeAlias = t.Literal[
    "auth", "transfer", "groups", "search", "timers", "flows"
]

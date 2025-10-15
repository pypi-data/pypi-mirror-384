import json
from collections.abc import Iterable
from typing import TypeVar

import betterproto2
from pydantic import BaseModel
from rich.console import ConsoleRenderable, Group
from rich.padding import Padding
from rich.pretty import Pretty
from rich.table import Table

T = TypeVar("T", bound=betterproto2.Message)
M = TypeVar("M", bound=BaseModel)


def table_of_models(cls: type[M], messages: Iterable[M], fields: list[str] = None, title: str = None) -> Table:
    """Centralized logic for printing tables of Pydantic models."""
    cols = fields or cls.model_fields.keys()
    table = Table(*cols, title=title or f"{cls.__name__}s")
    for msg in messages:
        table.add_row(*[_renderable(msg, col) for col in cols])
    return table


def _renderable(msg, col):
    attr = getattr(msg, col, "")
    if isinstance(attr, dict):
        return json.dumps(attr)
    return attr


def table_of_protos(cls: type[T], messages: Iterable[T], fields: list[str] = None, title: str = None) -> Table:
    """Centralized logic for printing tables of proto messages.

    TODO(ngates): add a CLI switch to emit JSON results instead of tables.
    """
    cols = fields or cls()._betterproto2.sorted_field_names
    table = Table(*cols, title=title or f"{cls.__name__}s")
    for msg in messages:
        table.add_row(*[getattr(msg, col, "") for col in cols])
    return table


def proto(message: T, title: str = None, fields: list[str] = None) -> ConsoleRenderable:
    """Centralized logic for printing a single proto message."""
    value = Pretty({k: v for k, v in message.to_dict().items() if not fields or k in fields})
    if title:
        return Group(
            f"[bold]{title}[/bold]",
            Padding.indent(value, level=2),
        )
    else:
        return value
